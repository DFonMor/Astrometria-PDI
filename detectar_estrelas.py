"""
detectar_estrelas.py - Módulo para segmentação e detecção de estrelas

Este módulo é responsável pela: Segmentação e detecção
de estrelas. Conceitos da disciplina: Segmentação, Morfologia Matemática, 
Rotulação de regiões (Aula 07).

Funcionalidades:
    - Limiarização global (Otsu) para separar estrelas do fundo
    - Operações morfológicas para limpeza (abertura/fechamento)
    - Rotulação para identificar objetos individuais
    - Extração de centroides, fluxos e áreas

Autor: Eduardo Fonseca Morato
Contato: morato@alunos.utfpr.edu.br
Disciplina: ELTD2 - Processamento de Imagens UTFPR
"""

import numpy as np
from scipy import ndimage
from skimage import measure, morphology, filters
import warnings


def detectar_estrelas(imagem, config=None):
    """
    Detecta estrelas em uma imagem pré-processada.
    
    Pipeline:
        1. Limiarização (Otsu) para criar máscara binária
        2. Abertura para remover pequenos ruídos
        3. Fechamento para conectar estrelas fragmentadas
        4. Rotulação para identificar objetos individuais
        5. Extração de propriedades (centroide, área, fluxo)
        6. Filtragem por tamanho (remove estrelas muito grandes/pequenas)
    
    Args:
        imagem (numpy.ndarray): Imagem pré-processada (range [0, 1])
        config (dict, optional): Parâmetros de configuração.
    
    Returns:
        list: Lista de dicionários, cada um contendo:
              - x (float): Coordenada x do centroide
              - y (float): Coordenada y do centroide
              - fluxo (float): Intensidade acumulada
              - area (int): Área em pixels
              - label (int): Rótulo do objeto
              - bbox (tuple): Bounding box (min_row, min_col, max_row, max_col)
    """
    
    # Configurações padrão
    if config is None:
        config = {
            'num_stars': 40,
            'otsu_sensitivity': 1.0,
            'morph_open_size': 3,
            'morph_close_size': 3,
            'min_star_area': 3,
            'max_star_area': 50,
            'min_flux': 0.01
        }
    
    # Passo 1: Limiarização (Otsu)
    mascara = aplicar_limiar_otsu(imagem, 
                                  sensitivity=config['otsu_sensitivity'])
    
    # Passo 2: Limpeza morfológica
    mascara = limpar_mascara(mascara,
                            open_size=config['morph_open_size'],
                            close_size=config['morph_close_size'])
    
    # Passo 3: Rotulação
    objetos = rotular_objetos(mascara)
    
    # Passo 4: Extrair propriedades e filtrar
    estrelas = extrair_propriedades(imagem, objetos,
                                   min_area=config['min_star_area'],
                                   max_area=config['max_star_area'],
                                   min_flux=config['min_flux'])
    
    # Seleciona as N mais brilhantes (AQUI!)
    estrelas = selecionar_estrelas_brilhantes(estrelas, config['num_stars'])

    return estrelas


def aplicar_limiar_otsu(imagem, sensitivity=1.0):
    """
    Aplica limiarização de Otsu para separar estrelas do fundo.
    
    Conceito da disciplina: Limiarização global - método de Otsu
    
    Args:
        imagem (numpy.ndarray): Imagem de entrada (range [0, 1])
        sensitivity (float): Fator multiplicador do limiar
                            (>1: menos estrelas, <1: mais estrelas)
    
    Returns:
        numpy.ndarray: Máscara binária (True = estrela, False = fundo)
    """
    # Otsu retorna o limiar no range [0, 1]
    limiar = filters.threshold_otsu(imagem)
    
    # Aplica fator de sensibilidade
    limiar_ajustado = limiar * sensitivity
    
    # Cria máscara binária: objetos são pixels acima do limiar
    mascara = imagem > limiar_ajustado
    
    return mascara


def limpar_mascara(mascara, open_size=3, close_size=3):
    """
    Aplica operações morfológicas para limpeza da máscara.
    
    Operações:
        1. Abertura (erosão + dilatação): remove pequenos ruídos
        2. Fechamento (dilatação + erosão): conecta objetos fragmentados
    
    Conceito da disciplina: Morfologia matemática
    
    Args:
        mascara (numpy.ndarray): Máscara binária
        open_size (int): Tamanho do elemento estruturante para abertura
        close_size (int): Tamanho do elemento estruturante para fechamento
    
    Returns:
        numpy.ndarray: Máscara limpa
    """
    # Elemento estruturante para abertura (remove ruído)
    se_open = morphology.disk(open_size)
    mascara = morphology.opening(mascara, se_open)
    
    # Elemento estruturante para fechamento (conecta estrelas fragmentadas)
    se_close = morphology.disk(close_size)
    mascara = morphology.closing(mascara, se_close)
    
    return mascara


def rotular_objetos(mascara):
    """
    Rotula objetos individuais em uma máscara binária.
    
    A rotulação atribui um número (label) para cada objeto distinto,
    permitindo medir propriedades de cada um separadamente.
    
    Conceito da disciplina: Rotulação de regiões binárias
    
    Args:
        mascara (numpy.ndarray): Máscara binária
    
    Returns:
        tuple: (labeled_image, num_objects)
            - labeled_image: Imagem com labels
            - num_objects: Número de objetos encontrados
    """
    # Rotulação com conectividade 8 (considera diagonais)
    labeled_image, num_objects = ndimage.label(mascara, structure=np.ones((3, 3))) #type: ignore
    
    return labeled_image, num_objects


def extrair_propriedades(imagem, objetos, min_area=3, max_area=50, min_flux=0.01):
    """
    Extrai propriedades de cada objeto rotulado.
    
    Propriedades extraídas:
        - Centroide (x, y) - posição da estrela
        - Área (pixels) - tamanho da estrela
        - Fluxo (soma dos pixels) - brilho da estrela
        - Bounding box - retângulo que envolve a estrela
    
    Conceito da disciplina: Extração de atributos
    
    Args:
        imagem (numpy.ndarray): Imagem original (para calcular fluxo)
        objetos (tuple): (labeled_image, num_objects)
        min_area (int): Área mínima (pixels) para considerar estrela
        max_area (int): Área máxima (pixels) para considerar estrela
        min_flux (float): Fluxo mínimo (intensidade acumulada)
    
    Returns:
        list: Lista de dicionários com as propriedades
    """
    labeled_image, _ = objetos
    
    estrelas = []
    
    # Propriedades padrão: 'label', 'area', 'centroid', 'bbox'
    props = measure.regionprops(labeled_image, intensity_image=imagem)
    
    for prop in props:
        # Filtra por área
        area = prop.area
        if area < min_area or area > max_area:
            continue
        
        # Filtra por fluxo (intensidade acumulada)
        # Usa a média de intensidade * área
        fluxo = prop.intensity_mean * area
        if fluxo < min_flux:
            continue
        
        # Extrai centroide (em coordenadas (x, y))
        # regionprops retorna (row, col) -> (y, x)
        y, x = prop.centroid
        
        # Extrai bounding box
        min_row, min_col, max_row, max_col = prop.bbox
        
        estrela = {
            'x': float(x),
            'y': float(y),
            'fluxo': float(fluxo),
            'area': int(area),
            'label': int(prop.label),
            'bbox': (int(min_row), int(min_col), int(max_row), int(max_col))
        }
        
        estrelas.append(estrela)
    
    # Ordena por fluxo (mais brilhante primeiro)
    estrelas.sort(key=lambda s: s['fluxo'], reverse=True)
    
    return estrelas


def selecionar_estrelas_brilhantes(estrelas, num_estrelas=40):
    """
    Seleciona as N estrelas mais brilhantes.
    
    Args:
        estrelas (list): Lista de estrelas detectadas
        num_estrelas (int): Número de estrelas a selecionar
    
    Returns:
        list: Lista com as N estrelas mais brilhantes
    """
    if len(estrelas) <= num_estrelas:
        return estrelas
    return estrelas[:num_estrelas]


def exibir_info_deteccao(estrelas):
    """
    Exibe informações sobre a detecção de estrelas (para debug).
    
    Args:
        estrelas (list): Lista de estrelas detectadas
    """
    print(f"  Estrelas detectadas: {len(estrelas)}")
    
    if estrelas:
        # Estatísticas
        fluxos = [s['fluxo'] for s in estrelas]
        areas = [s['area'] for s in estrelas]
        
        print(f"    Fluxo: min={min(fluxos):.3f}, max={max(fluxos):.3f}, "
              f"média={np.mean(fluxos):.3f}")
        print(f"    Área: min={min(areas)}, max={max(areas)}, "
              f"média={np.mean(areas):.1f}")
        
        # Estrela mais brilhante
        s = estrelas[0]
        print(f"    Mais brilhante: fluxo={s['fluxo']:.3f}, "
              f"posição=({s['x']:.1f}, {s['y']:.1f}), área={s['area']}px")


# ============================================================================
# TESTE (executado apenas se rodar este arquivo diretamente)
# ============================================================================

if __name__ == "__main__":
    import sys
    import matplotlib.pyplot as plt
    from ler_fits import carregar_imagem
    from melhorar_imagem import pre_processar
    
    if len(sys.argv) > 1:
        caminho_teste = sys.argv[1]
        print(f"Testando detecção de estrelas: {caminho_teste}")
        print("-" * 50)
        
        try:
            # Carrega e pré-processa
            img_raw, header = carregar_imagem(caminho_teste)
            img_proc = pre_processar(img_raw)
            
            config_deteccao = {
                'num_stars': 40,
                'otsu_sensitivity': 1.0,
                'morph_open_size': 3,
                'morph_close_size': 3,
                'min_star_area': 3,
                'max_star_area': 50,
                'min_flux': 0.01,
            }

            # Detecta estrelas
            estrelas = detectar_estrelas(img_proc, config_deteccao) 
            exibir_info_deteccao(estrelas)
            
            if estrelas:
                # Mostra resultado visual
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
                
                # Imagem original
                ax1.imshow(img_proc, cmap='gray')
                ax1.set_title('Imagem Pré-processada')
                
                # Imagem com estrelas marcadas
                ax2.imshow(img_proc, cmap='gray')
                for s in estrelas[:20]:  # Mostra as 20 mais brilhantes
                    ax2.plot(s['x'], s['y'], 'r+', markersize=8, markeredgewidth=1)
                    ax2.text(s['x']+5, s['y']-5, f"{s['fluxo']:.1f}", 
                            color='red', fontsize=8)
                ax2.set_title(f'{len(estrelas)} estrelas detectadas')
                
                plt.tight_layout()
                plt.show()
            else:
                print("⚠️ Nenhuma estrela detectada!")
                
        except Exception as e:
            print(f"❌ Erro: {e}")
    else:
        print("Uso: python detectar_estrelas.py caminho/para/imagem.fits")