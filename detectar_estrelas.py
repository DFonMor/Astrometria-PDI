"""
detectar_estrelas.py - Módulo para segmentação e detecção de estrelas

Este módulo é responsável pela detecção de estrelas usando a biblioteca photutils.
Conceitos da disciplina: Segmentação, Morfologia Matemática, Extração de atributos.

Funcionalidades:
    - Estimativa de fundo da imagem (Background2D)
    - Detecção de estrelas com DAOStarFinder
    - Extração de propriedades (centroide, fluxo, área)

Autor: Eduardo Fonseca Morato
Contato: morato@alunos.utfpr.edu.br
Disciplina: ELTD2 - Processamento de Imagens UTFPR
"""

import numpy as np
from photutils.detection import DAOStarFinder
from photutils.background import Background2D, MedianBackground
from astropy.stats import mad_std


def detectar_estrelas(imagem, config=None):
    """
    Detecta estrelas usando a biblioteca photutils (DAOStarFinder).
    
    Args:
        imagem (numpy.ndarray): Imagem de entrada (pode ser normalizada ou não)
        config (dict, optional): Parâmetros de configuração.
    
    Returns:
        list: Lista de dicionários, cada um contendo:
              - x (float): Coordenada x do centroide
              - y (float): Coordenada y do centroide
              - fluxo (float): Fluxo da estrela
              - area (int): Número de pixels
              - sharpness (float): Nitidez da estrela
              - roundness (float): Circularidade da estrela
    """
    
    # Configurações padrão (baseadas nos testes)
    if config is None:
        config = {
            'fwhm': 3.0,
            'threshold': 3.0,
            'n_brightest': 50,
            'sharpness_range': (-1.0, 1.0),
            'roundness_range': (-1.0, 1.0),
            'box_size': 50,
            'filter_size': 3,
        }
    
    # ============================================================
    # PASSO 1: Estimar o fundo da imagem
    # ============================================================
    try:
        bkg = Background2D(
            imagem,
            box_size=config['box_size'],
            filter_size=config['filter_size'],
            bkg_estimator=MedianBackground()
        )
        fundo = bkg.background
        rms = bkg.background_rms
    except Exception as e:
        # Fallback: usar estatísticas globais
        fundo = np.median(imagem)
        rms = mad_std(imagem)
    
    # ============================================================
    # PASSO 2: Subtrair o fundo
    # ============================================================
    if isinstance(fundo, np.ndarray):
        imagem_sub = imagem - fundo
        rms_value = np.median(rms) if isinstance(rms, np.ndarray) else rms
    else:
        imagem_sub = imagem - fundo
        rms_value = rms
    
    imagem_sub = np.maximum(imagem_sub, 0)
    
    # ============================================================
    # PASSO 3: Detecção de estrelas com DAOStarFinder
    # ============================================================
    daofind = DAOStarFinder(
        fwhm=config['fwhm'],
        threshold=config['threshold'] * rms_value,
        n_brightest=config['n_brightest'],
        sharpness_range=config['sharpness_range'],
        roundness_range=config['roundness_range'],
    )
    
    sources = daofind(imagem_sub)
    
    if sources is None or len(sources) == 0:
        return []
    
    # ============================================================
    # PASSO 4: Extrair propriedades
    # ============================================================
    estrelas = []
    colunas = sources.colnames
    
    for source in sources:
        # Extrai coordenadas
        if 'x_centroid' in colunas:
            x = float(source['x_centroid'])
            y = float(source['y_centroid'])
        elif 'xcentroid' in colunas:
            x = float(source['xcentroid'])
            y = float(source['ycentroid'])
        elif 'x' in colunas and 'y' in colunas:
            x = float(source['x'])
            y = float(source['y'])
        else:
            col_x = None
            col_y = None
            for col in colunas:
                if 'x' in col.lower() and col_x is None:
                    col_x = col
                if 'y' in col.lower() and col_y is None:
                    col_y = col
            if col_x is not None and col_y is not None:
                x = float(source[col_x])
                y = float(source[col_y])
            else:
                continue
        
        # Extrai fluxo
        fluxo = float(source['flux']) if 'flux' in colunas else 0
        
        # Extrai área
        area = int(source['n_pixels']) if 'n_pixels' in colunas else 0
        
        # Extrai qualidade
        sharpness = float(source['sharpness']) if 'sharpness' in colunas else 0
        roundness = float(source['roundness1']) if 'roundness1' in colunas else 0
        
        estrela = {
            'x': x,
            'y': y,
            'fluxo': fluxo,
            'area': area,
            'sharpness': sharpness,
            'roundness': roundness,
        }
        estrelas.append(estrela)
    
    # Ordena por fluxo (mais brilhante primeiro)
    estrelas.sort(key=lambda s: s['fluxo'], reverse=True)
    
    return estrelas


def salvar_estrelas_xy(estrelas, arquivo_saida):
    """
    Salva a lista de estrelas no formato .xy do astrometry.net (TEXTO SIMPLES).
    
    Formato:
        x y fluxo
        cada linha: coordenada_x coordenada_y fluxo
    
    Args:
        estrelas (list): Lista de estrelas detectadas
        arquivo_saida (str): Caminho para o arquivo .xy
    """
    with open(arquivo_saida, 'w') as f:
        f.write("# Estrelas detectadas\n")
        f.write("# x y fluxo\n")
        for s in estrelas:
            f.write(f"{s['x']:.3f} {s['y']:.3f} {s['fluxo']:.3f}\n")

def exibir_info_deteccao(estrelas):
    """
    Exibe informações sobre a detecção de estrelas (para debug).
    """
    print(f"  Estrelas detectadas: {len(estrelas)}")
    
    if estrelas:
        fluxos = [s['fluxo'] for s in estrelas[:10]]
        areas = [s['area'] for s in estrelas[:10]]
        
        print(f"    Top 10 fluxos: {', '.join([f'{f:.1f}' for f in fluxos])}")
        print(f"    Top 10 áreas: {', '.join([str(a) for a in areas])}")
        
        s = estrelas[0]
        print(f"    Mais brilhante: fluxo={s['fluxo']:.1f}, "
              f"posição=({s['x']:.1f}, {s['y']:.1f}), área={s['area']}px")


# ============================================================================
# TESTE (executado apenas se rodar este arquivo diretamente)
# ============================================================================

if __name__ == "__main__":
    import sys
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle
    from ler_fits import carregar_imagem
    from melhorar_imagem import pre_processar
    
    if len(sys.argv) > 1:
        caminho_teste = sys.argv[1]
        print(f"Testando detecção de estrelas com photutils: {caminho_teste}")
        print("-" * 50)
        
        try:
            # Carrega imagem (sem normalização para detecção)
            img_raw, header = carregar_imagem(caminho_teste)
            
            # Detecta estrelas
            estrelas = detectar_estrelas(img_raw)
            exibir_info_deteccao(estrelas)
            
            if estrelas:
                # ============================================================
                # SALVA ESTRELAS NO FORMATO .XY (para o solve-field)
                # ============================================================
                salvar_estrelas_xy(estrelas, "teste.xy")
                print(f"💾 Estrelas salvas em: teste.xy")
                
                # ============================================================
                # VISUALIZAÇÃO
                # ============================================================
                img_vis = pre_processar(img_raw)
                
                fig, ax = plt.subplots(1, 1, figsize=(12, 10))
                
                ax.imshow(img_vis, cmap='gray', origin='lower')
                ax.set_xlim(0, img_vis.shape[1])
                ax.set_ylim(0, img_vis.shape[0])
                
                for s in estrelas[:30]:
                    ax.plot(s['x'], s['y'], 'r+', markersize=10, markeredgewidth=2)
                    if s['area'] > 0:
                        radius = np.sqrt(s['area'] / np.pi) * 1.5
                        circle = Circle((s['x'], s['y']), radius, color='yellow', fill=False, linewidth=1.5)
                        ax.add_patch(circle)
                
                if estrelas:
                    s_mais = estrelas[0]
                    ax.plot(s_mais['x'], s_mais['y'], 'b+', markersize=12, markeredgewidth=2)
                    ax.text(s_mais['x']+15, s_mais['y']-15, f'{s_mais["fluxo"]:.1f}', 
                           color='cyan', fontsize=11, weight='bold',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.5))
                
                ax.set_title(f'{len(estrelas)} estrelas detectadas com photutils')
                ax.axis('off')
                
                plt.tight_layout()
                plt.show()
                
                print("\n✅ Visualização concluída!")
            else:
                print("⚠️ Nenhuma estrela detectada!")
                
        except Exception as e:
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("Uso: python detectar_estrelas.py caminho/para/imagem.fits")
