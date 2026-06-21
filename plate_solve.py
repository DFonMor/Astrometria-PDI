"""
plate_solve.py - Módulo para resolução astrométrica usando solve-field

Este módulo utiliza as estrelas detectadas (arquivo .xy) e chama o solve-field
para identificar o campo estelar da imagem.

Conceitos da disciplina: Reconhecimento de padrões (nível alto).
"""

import subprocess
import shutil
import os
import sys
import platform
from pathlib import Path
from astropy.io import fits
from astropy.wcs import WCS


def converter_caminho_wsl(caminho):
    """
    Converte um caminho Windows para formato WSL.
    Exemplo: D:\\pasta\\arquivo.xy -> /mnt/d/pasta/arquivo.xy
    """
    if not caminho:
        return caminho
    
    # Converte para string e substitui barras invertidas
    caminho = str(caminho).replace('\\', '/')
    
    # Converte D:/pasta -> /mnt/d/pasta
    if len(caminho) > 1 and caminho[1] == ':':
        drive = caminho[0].lower()
        caminho = f"/mnt/{drive}{caminho[2:]}"
    
    return caminho


def encontrar_solve_field():
    """
    Encontra o executável solve-field no sistema.
    No WSL, retorna 'wsl' para executar via WSL interop.
    
    Returns:
        str: Comando para executar solve-field ou None se não encontrado
    """
    # Verifica se está no WSL
    is_wsl = 'WSLENV' in os.environ or 'WSL_DISTRO_NAME' in os.environ
    
    if is_wsl:
        # Estamos no WSL, podemos executar diretamente
        if shutil.which('solve-field'):
            return 'solve-field'
        else:
            return None
    
    # Verifica se está no Windows (usando WSL interop)
    if platform.system() == 'Windows':
        # Tenta encontrar o wsl.exe
        wsl_path = shutil.which('wsl')
        if wsl_path:
            # Testa se solve-field existe no WSL
            try:
                result = subprocess.run(
                    ['wsl', 'which', 'solve-field'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0 and result.stdout.strip():
                    return 'wsl'  # Vai usar 'wsl solve-field ...'
            except:
                pass
    
    # Último recurso: tenta diretamente (pode falhar)
    if shutil.which('solve-field'):
        return 'solve-field'
    
    return None


def executar_solve_field(args, config=None):
    """
    Executa o solve-field, adaptando para o ambiente (WSL ou Windows).
    
    Args:
        args (list): Argumentos para o solve-field
        config (dict): Configuração
    
    Returns:
        subprocess.CompletedProcess: Resultado da execução
    """
    solve_cmd = encontrar_solve_field()
    
    if not solve_cmd:
        raise FileNotFoundError("solve-field não encontrado")
    
    # Se estiver no Windows e o comando for 'wsl', converte caminhos
    if platform.system() == 'Windows' and solve_cmd == 'wsl':
        # Converte TODOS os argumentos que parecem caminhos
        args_convertidos = []
        for arg in args:
            if isinstance(arg, str):
                # Se parece um caminho (tem /, \ ou :) converte
                if '/' in arg or '\\' in arg or ':' in arg:
                    arg = converter_caminho_wsl(arg)
            args_convertidos.append(arg)
        
        # Monta o comando completo
        cmd = ['wsl', 'solve-field'] + args_convertidos
    else:
        # Execução direta (Linux/Mac ou WSL)
        cmd = ['solve-field'] + args
    
    # Executa
    timeout = config.get('timeout', 120) + 10 if config else 130
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout
    )


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
    
    solve_cmd = encontrar_solve_field()
    if not solve_cmd:
        return {'success': False, 'erro': 'solve-field não encontrado'}
    
    args = [
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
        result = executar_solve_field(args, config)
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


def resolver_imagem(arquivo_xy, config=None):
    """
    Resolve uma imagem usando o arquivo .xy com as estrelas detectadas.
    
    Args:
        arquivo_xy (str): Caminho para o arquivo .xy com as estrelas
        config (dict, optional): Parâmetros de configuração.
    
    Returns:
        dict: Resultado da resolução
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
    
    # Verifica se o solve-field existe
    solve_cmd = encontrar_solve_field()
    if not solve_cmd:
        return {
            'success': False, 
            'erro': 'solve-field não encontrado. Instale o astrometry.net.\n'
                   'No WSL: sudo apt install astrometry.net'
        }
    
    # Verifica se o arquivo .xy existe
    xy_path = Path(arquivo_xy)
    if not xy_path.exists():
        return {'success': False, 'erro': f'Arquivo .xy não encontrado: {arquivo_xy}'}
    
    # Procura o arquivo .fits correspondente
    fits_path = None
    # Tenta na mesma pasta com mesmo nome
    for ext in ['.fits', '.fit', '.FITS']:
        possivel_fits = xy_path.parent / f"{xy_path.stem}{ext}"
        if possivel_fits.exists():
            fits_path = possivel_fits
            break
    
    # Se não encontrou, procura na pasta pai
    if not fits_path:
        possivel_fits = Path("teste.fits")
        if possivel_fits.exists():
            fits_path = possivel_fits
    
    # Se ainda não encontrou, procura qualquer .fits na pasta atual
    if not fits_path:
        fits_files = list(Path(".").glob("*.fits"))
        if fits_files:
            fits_path = fits_files[0]
    
    if not fits_path:
        return {'success': False, 'erro': 'Arquivo .fits correspondente não encontrado'}
    
    # IMPORTANTE: Copia o .xy para a mesma pasta da imagem com o mesmo nome base
    # O solve-field procura automaticamente por um arquivo .xy com o mesmo nome
    xy_destino = fits_path.parent / f"{fits_path.stem}.xy"
    
    # Se o .xy está em outra pasta, copia para a pasta da imagem
    if xy_path != xy_destino:
        if config.get('verbose', True):
            print(f"     Copiando {xy_path} para {xy_destino}")
        shutil.copy2(xy_path, xy_destino)
    
    if config.get('verbose', True):
        print(f"  🔭 Resolvendo imagem: {fits_path.name}")
        print(f"     Usando lista de estrelas: {xy_destino.name}")
        print(f"     Índices: {config['indices_dir']}")
        print(f"     Escala: {config['scale_low']}° - {config['scale_high']}°")
        print(f"     Dimensões: {config['width']} x {config['height']} px")
        print(f"     solve-field via: {solve_cmd}")
    
    # ============================================================
    # PASSO 1: Executa o solve-field APENAS com a imagem
    # ============================================================
    
    args = [
        str(fits_path),   # Apenas a imagem!
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
    
    if config.get('verbose', True):
        print(f"     Comando: {solve_cmd} {' '.join(args)}")
    
    try:
        result = executar_solve_field(args, config)
    except subprocess.TimeoutExpired:
        return {'success': False, 'erro': f'Tempo limite excedido ({config["timeout"]}s)'}
    except FileNotFoundError:
        return {'success': False, 'erro': f'solve-field não encontrado'}
    except Exception as e:
        return {'success': False, 'erro': f'Erro ao executar solve-field: {e}'}
    
    # Verifica se houve erro na execução
    if result.returncode != 0:
        return {
            'success': False, 
            'erro': f'solve-field retornou erro (código {result.returncode})',
            'saida': result.stdout + result.stderr
        }
    
    # ============================================================
    # PASSO 2: Verifica se resolveu
    # ============================================================
    
    solved_file = f"{fits_path.stem}.solved"
    wcs_file = f"{fits_path.stem}.wcs"
    
    if not Path(solved_file).exists():
        if config.get('verbose', True):
            print("     ⚠️ Não resolveu com .xy, tentando fallback com imagem...")
        return resolver_imagem_direta(fits_path, config)
    
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
            'xy': str(xy_destino),
            'fits': str(fits_path),
        },
        'header': dict(header),
    }


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
    
    solve_cmd = encontrar_solve_field()
    if not solve_cmd:
        return {'success': False, 'erro': 'solve-field não encontrado'}
    
    if saida is None:
        base = Path(imagem_path).stem
        saida = f"{base}_quads.pnm"
    
    args = [
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
        result = executar_solve_field(args, config)
        
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
        entrada = sys.argv[1]
        
        # Se for um .fits, procura o .xy correspondente
        if entrada.endswith('.fits'):
            # Tenta encontrar o .xy
            fits_path = Path(entrada)
            xy_path = fits_path.parent / f"{fits_path.stem}.xy"
            
            # Se não existir, tenta na pasta saidas_teste
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