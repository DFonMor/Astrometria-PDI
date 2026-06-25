"""
melhorar_imagem.py - Módulo para melhorar a visualização da imagem

Este módulo oferece diferentes métodos para realçar o contraste e a
visualização de imagens astronômicas, mantendo a imagem original intacta
para fins de detecção.

Conceitos da disciplina: Melhoria no domínio espacial, transformações
ponto-a-ponto (Aula 03), equalização de histograma (Aula 08).

Funcionalidades:
    - Normalização por percentis (padrão Astrometry.net)
    - Equalização de histograma (global)
    - CLAHE (Contrast Limited Adaptive Histogram Equalization)
    - Stretching com saturação de percentis personalizados

Autor: Eduardo Fonseca Morato
Contato: morato@alunos.utfpr.edu.br
Disciplina: ELTD2 - Processamento de Imagens UTFPR
"""

import numpy as np
from skimage import exposure, filters


def pre_processar(imagem, config=None):
    """
    Prepara a imagem para visualização usando normalização por percentis.
    """
    # Configurações padrão (usadas se não for passado um config)
    if config is None:
        config = {
            'low_percent': 5,
            'high_percent': 95,
        }
    
    if imagem.dtype != np.float64:
        imagem = imagem.astype(np.float64)
    
    imagem = normalizar_por_percentil(
        imagem,
        low_percent=config['low_percent'],
        high_percent=config['high_percent']
    )
    
    # CLAHE opcional (se configurado)
    if config.get('use_clahe', False):
        from skimage import exposure
        imagem = exposure.equalize_adapthist(
            imagem, 
            clip_limit=config.get('clahe_clip_limit', 0.02)
        )
    
    return imagem

def normalizar_linear(imagem):
    """Normalização linear min-max."""
    min_val = np.min(imagem)
    max_val = np.max(imagem)
    if max_val == min_val:
        return np.zeros_like(imagem)
    return (imagem - min_val) / (max_val - min_val)


def normalizar_por_percentil(imagem, low_percent=5, high_percent=99):
    """
    Normalização por percentis (mais agressiva para realçar estrelas).
    
    Valores abaixo do percentil inferior viram 0 (preto),
    valores acima do percentil superior viram 1 (branco).
    """
    low = np.percentile(imagem, low_percent)
    high = np.percentile(imagem, high_percent)
    
    if high == low:
        return np.zeros_like(imagem)
    
    imagem = np.clip(imagem, low, high)
    return (imagem - low) / (high - low)


def equalizar_histograma(imagem):
    """
    Equalização de histograma global (Aula 08).
    """
    return exposure.equalize_hist(imagem)


def aplicar_clahe(imagem, clip_limit=0.03, tile_size=8):
    """
    CLAHE (Contrast Limited Adaptive Histogram Equalization).
    
    Aula 08 - slides 18-19.
    """
    return exposure.equalize_adapthist(
        imagem,
        clip_limit=clip_limit,
        kernel_size=(tile_size, tile_size)
    )


def aplicar_stretch(imagem, config):
    """
    Stretching com saturação de percentis e ajuste de gama.
    """
    low_percent = config.get('low_percent', 5)
    high_percent = config.get('high_percent', 99)
    low = np.percentile(imagem, low_percent)
    high = np.percentile(imagem, high_percent)
    
    if high == low:
        return np.zeros_like(imagem)
    
    imagem = np.clip(imagem, low, high)
    imagem = (imagem - low) / (high - low)
    return imagem


def aplicar_gamma(imagem, gamma=0.8):
    """Correção gamma (Aula 03 - slides 8-9)."""
    return exposure.adjust_gamma(imagem, gamma)


def exibir_info_processamento(imagem_original, imagem_processada):
    """Exibe informações sobre o pré-processamento."""
    print("  Pré-processamento (visualização):")
    print(f"    Original: min={np.min(imagem_original):.3f}, "
          f"max={np.max(imagem_original):.3f}, "
          f"média={np.mean(imagem_original):.3f}")
    print(f"    Processada: min={np.min(imagem_processada):.3f}, "
          f"max={np.max(imagem_processada):.3f}, "
          f"média={np.mean(imagem_processada):.3f}")


# ============================================================================
# TESTE
# ============================================================================

if __name__ == "__main__":
    import sys
    import matplotlib.pyplot as plt
    from ler_fits import carregar_imagem
    
    if len(sys.argv) > 1:
        caminho_teste = sys.argv[1]
        print(f"Testando visualização com múltiplos métodos: {caminho_teste}")
        print("-" * 50)
        
        try:
            img, header = carregar_imagem(caminho_teste)
            
            # Testa diferentes métodos
            metodos = [
                {'metodo': 'percentis', 'low_percent': 5, 'high_percent': 99},
                {'metodo': 'equalizacao'},
                {'metodo': 'clahe', 'clahe_clip_limit': 0.03},
                {'metodo': 'percentis', 'low_percent': 10, 'high_percent': 95},  # padrão antigo
            ]
            
            fig, axes = plt.subplots(2, 2, figsize=(12, 12))
            axes = axes.flatten()
            
            for i, cfg in enumerate(metodos):
                img_proc = pre_processar(img, cfg)
                axes[i].imshow(img_proc, cmap='gray', origin='lower')
                axes[i].set_title(f"{cfg['metodo']} {cfg.get('low_percent', '')} {cfg.get('high_percent', '')}")
                axes[i].axis('off')
            
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("Uso: python melhorar_imagem.py caminho/para/imagem.fits")
