"""
plate_solve.py - Módulo para resolução astrométrica usando solve-field

Este módulo utiliza as estrelas detectadas (arquivo .xy) e chama o solve-field
para identificar o campo estelar da imagem.

Conceitos da disciplina: Reconhecimento de padrões (nível alto).
"""

import subprocess
from pathlib import Path
from astropy.io import fits
from astropy.wcs import WCS


def resolver_imagem(arquivo_xy, config=None):
    """
    Resolve uma imagem usando o arquivo .xy com as estrelas detectadas.
    
    Args:
        arquivo_xy (str): Caminho para o arquivo .xy com as estrelas
        config (dict, optional): Parâmetros de configuração.
    
    Returns:
        dict: Resultado da resolução com:
              - success (bool): True se resolveu
              - ra (float): RA do centro (graus)
              - dec (float): Dec do centro (graus)
              - objeto (str): Nome do campo
              - pixel_scale (float): Escala em arcsec/pixel
              - arquivos (dict): Arquivos gerados
              - erro (str): Mensagem de erro (se houver)
    """
    
    if config is None:
        config = {
            'indices_dir': 'data',
            'scale_low': 0.3,
            'scale_high': 1.0,
            'width': 1920,
            'height': 1080,
            'timeout': 120,
            'verbose': True,
        }
    
    # Verifica se o arquivo .xy existe
    xy_path = Path(arquivo_xy)
    if not xy_path.exists():
        return {'success': False, 'erro': f'Arquivo .xy não encontrado: {arquivo_xy}'}
    
    if config.get('verbose', True):
        print(f"  🔭 Resolvendo com arquivo: {xy_path.name}")
        print(f"     Índices: {config['indices_dir']}")
        print(f"     Escala: {config['scale_low']}° - {config['scale_high']}°")
        print(f"     Dimensões: {config['width']} x {config['height']} px")
    
    # ============================================================
    # PASSO 1: Executa o solve-field com o arquivo .xy
    # ============================================================
    
    # O nome base para os arquivos de saída
    base_name = xy_path.stem  # "estrelas"
    
    cmd = [
        'solve-field',
        str(xy_path),
        '--overwrite',
        '--no-plots',
        '--scale-low', str(config['scale_low']),
        '--scale-high', str(config['scale_high']),
        '--index-dir', config['indices_dir'],
        '--width', str(config['width']),
        '--height', str(config['height']),
        '--new-fits', 'none',
        '--match', 'none',
        '--corr', 'none',
        '--rdls', 'none',
        '--solved', 'none'
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=config['timeout']
        )
    except subprocess.TimeoutExpired:
        return {'success': False, 'erro': f'Tempo limite excedido ({config["timeout"]}s)'}
    except FileNotFoundError:
        return {'success': False, 'erro': 'solve-field não encontrado. Instale o astrometry.net.'}
    
    # ============================================================
    # PASSO 2: Verifica se resolveu
    # ============================================================
    
    solved_file = f"{base_name}.solved"
    wcs_file = f"{base_name}.wcs"
    
    if not Path(solved_file).exists():
        # Se não resolveu, tenta com a imagem original (fallback)
        return resolver_imagem_direta(None, config)
    
    if config.get('verbose', True):
        print(f"     ✅ Resolvido!")
    
    # ============================================================
    # PASSO 3: Lê o arquivo WCS
    # ============================================================
    
    if not Path(wcs_file).exists():
        return {'success': False, 'erro': 'Arquivo WCS não encontrado'}
    
    try:
        with fits.open(wcs_file) as hdul:
            header = hdul[0].header
            wcs = WCS(header)
            
            crpix1 = header.get('CRPIX1', 0)
            crpix2 = header.get('CRPIX2', 0)
            
            ra_center, dec_center = wcs.all_pix2world([[crpix1, crpix2]], 0)[0]
            objeto = header.get('OBJECT', 'Desconhecido')
            pixel_scale = abs(header.get('CDELT1', 0)) * 3600
            
    except Exception as e:
        return {'success': False, 'erro': f'Erro ao ler WCS: {e}'}
    
    # ============================================================
    # PASSO 4: Retorna o resultado
    # ============================================================
    
    return {
        'success': True,
        'ra': float(ra_center),
        'dec': float(dec_center),
        'objeto': str(objeto),
        'pixel_scale': float(pixel_scale),
        'arquivos': {
            'wcs': wcs_file,
            'solved': solved_file,
            'xy': str(xy_path),
        },
        'header': dict(header),
    }


def resolver_imagem_direta(imagem_path, config=None):
    """
    Fallback: resolve a imagem diretamente (sem arquivo .xy).
    
    Args:
        imagem_path (str): Caminho para o arquivo .fits
        config (dict, optional): Parâmetros de configuração.
    
    Returns:
        dict: Resultado da resolução
    """
    if imagem_path is None or not Path(imagem_path).exists():
        return {'success': False, 'erro': 'Falha no fallback: imagem não encontrada'}
    
    if config is None:
        config = {
            'indices_dir': 'data',
            'scale_low': 0.3,
            'scale_high': 1.0,
            'timeout': 120,
            'verbose': True,
        }
    
    cmd = [
        'solve-field',
        str(imagem_path),
        '--overwrite',
        '--no-plots',
        '--scale-low', str(config['scale_low']),
        '--scale-high', str(config['scale_high']),
        '--index-dir', config['indices_dir'],
        '--new-fits', 'none',
        '--match', 'none',
        '--wcs', 'none',
        '--corr', 'none',
        '--rdls', 'none',
        '--solved', 'none'
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=config['timeout'])
    except Exception as e:
        return {'success': False, 'erro': str(e)}
    
    base_name = Path(imagem_path).stem
    solved_file = f"{base_name}.solved"
    wcs_file = f"{base_name}.wcs"
    
    if not Path(solved_file).exists():
        return {'success': False, 'erro': 'Não foi possível resolver'}
    
    try:
        with fits.open(wcs_file) as hdul:
            header = hdul[0].header
            wcs = WCS(header)
            
            crpix1 = header.get('CRPIX1', 0)
            crpix2 = header.get('CRPIX2', 0)
            
            ra_center, dec_center = wcs.all_pix2world([[crpix1, crpix2]], 0)[0]
            objeto = header.get('OBJECT', 'Desconhecido')
            pixel_scale = abs(header.get('CDELT1', 0)) * 3600
            
            return {
                'success': True,
                'ra': float(ra_center),
                'dec': float(dec_center),
                'objeto': str(objeto),
                'pixel_scale': float(pixel_scale),
                'arquivos': {
                    'wcs': wcs_file,
                    'solved': solved_file,
                },
                'header': dict(header),
            }
    except Exception as e:
        return {'success': False, 'erro': f'Erro ao ler WCS: {e}'}


def gerar_imagem_quads(imagem_path, saida=None, config=None):
    """
    Gera uma imagem com os quads desenhados.
    
    Args:
        imagem_path (str): Caminho para o arquivo .fits
        saida (str, optional): Caminho para o arquivo de saída (.pnm ou .png)
        config (dict, optional): Parâmetros de configuração.
    
    Returns:
        dict: Resultado com caminho do arquivo gerado
    """
    
    if config is None:
        config = {
            'indices_dir': 'data',
            'scale_low': 0.3,
            'scale_high': 1.0,
            'timeout': 120,
        }
    
    if saida is None:
        base = Path(imagem_path).stem
        saida = f"{base}_quads.pnm"
    
    cmd = [
        'solve-field',
        str(imagem_path),
        '--overwrite',
        '--no-plots',
        '--scale-low', str(config['scale_low']),
        '--scale-high', str(config['scale_high']),
        '--index-dir', config['indices_dir'],
        '--pnm', saida,
        '--new-fits', 'none',
        '--match', 'none',
        '--wcs', 'none',
        '--corr', 'none',
        '--rdls', 'none',
        '--solved', 'none'
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=config.get('timeout', 120))
        
        if Path(saida).exists():
            return {'success': True, 'arquivo': saida}
        else:
            return {'success': False, 'erro': 'Arquivo não gerado'}
            
    except Exception as e:
        return {'success': False, 'erro': str(e)}


# ============================================================================
# TESTE
# ============================================================================

if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    if len(sys.argv) > 1:
        # Se receber um .fits, usa o arquivo .xy correspondente
        entrada = sys.argv[1]
        
        if entrada.endswith('.fits'):
            # Tenta usar o .xy gerado pelo detectar_estrelas
            xy_file = Path("saidas_teste") / "estrelas.xy"
            if not xy_file.exists():
                print(f"⚠️ Arquivo .xy não encontrado em {xy_file}")
                print("   Execute primeiro: python detectar_estrelas.py teste.fits")
                sys.exit(1)
            entrada = str(xy_file)
        
        print(f"Testando plate_solve com: {entrada}")
        print("-" * 50)
        
        # Configuração com dimensões do Seestar S50
        config = {
            'indices_dir': 'data',
            'scale_low': 0.3,
            'scale_high': 1.0,
            'width': 1920,
            'height': 1080,
            'timeout': 120,
            'verbose': True,
        }
        
        resultado = resolver_imagem(entrada, config)
        
        if resultado['success']:
            print(f"\n✅ Resolvido!")
            print(f"  RA: {resultado['ra']:.6f}°")
            print(f"  Dec: {resultado['dec']:.6f}°")
            print(f"  Objeto: {resultado['objeto']}")
            print(f"  Escala: {resultado['pixel_scale']:.3f} \"/pixel")
            
            if 'arquivos' in resultado:
                print("\n  📁 Arquivos gerados:")
                for nome, caminho in resultado['arquivos'].items():
                    if Path(caminho).exists():
                        print(f"     {nome}: {caminho}")
        else:
            print(f"\n❌ Falha: {resultado.get('erro', 'Erro desconhecido')}")
            if 'saida' in resultado:
                print(f"\nSaída do solve-field:\n{resultado['saida']}")
    else:
        print("Uso: python plate_solve.py caminho/para/imagem.fits")
        print("\nExemplo:")
        print("  python plate_solve.py teste.fits")
        print("  python plate_solve.py saidas_teste/estrelas.xy")