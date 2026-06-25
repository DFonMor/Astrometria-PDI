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
import glob
import tempfile
import os
import sys
from pathlib import Path
from astropy.io import fits
from astropy.wcs import WCS


def encontrar_solve_field():
    """
    Encontra o executável solve-field no sistema Linux.
    
    Returns:
        str: Caminho para solve-field ou None se não encontrado
    """
    if shutil.which('solve-field'):
        return 'solve-field'
    return None


def listar_indices(diretorio):
    """
    Lista todos os arquivos de índice no diretório.
    
    Args:
        diretorio (str): Caminho para o diretório com os índices
    
    Returns:
        list: Lista de caminhos completos dos índices
    """
    diretorio = Path(diretorio)
    if not diretorio.exists():
        return []
    
    # Procura por arquivos de índice em vários formatos
    padroes = ['index-*.fits', 'index-*.fit', '*.fits']
    indices = []
    
    for padrao in padroes:
        indices.extend(glob.glob(str(diretorio / padrao)))
    
    # Filtra apenas arquivos que parecem ser índices (contêm 'index' no nome)
    indices = [i for i in indices if 'index' in Path(i).stem.lower()]
    
    return sorted(indices)


def criar_arquivo_config(indices, arquivo_config):
    """
    Cria um arquivo de configuração para o solve-field.
    
    Formato do arquivo de configuração:
        index /caminho/para/index-xxx.fits
        index /caminho/para/index-yyy.fits
        ...
    
    Args:
        indices (list): Lista de caminhos dos índices
        arquivo_config (str): Caminho para o arquivo de configuração
    """
    with open(arquivo_config, 'w') as f:
        f.write("# Arquivo de configuração gerado pelo plate_solve.py\n")
        f.write(f"# Total de índices: {len(indices)}\n\n")
        for idx in indices:
            f.write(f"index {idx}\n")


def converter_xy_para_fits(arquivo_xy, arquivo_saida=None):
    """
    Converte um arquivo .xy para FITS BINTABLE.
    
    Args:
        arquivo_xy (str): Caminho para o arquivo .xy
        arquivo_saida (str, optional): Caminho para o arquivo .fits de saída
    
    Returns:
        str: Caminho para o arquivo .fits criado
    """
    import numpy as np
    
    xy_path = Path(arquivo_xy)
    if not xy_path.exists():
        raise FileNotFoundError(f"Arquivo .xy não encontrado: {arquivo_xy}")
    
    if arquivo_saida is None:
        arquivo_saida = xy_path.parent / f"{xy_path.stem}.axy.fits"
    
    # Tenta diferentes encodings
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'utf-16']
    conteudo = None
    
    for encoding in encodings:
        try:
            with open(xy_path, 'r', encoding=encoding) as f:
                conteudo = f.readlines()
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    if conteudo is None:
        with open(xy_path, 'rb') as f:
            raw_data = f.read()
            texto = raw_data.decode('utf-8', errors='ignore')
            conteudo = texto.splitlines()
    
    # Pula linhas de comentário e processa dados
    dados = []
    for linha in conteudo:
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
    
    # Cria um array numpy estruturado
    dtype = [('X', 'f8'), ('Y', 'f8'), ('FLUX', 'f8')]
    array = np.array(dados, dtype=dtype)
    
    # Cria o HDU
    hdu = fits.BinTableHDU(array)
    hdu.header['EXTNAME'] = 'XYLIST'
    
    # Salva
    hdu.writeto(arquivo_saida, overwrite=True)
    
    return str(arquivo_saida)


def resolver_imagem(arquivo_xy, config=None):
    """
    Resolve uma imagem usando o arquivo .xy com as estrelas detectadas.
    Compatível com solve-field versão 0.93.
    
    Args:
        arquivo_xy (str): Caminho para o arquivo .xy com as estrelas
        config (dict, optional): Parâmetros de configuração
    
    Returns:
        dict: Resultado da resolução com:
              - success (bool): True se resolveu
              - ra (float): RA do centro (graus)
              - dec (float): Dec do centro (graus)
              - objeto (str): Nome do campo
              - pixel_scale (float): Escala em arcsec/pixel
              - arquivos (dict): Arquivos gerados
              - header (dict): Cabeçalho WCS
    """
    
    # Configurações padrão
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
    
    # Verifica se o solve-field existe
    solve_cmd = encontrar_solve_field()
    if not solve_cmd:
        return {
            'success': False, 
            'erro': 'solve-field não encontrado. Instale: sudo apt install astrometry.net'
        }
    
    # Verifica se o arquivo .xy existe
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
    
    if not fits_path:
        # Tenta na pasta atual
        possivel_fits = Path("teste.fits")
        if possivel_fits.exists():
            fits_path = possivel_fits
    
    if not fits_path:
        fits_files = list(Path(".").glob("*.fits"))
        if fits_files:
            fits_path = fits_files[0]
    
    if not fits_path:
        return {'success': False, 'erro': 'Arquivo .fits correspondente não encontrado'}
    
    # ============================================================
    # PASSO 1: Converte .xy para FITS BINTABLE
    # ============================================================
    
    try:
        axy_fits = converter_xy_para_fits(xy_path)
        if config.get('verbose', True):
            print(f"  🔭 Resolvendo imagem: {fits_path.name}")
            print(f"     Usando lista de estrelas: {xy_path.name}")
            print(f"     ✅ .xy convertido para: {axy_fits}")
    except Exception as e:
        return {'success': False, 'erro': f'Erro ao converter .xy para FITS: {e}'}
    
    # ============================================================
    # PASSO 2: Lista os índices
    # ============================================================
    
    indices = listar_indices(config['indices_dir'])
    
    if not indices:
        return {
            'success': False, 
            'erro': f'Nenhum arquivo de índice encontrado em {config["indices_dir"]}'
        }
    
    if config.get('verbose', True):
        print(f"     Encontrados {len(indices)} arquivos de índice")
        print(f"     Escala: {config['scale_low']}° - {config['scale_high']}°")
        print(f"     Dimensões: {config['width']} x {config['height']} px")
        print(f"     Versão do solve-field: 0.93 (usando --config)")
    
    # ============================================================
    # PASSO 3: Cria arquivo de configuração temporário
    # ============================================================
    
    # Cria um arquivo temporário para o config
    config_file = tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.cfg',
        delete=False,
        dir='/tmp'
    )
    config_path = config_file.name
    
    try:
        criar_arquivo_config(indices, config_path)
        if config.get('verbose', True):
            print(f"     Arquivo de configuração: {config_path}")
    except Exception as e:
        return {'success': False, 'erro': f'Erro ao criar arquivo de configuração: {e}'}
    
    # ============================================================
    # PASSO 4: Monta e executa o comando
    # ============================================================
    
    base_name = fits_path.stem
    solved_file = f"{base_name}.solved"
    wcs_file = f"{base_name}.wcs"
    match_file = f"{base_name}.match"
    
    # Comando usando --config (compatível com 0.93)
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
        '--match', match_file,
        '--new-fits', 'none',
        '--corr', 'none',
        '--rdls', 'none',
    ]
    
    if config.get('verbose', True):
        print(f"     Comando: solve-field {fits_path.name} (com {len(indices)} índices)")
    
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
        # Limpa o arquivo temporário
        try:
            os.unlink(config_path)
        except:
            pass
    
    # ============================================================
    # PASSO 5: Verifica se resolveu
    # ============================================================
    
    if not Path(solved_file).exists():
        # Verifica se houve algum erro
        if result.returncode != 0:
            return {
                'success': False, 
                'erro': f'solve-field retornou erro (código {result.returncode})',
                'saida': result.stdout + result.stderr
            }
        else:
            return {
                'success': False, 
                'erro': 'Não foi possível resolver a imagem',
                'saida': result.stdout + result.stderr
            }
    
    if config.get('verbose', True):
        print(f"     ✅ Resolvido!")
    
    # ============================================================
    # PASSO 6: Lê o arquivo WCS
    # ============================================================
    
    if not Path(wcs_file).exists():
        return {'success': False, 'erro': 'Arquivo WCS não encontrado'}
    
    try:
        with fits.open(wcs_file) as hdul:
            header = hdul[0].header
            wcs = WCS(header)
            
            crpix1 = header.get('CRPIX1', 0)
            crpix2 = header.get('CRPIX2', 0)
            
            # Extrai centro da imagem
            ra_center, dec_center = wcs.all_pix2world([[crpix1, crpix2]], 0)[0]
            
            # Extrai informações
            objeto = header.get('OBJECT', 'Desconhecido')
            
            # Calcula escala em arcsec/pixel
            cdelt1 = header.get('CDELT1', 0)
            if cdelt1 == 0:
                cdelt1 = header.get('CD1_1', 0)
            pixel_scale = abs(cdelt1) * 3600
            
    except Exception as e:
        return {'success': False, 'erro': f'Erro ao ler WCS: {e}'}
    
    # ============================================================
    # PASSO 7: Retorna o resultado
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
            'match': match_file,
            'xy': str(xy_path),
            'fits': str(fits_path),
            'axy_fits': axy_fits,
        },
        'header': dict(header),
    }


# ============================================================================
# FUNÇÃO AUXILIAR: Resolver imagem direta (sem .xy)
# ============================================================================

def resolver_imagem_direta(imagem_path, config=None):
    """
    Resolve uma imagem diretamente (sem usar .xy).
    Fallback para quando não há arquivo .xy.
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
    
    # Verifica se o solve-field existe
    solve_cmd = encontrar_solve_field()
    if not solve_cmd:
        return {'success': False, 'erro': 'solve-field não encontrado'}
    
    fits_path = Path(imagem_path)
    if not fits_path.exists():
        return {'success': False, 'erro': f'Arquivo não encontrado: {imagem_path}'}
    
    # Lista os índices
    indices = listar_indices(config['indices_dir'])
    if not indices:
        return {'success': False, 'erro': 'Nenhum arquivo de índice encontrado'}
    
    # Cria arquivo de configuração temporário
    config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.cfg', delete=False, dir='/tmp')
    config_path = config_file.name
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
        return {
            'success': False,
            'erro': 'Não foi possível resolver',
            'saida': result.stdout + result.stderr
        }
    
    # Lê WCS
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
                'arquivos': {
                    'wcs': wcs_file,
                    'solved': solved_file,
                },
                'header': dict(header),
            }
    except Exception as e:
        return {'success': False, 'erro': f'Erro ao ler WCS: {e}'}


# ============================================================================
# TESTE
# ============================================================================

if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    if len(sys.argv) > 1:
        entrada = sys.argv[1]
        
        if entrada.endswith('.fits'):
            fits_path = Path(entrada)
            xy_path = fits_path.parent / f"{fits_path.stem}.xy"
            
            if not xy_path.exists():
                xy_path = Path("saidas_teste") / "estrelas.xy"
            
            if not xy_path.exists():
                print(f"⚠️ Arquivo .xy não encontrado")
                print(f"   Procurado em: {xy_path}")
                print("   Execute primeiro: python detectar_estrelas.py teste.fits")
                sys.exit(1)
            
            entrada = str(xy_path)
        
        print(f"Testando plate_solve com: {entrada}")
        print("-" * 50)
        
        config = {
            'indices_dir': '/home/dell/Astrometria-PDI/data',
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
