"""
melhorar_imagem.py - Módulo para melhorar a visualização da imagem

Este módulo é responsável por preparar a imagem para visualização,
sem alterar os dados originais usados para detecção.

Conceitos da disciplina: Melhoria no domínio espacial, transformações
ponto-a-ponto (Aula 03).

Funcionalidades:
    - Normalização por percentis (como o Astrometry.net)
    - Visualização otimizada para exibição

Autor: Eduardo Fonseca Morato
Contato: morato@alunos.utfpr.edu.br
Disciplina: ELTD2 - Processamento de Imagens UTFPR
"""

import numpy as np


def pre_processar(imagem, config=None):
    """
    Prepara a imagem para visualização usando normalização por percentis.
    
    Esta função é usada APENAS para visualização. A detecção de estrelas
    deve ser feita na imagem original (sem normalização).
    
    Fluxo:
        1. Garante que a imagem está em float64
        2. Aplica normalização por percentis (10%-95%)
        3. Retorna imagem no range [0, 1] para exibição
    
    Args:
        imagem (numpy.ndarray): Imagem de entrada (pode ser qualquer escala)
        config (dict, optional): Parâmetros de configuração.
    
    Returns:
        numpy.ndarray: Imagem visualizável (float64, range [0, 1])
    """
    
    # Configurações padrão
    if config is None:
        config = {
            'low_percent': 10,      # Percentil inferior (10% = padrão do teste)
            'high_percent': 95,     # Percentil superior (95% = padrão do teste)
        }
    
    # Passo 1: Garantir que a imagem está em float64
    if imagem.dtype != np.float64:
        imagem = imagem.astype(np.float64)
    
    # Passo 2: Normalização por percentis
    imagem = normalizar_por_percentil(
        imagem,
        low_percent=config['low_percent'],
        high_percent=config['high_percent']
    )
    
    return imagem


def normalizar_por_percentil(imagem, low_percent=10, high_percent=95):
    """
    Normaliza a imagem usando percentis (como o Astrometry.net).
    
    Esta é a abordagem utilizada pelo Astrometry.net (an-fitstopnm).
    Os valores abaixo do percentil inferior tornam-se 0 (preto),
    os valores acima do percentil superior tornam-se 1 (branco).
    
    Args:
        imagem (numpy.ndarray): Imagem de entrada
        low_percent (int): Percentil inferior (padrão: 10)
        high_percent (int): Percentil superior (padrão: 95)
    
    Returns:
        numpy.ndarray: Imagem normalizada no intervalo [0, 1]
    """
    # Calcula os percentis
    low = np.percentile(imagem, low_percent)
    high = np.percentile(imagem, high_percent)
    
    # Evita divisão por zero
    if high == low:
        return np.zeros_like(imagem)
    
    # Recorta valores fora do intervalo
    imagem = np.clip(imagem, low, high)
    
    # Normaliza para [0, 1]
    return (imagem - low) / (high - low)


def exibir_info_processamento(imagem_original, imagem_processada):
    """
    Exibe informações sobre o pré-processamento (para debug).
    
    Args:
        imagem_original (numpy.ndarray): Imagem original
        imagem_processada (numpy.ndarray): Imagem após pré-processamento
    """
    print("  Pré-processamento (visualização):")
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
    import matplotlib.pyplot as plt
    from ler_fits import carregar_imagem
    
    if len(sys.argv) > 1:
        caminho_teste = sys.argv[1]
        print(f"Testando visualização: {caminho_teste}")
        print("-" * 50)
        
        try:
            # Carrega a imagem (crua, sem modificações)
            img, header = carregar_imagem(caminho_teste)
            print(f"Imagem original: {img.shape[0]} × {img.shape[1]} pixels")
            
            # Apenas para visualização
            img_vis = pre_processar(img)
            
            print(f"\nImagem visualizável: {img_vis.shape[0]} × {img_vis.shape[1]} pixels")
            print(f"  Min: {np.min(img_vis):.3f}, Max: {np.max(img_vis):.3f}")
            print(f"  Média: {np.mean(img_vis):.3f}")
            
            # Mostra a imagem limpa (sem marcações)
            fig, ax = plt.subplots(1, 1, figsize=(12, 10))
            
            ax.imshow(img_vis, cmap='gray', origin='lower')
            ax.set_xlim(0, img_vis.shape[1])
            ax.set_ylim(0, img_vis.shape[0])
            
            ax.set_title(f'Visualização com percentis 10%-95%')
            ax.axis('off')
            
            plt.tight_layout()
            plt.show()
            
            print("\n✅ Visualização concluída!")
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("Uso: python melhorar_imagem.py caminho/para/imagem.fits")