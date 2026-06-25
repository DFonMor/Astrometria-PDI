"""
plate_solve.py - Módulo para resolução astrométrica usando solve-field (versão 0.93)

Este módulo utiliza as estrelas detectadas (arquivo .xy) e chama o solve-field
para identificar o campo estelar da imagem.

Funcionalidades:
    - Converte .xy para FITS BINTABLE
    - Lista arquivos de índice
    - Cria arquivo de configuração temporário
    - Executa solve-field com --config
    - Lê e interpreta WCS
"""

import subprocess
import shutil
import tempfile
import os
import sys
from pathlib import Path
from astropy.io import fits
from astropy.wcs import WCS
import numpy as np


def encontrar_solve_field():
    """Encontra o executável solve-field no sistema."""
    if shutil.which('solve-field'):
        return 'solve-field'
    return None


def listar_indices(diretorio):
    """Lista todos os arquivos de índice no diretório."""
    diretorio = Path(diretorio)
    if not diretorio.exists():
        return []
    indices = list(diretorio.glob('index-*.fits'))
    indices.extend(diretorio.glob('index-*.fit'))
    return sorted([str(i) for i in indices])


def criar_arquivo_config(indices, arquivo_config):
    """Cria um arquivo de configuração para o solve-field."""
    with open(arquivo_config, 'w') as f:
        f.write("# Config file for astrometry-engine\n")
        for idx in indices:
            f.write(f"index {idx}\n")


def converter_xy_para_fits(arquivo_xy, arquivo_saida=None):
    """Converte um arquivo .xy para FITS BINTABLE."""
    xy_path = Path(arquivo_xy)
    if not xy_path.exists():
        raise FileNotFoundError(f"Arquivo .xy não encontrado: {arquivo_xy}")
    
    if arquivo_saida is None:
        arquivo_saida = xy_path.parent / f"{xy_path.stem}.axy.fits"
    
    dados = []
    with open(xy_path, 'r') as f:
        for linha in f:
            linha = linha.strip()
            if not linha or linha.startswith('#'):
                continue
            partes = linha.split()
            if len(partes) >= 2:
                try:
                    x = float(partes[0])
                    y = float(partes[1])
                    fluxo = float(partes[2]) if len(partes) >= 3 else 1.0
                    dados.append((x, y, fluxo))
                except ValueError:
                    continue
    
    if not dados:
        raise ValueError("Nenhum dado válido encontrado no arquivo .xy")
    
    dtype = [('X', 'f8'), ('Y', 'f8'), ('FLUX', 'f8')]
    array = np.array(dados, dtype=dtype)
    hdu = fits.BinTableHDU(array)
    hdu.header['EXTNAME'] = 'XYLIST'
    hdu.writeto(arquivo_saida, overwrite=True)
    
    return str(arquivo_saida)


def resolver_imagem(arquivo_xy, config=None):
    """
    Resolve uma imagem usando o arquivo .xy com as estrelas detectadas.
    """
    if config is None:
        config = {
            'indices_dir': '/home/dell/Astrometria-PDI/data',
            'scale_low': 0.3,
            'scale_high': 1.0,
            'width': 1920,
            'height': 1080,
            'timeout': 120,
            'verbose': True,
        }
    
    solve_cmd = encontrar_solve_field()
    if not solve_cmd:
        return {'success': False, 'erro': 'solve-field não encontrado'}
    
    xy_path = Path(arquivo_xy)
    if not xy_path.exists():
        return {'success': False, 'erro': f'Arquivo .xy não encontrado: {arquivo_xy}'}
    
    # Procura o arquivo .fits correspondente
    fits_path = None
    for ext in ['.fits', '.fit', '.FITS']:
        possivel_fits = xy_path.parent / f"{xy_path.stem}{ext}"
        if possivel_fits.exists():
            fits_path = possivel_fits
            break
    
    if not fits_path or not fits_path.exists():
        return {'success': False, 'erro': 'Arquivo .fits correspondente não encontrado'}
    
    # Converte .xy para FITS
    try:
        axy_fits = converter_xy_para_fits(xy_path)
        if config.get('verbose', True):
            print(f"  🔭 Resolvendo: {fits_path.name}")
            print(f"     Usando: {xy_path.name}")
            print(f"     ✅ Convertido para: {axy_fits}")
    except Exception as e:
        return {'success': False, 'erro': f'Erro ao converter .xy para FITS: {e}'}
    
    # Lista os índices
    indices = listar_indices(config['indices_dir'])
    if not indices:
        return {'success': False, 'erro': f'Nenhum arquivo de índice encontrado em {config["indices_dir"]}'}
    
    if config.get('verbose', True):
        print(f"     Encontrados {len(indices)} arquivos de índice")
        print(f"     Escala: {config['scale_low']}° - {config['scale_high']}°")
    
    # Cria arquivo de configuração temporário
    with tempfile.NamedTemporaryFile(mode='w', suffix='.cfg', delete=False) as f:
        config_path = f.name
        criar_arquivo_config(indices, config_path)
    
    base_name = fits_path.stem
    solved_file = f"{base_name}.solved"
    wcs_file = f"{base_name}.wcs"
    
    args = [
        str(fits_path),
        '--config', config_path,
        '--overwrite',
        '--no-plots',
        '--scale-low', str(config['scale_low']),
        '--scale-high', str(config['scale_high']),
        '--width', str(config['width']),
        '--height', str(config['height']),
        '--solved', solved_file,
        '--wcs', wcs_file,
        '--new-fits', 'none',
        '--match', 'none',
        '--corr', 'none',
        '--rdls', 'none',
    ]
    
    try:
        result = subprocess.run(
            ['solve-field'] + args,
            capture_output=True,
            text=True,
            timeout=config.get('timeout', 120)
        )
    except subprocess.TimeoutExpired:
        return {'success': False, 'erro': f'Tempo limite excedido ({config["timeout"]}s)'}
    except Exception as e:
        return {'success': False, 'erro': f'Erro ao executar solve-field: {e}'}
    finally:
        try:
            os.unlink(config_path)
        except:
            pass
    
    if not Path(solved_file).exists():
        return {'success': False, 'erro': 'Não foi possível resolver a imagem', 'saida': result.stdout + result.stderr}
    
    if config.get('verbose', True):
        print(f"     ✅ Resolvido!")
    
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
            cdelt1 = header.get('CDELT1', 0)
            if cdelt1 == 0:
                cdelt1 = header.get('CD1_1', 0)
            pixel_scale = abs(cdelt1) * 3600
    except Exception as e:
        return {'success': False, 'erro': f'Erro ao ler WCS: {e}'}
    
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
            'fits': str(fits_path),
            'axy_fits': axy_fits,
        },
        'header': dict(header),
    }


def resolver_imagem_direta(imagem_path, config=None):
    """Resolve uma imagem diretamente (fallback sem .xy)."""
    if config is None:
        config = {
            'indices_dir': '/home/dell/Astrometria-PDI/data',
            'scale_low': 0.3,
            'scale_high': 1.0,
            'timeout': 120,
            'verbose': True,
        }
    
    fits_path = Path(imagem_path)
    if not fits_path.exists():
        return {'success': False, 'erro': f'Arquivo não encontrado: {imagem_path}'}
    
    indices = listar_indices(config['indices_dir'])
    if not indices:
        return {'success': False, 'erro': 'Nenhum arquivo de índice encontrado'}
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.cfg', delete=False) as f:
        config_path = f.name
        criar_arquivo_config(indices, config_path)
    
    base_name = fits_path.stem
    solved_file = f"{base_name}.solved"
    wcs_file = f"{base_name}.wcs"
    
    args = [
        str(fits_path),
        '--config', config_path,
        '--overwrite',
        '--no-plots',
        '--scale-low', str(config['scale_low']),
        '--scale-high', str(config['scale_high']),
        '--solved', solved_file,
        '--wcs', wcs_file,
        '--new-fits', 'none',
        '--match', 'none',
        '--corr', 'none',
        '--rdls', 'none',
    ]
    
    try:
        result = subprocess.run(
            ['solve-field'] + args,
            capture_output=True,
            text=True,
            timeout=config.get('timeout', 120)
        )
    except Exception as e:
        return {'success': False, 'erro': str(e)}
    finally:
        try:
            os.unlink(config_path)
        except:
            pass
    
    if not Path(solved_file).exists():
        return {'success': False, 'erro': 'Não foi possível resolver', 'saida': result.stdout + result.stderr}
    
    try:
        with fits.open(wcs_file) as hdul:
            header = hdul[0].header
            wcs = WCS(header)
            crpix1 = header.get('CRPIX1', 0)
            crpix2 = header.get('CRPIX2', 0)
            ra_center, dec_center = wcs.all_pix2world([[crpix1, crpix2]], 0)[0]
            objeto = header.get('OBJECT', 'Desconhecido')
            cdelt1 = header.get('CDELT1', 0)
            if cdelt1 == 0:
                cdelt1 = header.get('CD1_1', 0)
            pixel_scale = abs(cdelt1) * 3600
            return {
                'success': True,
                'ra': float(ra_center),
                'dec': float(dec_center),
                'objeto': str(objeto),
                'pixel_scale': float(pixel_scale),
                'arquivos': {'wcs': wcs_file, 'solved': solved_file},
                'header': dict(header),
            }
    except Exception as e:
        return {'success': False, 'erro': f'Erro ao ler WCS: {e}'}
