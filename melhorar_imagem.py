"""
melhorar_imagem.py - Módulo para pré-processamento e melhoria da imagem

Este módulo é responsável pelo tratamento da imagem antes da segmentação. 
Conceitos da disciplina: Melhoria no domínio espacial.

Funcionalidades:
    - CLAHE (Contrast Limited Adaptive Histogram Equalization)
    - Filtro Gaussiano para redução de ruído
    - Preparação da imagem para detecção de estrelas

Autor: Eduardo Fonseca Morato
Contato: morato@alunos.utfpr.edu.br
Disciplina: ELTD2 - Processamento de Imagens UTFPR
"""

import numpy as np
from skimage import exposure, filters


def pre_processar(imagem, config=None):
    """
    Aplica uma sequência de operações para melhorar a imagem,
    destacando as estrelas e reduzindo ruído.
    
    Fluxo:
        1. Normaliza a imagem para [0, 1] (caso rode esse script direto)
        2. Aplica CLAHE para uniformizar iluminação
        3. Aplica filtro Gaussiano para suavizar ruído
    
    Args:
        imagem (numpy.ndarray): Imagem de entrada (pode ser qualquer escala)
        config (dict, optional): Parâmetros de configuração.
                                 Se None, usa valores padrão.
    
    Returns:
        numpy.ndarray: Imagem processada (float64, range [0, 1])
    """
    
    # Configurações padrão
    if config is None:
        config = {
            'clahe_clip_limit': 0.02,
            'clahe_tile_size': 8,
            'gaussian_sigma': 1.5
        }
    
    # Passo 1: Garantir que a imagem está em float64
    if imagem.dtype != np.float64:
        imagem = imagem.astype(np.float64)

    # Passo 2: Normalizar para [0, 1] se já não estiver
    if imagem.min() < 0 or imagem.max() > 1:
        imagem = normalizar_imagem(imagem)
    
    # Passo 3: Aplicar CLAHE
    imagem = aplicar_clahe(imagem, 
                           clip_limit=config['clahe_clip_limit'],
                           tile_size=config['clahe_tile_size'])
    
    # Passo 4: Aplicar filtro Gaussiano
    imagem = aplicar_filtro_gaussiano(imagem,
                                      sigma=config['gaussian_sigma'])
    
    return imagem


def normalizar_imagem(imagem):
    """
    Normaliza a imagem linearmente para o intervalo [0, 1].
    
    Args:
        imagem (numpy.ndarray): Imagem de entrada
    
    Returns:
        numpy.ndarray: Imagem normalizada
    """
    r_min = np.min(imagem)
    r_max = np.max(imagem)
    
    if r_max == r_min:
        return np.zeros_like(imagem)
    
    return (imagem - r_min) / (r_max - r_min)

def aplicar_clahe(imagem, clip_limit=0.02, tile_size=8):
    """
    Aplica CLAHE (Contrast Limited Adaptive Histogram Equalization).
    
    O CLAHE é uma evolução da equalização de histograma adaptativa.
    Ele opera em pequenas regiões (tiles) da imagem e limita o contraste
    para evitar amplificação excessiva de ruído em áreas homogêneas.
    
    Conceito da disciplina: Melhoria no domínio espacial (Aula 08)
    
    Args:
        imagem (numpy.ndarray): Imagem de entrada (range [0, 1])
        clip_limit (float): Limite de contraste (0.01 é padrão do MATLAB)
        tile_size (int): Tamanho dos tiles (8x8 pixels)
    
    Returns:
        numpy.ndarray: Imagem com contraste melhorado
    """
    # CLAHE do scikit-image
    # O parâmetro clip_limit é normalizado internamente
    imagem_clahe = exposure.equalize_adapthist(
        imagem,
        clip_limit=clip_limit,
        kernel_size=(tile_size, tile_size)
    )
    
    return imagem_clahe


def aplicar_filtro_gaussiano(imagem, sigma=1.5):
    """
    Aplica filtro Gaussiano para suavização e redução de ruído.
    
    O filtro Gaussiano é um filtro passa-baixas que atenua
    componentes de alta frequência (ruído, detalhes finos).
    
    Conceito da disciplina: Filtros espaciais lineares (Aula 04)
    
    Para imagens astronômicas, o filtro Gaussiano ajuda a:
    - Reduzir ruído de leitura do sensor
    - Suavizar variações indesejadas
    - Tornar a detecção de estrelas mais robusta
    
    Args:
        imagem (numpy.ndarray): Imagem de entrada
        sigma (float): Desvio padrão do kernel Gaussiano
    
    Returns:
        numpy.ndarray: Imagem suavizada
    """
    # Filtro Gaussiano do scikit-image
    # preserve_range=True mantém a imagem no mesmo range [0, 1]
    imagem_suave = filters.gaussian(
        imagem,
        sigma=sigma,
        preserve_range=True
    )
    
    return imagem_suave


def exibir_info_processamento(imagem_original, imagem_processada):
    """
    Exibe informações sobre o pré-processamento (para debug).
    
    Args:
        imagem_original (numpy.ndarray): Imagem original
        imagem_processada (numpy.ndarray): Imagem após pré-processamento
    """
    print("  Pré-processamento:")
    print(f"    Original: min={np.min(imagem_original):.3f}, "
          f"max={np.max(imagem_original):.3f}, "
          f"média={np.mean(imagem_original):.3f}")
    print(f"    Processada: min={np.min(imagem_processada):.3f}, "
          f"max={np.max(imagem_processada):.3f}, "
          f"média={np.mean(imagem_processada):.3f}")


# ============================================================================
# TESTE (executado apenas se rodar este arquivo diretamente)
# ============================================================================

if __name__ == "__main__":
    import sys
    from ler_fits import carregar_imagem
    
    
    if len(sys.argv) > 1:
        caminho_teste = sys.argv[1]
        print(f"Testando pré-processamento: {caminho_teste}")
        print("-" * 50)
        
        try:
            # Carrega a imagem
            img, header = carregar_imagem(caminho_teste)
            print(f"Imagem original: {img.shape[0]} × {img.shape[1]} pixels")
            print(f"  Min: {np.min(img):.3f}, Max: {np.max(img):.3f}")
            
            # Aplica pré-processamento
            img_proc = pre_processar(img)

            print(f"\nImagem processada: {img_proc.shape[0]} × {img_proc.shape[1]} pixels")  # type: ignore
            print(f"  Min: {np.min(img_proc):.3f}, Max: {np.max(img_proc):.3f}")
            print(f"  Média: {np.mean(img_proc):.3f}")
            print(f"  Desvio padrão: {np.std(img_proc):.3f}")
            
            print("\n✅ Pré-processamento concluído!")
            
            # Opcional: mostrar a imagem (se tiver matplotlib)
            try:
                import matplotlib.pyplot as plt
                fig, axes = plt.subplots(1, 2, figsize=(12, 5))
                axes[0].imshow(img, cmap='gray')
                axes[0].set_title('Original')
                axes[1].imshow(img_proc, cmap='gray')
                axes[1].set_title('Após Pré-processamento')
                plt.show()
            except ImportError:
                print("(Matplotlib não disponível para visualização)")
            
        except Exception as e:
            print(f"❌ Erro: {e}")
    else:
        print("Uso: python melhorar_imagem.py caminho/para/imagem.fits")