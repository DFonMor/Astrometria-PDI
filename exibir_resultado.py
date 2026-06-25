"""
exibir_resultado.py - Módulo para exibição dos resultados

Este módulo é responsável por exibir os resultados do pipeline de forma clara
e organizada para o usuário.

Funcionalidades:
    - Exibir informações do plate solving (RA, Dec, campo)
    - Exibir estatísticas da detecção de estrelas
    - Exibir arquivos gerados
    - Exibir resumo do tempo de processamento
    - Exibir imagens

Autor: Eduardo Fonseca Morato
Contato: morato@alunos.utfpr.edu.br
Disciplina: ELTD2 - Processamento de Imagens UTFPR
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from pathlib import Path
from PIL import Image
from io import BytesIO


def exibir_resultado(resultado_solve, estrelas, img_vis, img_original=None, cabecalho=None, tempo_total=None):
    """
    Exibe os resultados do processamento com visualização gráfica.
    
    Args:
        resultado_solve (dict): Resultado do plate solving
        estrelas (list): Lista de estrelas detectadas
        img_vis (numpy.ndarray): Imagem melhorada (para visualização)
        img_original (numpy.ndarray, optional): Imagem original (crua)
        cabecalho (dict, optional): Cabeçalho FITS para comparar RA/Dec
        tempo_total (float, optional): Tempo total de processamento
    """
    
    # ============================================================
    # 1. EXIBE INFORMAÇÕES NO CONSOLE
    # ============================================================
    
    print(f"\n{'='*60}")
    print("📊 RESULTADO DA ASTROMETRIA")
    print(f"{'='*60}")
    
    print(f"\n  ⭐ ESTRELAS DETECTADAS: {len(estrelas)}")
    if estrelas:
        s_mais = estrelas[0]
        print(f"     🌟 Mais brilhante: fluxo={s_mais['fluxo']:.1f}, "
              f"posição=({s_mais['x']:.1f}, {s_mais['y']:.1f})px")
    
    # ============================================================
    # 2. EXIBE COORDENADAS (HEADER vs RESOLVIDO)
    # ============================================================
    
    # Coordenadas do cabeçalho (Seestar)
    ra_header = cabecalho.get('RA') if cabecalho else None
    dec_header = cabecalho.get('DEC') if cabecalho else None
    
    # Coordenadas resolvidas
    ra_solve = resultado_solve.get('ra') if resultado_solve.get('success') else None
    dec_solve = resultado_solve.get('dec') if resultado_solve.get('success') else None
    
    print(f"\n  📍 COORDENADAS:")
    
    if ra_header is not None and dec_header is not None:
        print(f"     Cabeçalho (Seestar): RA={ra_header:.6f}°, Dec={dec_header:.6f}°")
    else:
        print(f"     Cabeçalho (Seestar): RA=Não disponível, Dec=Não disponível")
    
    if ra_solve is not None and dec_solve is not None:
        print(f"     Resolvido (solve-field): RA={ra_solve:.6f}°, Dec={dec_solve:.6f}°")
        
        # Calcula diferença
        if ra_header is not None and dec_header is not None:
            diff_ra = (ra_solve - float(ra_header)) * 3600  # em segundos de arco
            diff_dec = (dec_solve - float(dec_header)) * 3600
            print(f"     Diferença: ΔRA={diff_ra:.2f}\", ΔDec={diff_dec:.2f}\"")
    else:
        print(f"     Resolvido (solve-field): NÃO RESOLVIDO")
    
    if resultado_solve.get('success', False):
        print(f"\n  ✅ CAMPO IDENTIFICADO: {resultado_solve['objeto']}")
        if resultado_solve.get('pixel_scale'):
            print(f"  📐 Escala: {resultado_solve['pixel_scale']:.3f} \"/pixel")
    else:
        print(f"\n  ❌ IMAGEM NÃO RESOLVIDA")
        if 'erro' in resultado_solve:
            print(f"     Erro: {resultado_solve['erro']}")
    
    if tempo_total is not None:
        print(f"\n  ⏱️ Tempo: {tempo_total:.2f} s")
    
    print(f"{'='*60}\n")
    
    # ============================================================
    # 3. CRIA IMAGEM COM ESTRELAS
    # ============================================================
    
    img_estrelas = criar_imagem_estrelas_matplotlib(img_vis, estrelas)
    
    # ============================================================
    # 4. EXIBE AS IMAGENS
    # ============================================================
    
    n_imagens = 2  # melhorada + estrelas
    if img_original is not None:
        n_imagens = 3
    
    fig, axes = plt.subplots(1, n_imagens, figsize=(n_imagens * 5, 5))
    
    if n_imagens == 1:
        axes = [axes]
    
    idx = 0
    
    # Imagem 1: Original (se disponível)
    if img_original is not None:
        img_orig_norm = (img_original - np.min(img_original)) / (np.max(img_original) - np.min(img_original) + 1e-10)
        axes[idx].imshow(img_orig_norm, cmap='gray', origin='lower', vmin=0, vmax=1)
        axes[idx].set_title("Imagem Original", fontsize=12)
        axes[idx].axis('off')
        idx += 1
    
    # Imagem 2: Melhorada
    axes[idx].imshow(img_vis, cmap='gray', origin='lower')
    axes[idx].set_title("Imagem Melhorada", fontsize=12)
    axes[idx].axis('off')
    idx += 1
    
    # Imagem 3: Com estrelas marcadas
    axes[idx].imshow(img_estrelas, origin='lower')
    axes[idx].set_title("Estrelas Detectadas", fontsize=12)
    axes[idx].axis('off')
    
    plt.tight_layout()
    plt.show()
    
    # ============================================================
    # 5. SALVA AS IMAGENS
    # ============================================================
    
    pasta_saida = Path("resultados")
    pasta_saida.mkdir(exist_ok=True)
    
    nome_base = "resultado"
    if resultado_solve.get('success', False) and resultado_solve.get('objeto') != 'Desconhecido':
        nome_base = resultado_solve.get('objeto', 'identificado').replace(' ', '_')
    
    caminho_figura = pasta_saida / f"{nome_base}_visualizacao.png"
    fig.savefig(caminho_figura, dpi=150, bbox_inches='tight', facecolor='black')
    print(f"💾 Visualização salva em: {caminho_figura}")
    
    # Salva imagens individuais
    if img_original is not None:
        plt.imsave(pasta_saida / f"{nome_base}_original.png", img_orig_norm, cmap='gray', origin='lower', vmin=0, vmax=1)
    
    plt.imsave(pasta_saida / f"{nome_base}_melhorada.png", img_vis, cmap='gray', origin='lower')
    plt.imsave(pasta_saida / f"{nome_base}_estrelas.png", img_estrelas, origin='lower')
    
    print(f"💾 Imagens individuais salvas em: {pasta_saida}")
    
    plt.close(fig)


def criar_imagem_estrelas_matplotlib(img_vis, estrelas, max_estrelas=50):
    """
    Cria uma imagem com as estrelas marcadas usando matplotlib.
    Retorna um array RGB com a orientação corrigida.
    """
    height, width = img_vis.shape
    
    fig, ax = plt.subplots(1, 1, figsize=(width/100, height/100), dpi=100)
    ax.imshow(img_vis, cmap='gray', origin='lower')
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    
    for s in estrelas[:max_estrelas]:
        ax.plot(s['x'], s['y'], 'r+', markersize=10, markeredgewidth=2)
        if s.get('area', 0) > 0:
            radius = np.sqrt(s['area'] / np.pi) * 1.5
            circle = Circle((s['x'], s['y']), radius, color='yellow', fill=False, linewidth=1.5)
            ax.add_patch(circle)
    
    if estrelas:
        s_mais = estrelas[0]
        ax.plot(s_mais['x'], s_mais['y'], 'b+', markersize=14, markeredgewidth=3)
        ax.text(s_mais['x']+15, s_mais['y']-15, f'{s_mais["fluxo"]:.1f}', 
                color='cyan', fontsize=10, weight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.7))
    
    ax.axis('off')
    
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight', pad_inches=0, facecolor='black')
    buf.seek(0)
    
    img_array = np.array(Image.open(buf))
    plt.close(fig)
    
    # Inverte verticalmente
    img_array = np.flipud(img_array)
    
    return img_array
