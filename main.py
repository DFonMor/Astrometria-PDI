"""
main.py - Sistema de Astrometria para identificação de campos estrelados
"""

import sys
import argparse
import time
from pathlib import Path

import constants as c

# Importa funções dos módulos (todos na mesma pasta)
from ler_fits import carregar_imagem
from melhorar_imagem import pre_processar
from detectar_estrelas import detectar_estrelas
from extrair_padroes import extrair_padroes
from buscar_matches import buscar_matches
from identificar_campo import identificar_campo
from exibir_resultado import exibir_resultado


# ============================================================================
# FUNÇÃO PRINCIPAL (ORQUESTRAÇÃO DO FLUXO)
# ============================================================================

def processar_imagem(caminho_arquivo):
    """
    Executa o pipeline completo de processamento para uma imagem
    """
    print(f"\n{'='*60}")
    print(f"Processando: {caminho_arquivo}")
    print(f"{'='*60}\n")
    
    inicio_total = time.time()
    
    print("[1/7] Carregando imagem...")
    imagem, cabecalho = carregar_imagem(caminho_arquivo)
    
    print("[2/7] Pré-processando imagem...")
    imagem_proc = pre_processar(imagem)
    
    print("[3/7] Detectando estrelas...")
    estrelas = detectar_estrelas(imagem_proc)
    print(f"     → {len(estrelas)} estrelas detectadas")
    
    if len(estrelas) < 5:
        print("     → ⚠️ Poucas estrelas detectadas. Abortando.")
        return None
    
    print("[4/7] Extraindo padrões...")
    padroes = extrair_padroes(estrelas)
    print(f"     → {len(padroes)} padrões gerados")
    
    print("[5/7] Buscando correspondências...")
    votos = buscar_matches(padroes)
    
    print("[6/7] Identificando campo...")
    resultado = identificar_campo(votos)
    
    tempo_total = time.time() - inicio_total
    print("[7/7] Gerando saída...")
    exibir_resultado(resultado, tempo_total)
    
    return {
        'imagem': caminho_arquivo,
        'estrelas': len(estrelas),
        'padroes': len(padroes),
        'resultado': resultado,
        'tempo': tempo_total
    }


def main():
    """Ponto de entrada do programa"""
        
    parser = argparse.ArgumentParser(
        description='Sistema de Astrometria para identificação de campos estrelados',
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
        help='Executa em modo de teste'
    )
    
    parser.add_argument(
        '--info',
        action='store_true',
        help='Exibe informações do telescópio'
    )
    
    args = parser.parse_args()
    
    # Modo info
    if args.info:
        print(f"\n{'='*50}")
        print("CONFIGURAÇÃO DO TELESCÓPIO")
        print(f"{'='*50}")
        print(f"Modelo: Seestar S50")
        print(f"Distância focal: {c.FOCAL_LENGTH_MM} mm")
        print(f"Tamanho do pixel: {c.PIXEL_SIZE_UM} µm")
        print(f"Resolução: {c.SENSOR_WIDTH_PX} × {c.SENSOR_HEIGHT_PX} px")
        print(f"Escala de placa: {c.escala_arcsec_px():.2f} arcsec/px")
        print(f"Campo de visão: {c.fov_width_arcmin():.1f}' × {c.fov_height_arcmin():.1f}'")
        print(f"{'='*50}\n")
        return
    
    # Modo teste
    if args.test:
        caminho = "data/teste/imagem_exemplo.fits"
        if not Path(caminho).exists():
            print(f"Erro: Imagem de teste não encontrada em {caminho}")
            return
    else:
        if not args.imagem:
            parser.print_help()
            print("\n⚠️ Forneça o caminho da imagem ou use --test ou --info")
            return
        caminho = args.imagem
    
    if not Path(caminho).exists():
        print(f"Erro: Arquivo não encontrado: {caminho}")
        return
    
    try:
        resultado = processar_imagem(caminho)
        if resultado:
            print(f"\n{'='*60}")
            print("✅ PROCESSAMENTO CONCLUÍDO")
            print(f"{'='*60}")
    except Exception as e:
        print(f"\n❌ Erro durante o processamento: {e}")
        raise


if __name__ == "__main__":
    main()