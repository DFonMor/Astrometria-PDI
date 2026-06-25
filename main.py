"""
main.py - Sistema de Astrometria para identificação de campos estrelados

Pipeline de processamento:
    Leitura do FITS (ler_fits)
    Visualização (melhorar_imagem) - apenas para exibição
    Detecção de estrelas (detectar_estrelas) - com photutils
    Plate solving (plate_solve) - com solve-field
    Exibição do resultado (exibir_resultado)
    
Autor: Eduardo Fonseca Morato
Contato: morato@alunos.utfpr.edu.br
Disciplina: ELTD2 - Processamento de Imagens UTFPR
"""

import sys
import argparse
import time
from pathlib import Path

# Importa todas as configurações do constants.py
from constants import (
    CONFIG_VISUALIZACAO,
    CONFIG_DETECCAO,
    CONFIG_PLATE_SOLVE,
    CONFIG_SAIDA,
    FOCAL_LENGTH_MM,
    PIXEL_SIZE_UM,
    SENSOR_WIDTH_PX,
    SENSOR_HEIGHT_PX,
    escala_arcsec_px,
    fov_width_arcmin,
    fov_height_arcmin,
)

# Importa funções dos módulos
from ler_fits import carregar_imagem
from melhorar_imagem import pre_processar, exibir_info_processamento
from detectar_estrelas import detectar_estrelas, exibir_info_deteccao, salvar_estrelas_xy
from plate_solve import resolver_imagem, resolver_imagem_direta
from exibir_resultado import exibir_resultado


# ============================================================================
# FUNÇÃO PRINCIPAL (ORQUESTRAÇÃO DO FLUXO)
# ============================================================================

def processar_imagem(caminho_arquivo):
    """
    Executa o pipeline completo de processamento para uma imagem
    """
    print(f"\n{'='*60}")
    print(f"Processando: {Path(caminho_arquivo).name}")
    print(f"{'='*60}\n")
    
    inicio_total = time.time()
    
    # Obtém o nome base do arquivo (sem extensão)
    base_name = Path(caminho_arquivo).stem
    
    # ============================================================
    # Aquisição
    # ============================================================
    print("[1/5] Carregando imagem...")
    imagem, cabecalho = carregar_imagem(caminho_arquivo)
    print(f"     -> {imagem.shape[0]} x {imagem.shape[1]} pixels")
    
    # ============================================================
    # Visualização (apenas para exibição)
    # ============================================================
    print("[2/5] Preparando visualização...")
    img_vis = pre_processar(imagem, CONFIG_VISUALIZACAO)
    exibir_info_processamento(imagem, img_vis)
    
    # ============================================================
    # Detecção de estrelas (com photutils)
    # ============================================================
    print("[3/5] Detectando estrelas...")
    estrelas = detectar_estrelas(imagem, CONFIG_DETECCAO)
    exibir_info_deteccao(estrelas)
    
    if len(estrelas) < 5:
        print("     -> Poucas estrelas detectadas. Abortando.")
        return None
    
    # Salva estrelas no formato .xy com o mesmo nome base
    xy_file = f"{base_name}.xy"
    salvar_estrelas_xy(estrelas, xy_file)
    print(f"     -> Estrelas salvas em: {xy_file}")
    
    # ============================================================
    # Plate Solving (solve-field)
    # ============================================================
    print("[4/5] Resolvendo campo...")
    
    # Verifica se o arquivo .xy existe
    xy_path = Path(xy_file)
    if not xy_path.exists():
        print(f"     -> Arquivo {xy_file} nao encontrado!")
        return None
    
    # Tenta resolver usando o .xy
    resultado_solve = resolver_imagem(str(xy_path), CONFIG_PLATE_SOLVE)
    
    # Se falhou com .xy, tenta com a imagem diretamente
    if not resultado_solve.get('success', False):
        print("     -> Falha com .xy, tentando com a imagem diretamente...")
        resultado_solve = resolver_imagem_direta(caminho_arquivo, CONFIG_PLATE_SOLVE)
    
    # ============================================================
    # Saída
    # ============================================================
    tempo_total = time.time() - inicio_total
    print("[5/5] Gerando saida...")
    
    # Exibe o resultado com as imagens
    exibir_resultado(
        resultado_solve=resultado_solve,
        estrelas=estrelas,
        img_vis=img_vis,
        img_original=imagem,
        cabecalho=cabecalho,
        tempo_total=tempo_total,
        config=CONFIG_SAIDA
    )
    
    return {
        'imagem': caminho_arquivo,
        'estrelas': len(estrelas),
        'resultado_solve': resultado_solve,
        'tempo': tempo_total
    }


# ============================================================================
# PONTO DE ENTRADA PRINCIPAL
# ============================================================================

def main():
    """Ponto de entrada do programa"""
    
    parser = argparse.ArgumentParser(
        description='Sistema de Astrometria para identificacao de campos estrelados',
        epilog=f'Exemplo: python {sys.argv[0]} imagem.fits'
    )
    
    parser.add_argument(
        'imagem',
        nargs='?',
        help='Caminho para o arquivo .fits a ser processado'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Executa em modo de teste (usa teste.fits)'
    )
    
    parser.add_argument(
        '--info',
        action='store_true',
        help='Exibe informacoes do telescopio'
    )
    
    parser.add_argument(
        '--no-viz',
        action='store_true',
        help='Nao exibe visualizacao das estrelas'
    )
    
    args = parser.parse_args()
    
    # Modo info
    if args.info:
        print(f"\n{'='*50}")
        print("CONFIGURACAO DO TELESCOPIO")
        print(f"{'='*50}")
        print(f"Modelo: Seestar S50")
        print(f"Distancia focal: {FOCAL_LENGTH_MM} mm")
        print(f"Tamanho do pixel: {PIXEL_SIZE_UM} um")
        print(f"Resolucao: {SENSOR_WIDTH_PX} x {SENSOR_HEIGHT_PX} px")
        print(f"Escala de placa: {escala_arcsec_px():.2f} arcsec/px")
        print(f"Campo de visao: {fov_width_arcmin():.1f}' x {fov_height_arcmin():.1f}'")
        print(f"Indices recomendados: 4107, 5206")
        print(f"{'='*50}\n")
        return
    
    # Modo teste
    if args.test:
        caminho = "teste.fits"
        if not Path(caminho).exists():
            print(f"Erro: Imagem de teste nao encontrada: {caminho}")
            print("Coloque um arquivo teste.fits na pasta do projeto.")
            return
    else:
        if not args.imagem:
            parser.print_help()
            print("\nForneca o caminho da imagem ou use --test ou --info")
            return
        caminho = args.imagem
    
    # Verifica se o arquivo existe
    if not Path(caminho).exists():
        print(f"Erro: Arquivo nao encontrado: {caminho}")
        return
    
    # Executa o processamento
    try:
        resultado = processar_imagem(caminho)
        
        if resultado:
            print(f"\n{'='*60}")
            if resultado['resultado_solve'].get('success', False):
                print("Pipeline concluido com sucesso!")
            else:
                print("Pipeline concluido, mas a imagem nao foi resolvida")
                print("   Verifique os indices, a escala ou a qualidade da imagem.")
            print(f"{'='*60}")
        else:
            print("\nFalha no processamento da imagem")
            
    except KeyboardInterrupt:
        print("\n\nProcessamento interrompido pelo usuario.")
    except Exception as e:
        print(f"\nErro durante o processamento: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
