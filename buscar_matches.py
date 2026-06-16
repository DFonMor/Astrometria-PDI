"""
buscar_matches.py - Módulo para busca de correspondências na base de dados

Este módulo é responsável pelo: Matching.
Conceitos da disciplina: Reconhecimento de padrões (nível alto).

Funcionalidades:
    - Carregamento dos índices do astrometry.net (arquivos .fits)
    - Extração de quads dos índices (HDU 1)
    - Construção da tabela hash (hash → lista de índices)
    - Filtragem por Declinação baseada na latitude (hemisfério sul)
    - Busca de correspondências entre quads da imagem e da base

Autor: Eduardo Fonseca Morato
Contato: morato@alunos.utfpr.edu.br
Disciplina: ELTD2 - Processamento de Imagens UTFPR
"""

import numpy as np
from astropy.io import fits
from pathlib import Path
import math
import gc
import time


def buscar_matches(padroes, header=None, config=None):
    """
    Busca correspondências entre os padrões da imagem e a base de dados.
    
    Pipeline:
        1. Extrai latitude do cabeçalho (se disponível)
        2. Calcula intervalo de Dec visível (hemisfério sul)
        3. Carrega quads dos índices filtrando por Dec
        4. Constrói tabela hash
        5. Busca correspondências
    
    Args:
        padroes (list): Lista de padrões (quads) da imagem
        header (dict, optional): Cabeçalho FITS para obter latitude
        config (dict, optional): Parâmetros de configuração.
    
    Returns:
        dict: Dicionário onde as chaves são nomes dos índices (str)
              e os valores são o número de votos (int)
    """
    
    if config is None:
        config = {
            'data_dir': 'data',
            'max_quads_to_load': 100000,
            'verbose': True,
        }
    
    if not padroes:
        if config.get('verbose', True):
            print("⚠️ Nenhum padrão para buscar")
        return {}
    
    # ============================================================
    # FILTRO POR LATITUDE (HEMISFÉRIO SUL)
    # ============================================================
    
    dec_min = -90.0
    dec_max = 90.0
    latitude = None
    
    if header:
        latitude = header.get('SITELAT', None)
        if latitude is not None:
            latitude = float(latitude)
            
            # Fórmula para hemisfério sul:
            # - Polo sul sempre visível → dec_min = -90°
            # - Polo norte limitado pela latitude → dec_max = 90° - |latitude|
            dec_min = -90.0
            dec_max = 90.0 - abs(latitude)
            
            if config.get('verbose', True):
                print(f"\n  📍 FILTRO POR LATITUDE (hemisfério sul):")
                print(f"    Latitude: {latitude:.2f}°")
                print(f"    Dec range: {dec_min:.2f}° - {dec_max:.2f}°")
        else:
            if config.get('verbose', True):
                print("  ⚠️ Latitude não encontrada no cabeçalho. Busca completa.")
    
    # ============================================================
    # CARREGAR QUADS COM FILTRO DE DEC
    # ============================================================
    
    tabela_hash = carregar_quads_com_filtro(config, dec_min, dec_max)
    
    if not tabela_hash:
        if config.get('verbose', True):
            print("⚠️ Nenhum índice carregado")
        return {}
    
    if config.get('verbose', True):
        print(f"    Tabela hash construída: {len(tabela_hash):,} chaves únicas")
    
    # ============================================================
    # BUSCAR CORRESPONDÊNCIAS
    # ============================================================
    
    votos = buscar_correspondencias(padroes, tabela_hash, config)
    
    return votos


def carregar_quads_com_filtro(config, dec_min, dec_max):
    """
    Carrega quads dos índices, filtrando por Declinação.
    
    Args:
        config (dict): Configurações
        dec_min (float): Dec mínima (graus)
        dec_max (float): Dec máxima (graus)
    
    Returns:
        dict: Tabela hash
    """
    if config.get('verbose', True):
        print("\n  Carregando índices do astrometry.net...")
    
    data_dir = Path(config['data_dir'])
    
    if not data_dir.exists():
        if config.get('verbose', True):
            print(f"    ⚠️ Pasta data/ não encontrada em {data_dir.absolute()}")
        return {}
    
    arquivos_fits = list(data_dir.glob('*.fits'))
    
    if not arquivos_fits:
        if config.get('verbose', True):
            print(f"    ⚠️ Nenhum arquivo .fits encontrado em {data_dir.absolute()}")
        return {}
    
    if config.get('verbose', True):
        print(f"    Encontrados {len(arquivos_fits)} arquivos .fits")
    
    # Filtra apenas os índices que queremos (4107-4109 e 5206-*)
    indices_selecionados = []
    for arquivo in arquivos_fits:
        nome = arquivo.name
        if nome.startswith('index-410') or nome.startswith('index-5206'):
            indices_selecionados.append(arquivo)
    
    if config.get('verbose', True):
        print(f"    Selecionados {len(indices_selecionados)} índices")
    
    if not indices_selecionados:
        if config.get('verbose', True):
            print("    ⚠️ Nenhum índice das séries 4100 ou 5206 encontrado")
        return {}
    
    # Constrói tabela hash (com filtro de Dec)
    tabela_hash = construir_tabela_hash_com_filtro(indices_selecionados, config, dec_min, dec_max)
    
    return tabela_hash


def construir_tabela_hash_com_filtro(arquivos_indice, config, dec_min, dec_max):
    """
    Constrói a tabela hash a partir dos quads, filtrando por Dec.
    """
    tabela_hash = {}
    max_quads = config.get('max_quads_to_load', 100000)
    verbose = config.get('verbose', True)
    timeout = config.get('timeout_seconds', 60)
    tempo_inicio = time.time()
    
    for arquivo in arquivos_indice:
        # Verifica timeout
        if time.time() - tempo_inicio > timeout:
            if verbose:
                print(f"    ⚠️ Tempo limite excedido ({timeout}s)")
            break
        
        if verbose:
            print(f"    Processando: {arquivo.name}")
        
        try:
            with fits.open(arquivo) as hdul:
                if len(hdul) < 2:
                    if verbose:
                        print(f"      ⚠️ Formato inesperado")
                    continue
                
                # ============================================================
                # CARREGA QUADS (HDU 1)
                # ============================================================
                quad_data = hdul[1].data
                if quad_data is None:
                    if verbose:
                        print(f"      ⚠️ HDU 1 vazio")
                    continue
                
                # Extrai quads (4 inteiros)
                if isinstance(quad_data, np.ndarray) and quad_data.dtype.names is None:
                    quads = quad_data.reshape(-1, 4)
                else:
                    quads = []
                    for q in quad_data:
                        if len(q) >= 4:
                            quads.append([q[0], q[1], q[2], q[3]])
                        else:
                            campos = list(q.dtype.names) if hasattr(q, 'dtype') else []
                            if len(campos) >= 4:
                                quads.append([q[c] for c in campos[:4]])
                    quads = np.array(quads)
                
                n_quads = len(quads)
                if verbose:
                    print(f"      Quads encontrados: {n_quads:,}")
                
                # Se não há quads, pula
                if n_quads == 0:
                    if verbose:
                        print(f"      ⚠️ Sem quads, pulando")
                    continue
                
                # ============================================================
                # CARREGA ESTRELAS (HDU 11) PARA FILTRAR POR DEC
                # ============================================================
                star_data = None
                
                # Tenta HDU 11 primeiro
                if len(hdul) > 11 and hdul[11].data is not None:
                    star_data = hdul[11].data
                    if verbose:
                        print(f"      HDU 11 encontrado: {len(star_data)} registros")
                else:
                    if verbose:
                        print(f"      ⚠️ HDU 11 não encontrado ou vazio")
                    continue
                
                # Se não tiver dados de estrelas, não podemos filtrar
                if star_data is None or len(star_data) == 0:
                    if verbose:
                        print(f"      ⚠️ Sem dados de estrelas para filtrar Dec")
                    continue
                
                # ============================================================
                # EXTRAI DEC DAS ESTRELAS
                # ============================================================
                estrelas_dec = []
                
                # Caso 1: Tabela com colunas nomeadas
                if hasattr(star_data, 'dtype') and star_data.dtype.names is not None:
                    colunas = list(star_data.dtype.names)
                    if verbose:
                        print(f"      Colunas do HDU 11: {colunas}")
                    
                    col_dec = None
                    for nome in colunas:
                        nome_lower = nome.lower()
                        if nome_lower in ['dec', 'dej2000', 'dec_deg']:
                            col_dec = nome
                            break
                    
                    if col_dec is None:
                        if verbose:
                            print(f"      ⚠️ Coluna Dec não encontrada em {colunas}")
                        
                        # Tenta extrair Dec pela posição (formato 12A)
                        if verbose:
                            print(f"      Tentando extrair Dec por posição (formato 12A)...")
                        
                        # Para o formato 12A, a Dec está nas posições 6-12
                        for star in star_data:
                            try:
                                # Converte para string se for bytes
                                if isinstance(star[0], bytes):
                                    star_str = star[0].decode('utf-8').strip()
                                else:
                                    star_str = str(star[0]).strip()
                                
                                # Se tiver pelo menos 12 caracteres, extrai Dec
                                if len(star_str) >= 12:
                                    # Dec está nas posições 6-12
                                    dec_str = star_str[6:12]
                                    dec = float(dec_str)
                                    if -90 <= dec <= 90:
                                        estrelas_dec.append(dec)
                            except (ValueError, TypeError, IndexError):
                                continue
                    else:
                        # Coluna Dec encontrada
                        for star in star_data:
                            dec = star[col_dec]
                            if not np.isnan(dec) and -90 <= dec <= 90:
                                estrelas_dec.append(float(dec))
                
                # Caso 2: Formato bruto (12A) - sem colunas nomeadas
                else:
                    if verbose:
                        print(f"      Tentando extrair Dec do formato bruto...")
                    
                    for star in star_data:
                        try:
                            # Converte para string
                            if isinstance(star, bytes):
                                star_str = star.decode('utf-8').strip()
                            elif isinstance(star, np.ndarray):
                                star_str = str(star[0]).strip()
                            else:
                                star_str = str(star).strip()
                            
                            # Extrai Dec da posição 6-12
                            if len(star_str) >= 12:
                                dec_str = star_str[6:12]
                                dec = float(dec_str)
                                if -90 <= dec <= 90:
                                    estrelas_dec.append(dec)
                        except (ValueError, TypeError, IndexError):
                            continue
                
                # Se não conseguiu extrair Dec, pula este índice
                if not estrelas_dec:
                    if verbose:
                        print(f"      ⚠️ Nenhuma Dec válida extraída")
                    
                    # Para debug: mostra os primeiros registros
                    if verbose and len(star_data) > 0:
                        print(f"      Primeiro registro (bruto): {star_data[0]}")
                    continue
                
                # Filtra estrelas por Dec
                dec_min_local = min(estrelas_dec)
                dec_max_local = max(estrelas_dec)
                
                if verbose:
                    print(f"      Dec extraídas: {len(estrelas_dec):,} estrelas")
                    print(f"      Faixa do índice: {dec_min_local:.2f}° - {dec_max_local:.2f}°")
                
                # Verifica se o índice cobre a faixa de Dec desejada
                if dec_max_local < dec_min or dec_min_local > dec_max:
                    if verbose:
                        print(f"      ⚠️ Índice fora da faixa de Dec ({dec_min:.1f}° - {dec_max:.1f}°)")
                    continue
                
                # Limita o número de quads para evitar memória
                if n_quads > max_quads:
                    if verbose:
                        print(f"      ⚠️ Limitando a {max_quads:,} quads")
                    quads = quads[:max_quads]
                    n_quads = len(quads)
                
                nome_indice = arquivo.name.replace('.fits', '')
                
                # Adiciona cada quad à tabela hash
                for i, quad in enumerate(quads):
                    hash_quad = tuple(quad.tolist()) if isinstance(quad, np.ndarray) else tuple(quad)
                    
                    if hash_quad not in tabela_hash:
                        tabela_hash[hash_quad] = []
                    tabela_hash[hash_quad].append(nome_indice)
                    
                    # Libera memória a cada 10.000 quads
                    if i % 10000 == 0:
                        gc.collect()
                
                if verbose:
                    print(f"      Adicionados {n_quads:,} quads à tabela")
                
        except Exception as e:
            if verbose:
                print(f"      ❌ Erro ao processar {arquivo.name}: {e}")
                import traceback
                traceback.print_exc()
            continue
    
    return tabela_hash


def buscar_correspondencias(padroes, tabela_hash, config):
    """
    Busca correspondências entre os quads da imagem e a tabela hash.
    
    Args:
        padroes (list): Lista de quads da imagem
        tabela_hash (dict): Tabela hash (hash → lista de índices)
        config (dict): Configurações
    
    Returns:
        dict: Dicionário índice → número de votos
    """
    votos = {}
    verbose = config.get('verbose', True)
    total_quads = len(padroes)
    
    if verbose:
        print(f"\n  Buscando {total_quads:,} quads na tabela...")
    
    quads_encontrados = 0
    
    for i, padrao in enumerate(padroes):
        hash_quad = padrao['hash']
        
        if hash_quad in tabela_hash:
            indices = tabela_hash[hash_quad]
            quads_encontrados += 1
            
            for nome_indice in indices:
                votos[nome_indice] = votos.get(nome_indice, 0) + 1
        
        # Mostra progresso a cada 1000 quads
        if verbose and (i + 1) % 1000 == 0:
            print(f"    Buscados {i+1:,}/{total_quads:,} quads...", end='\r')
    
    if verbose:
        print(f"    Buscados {total_quads:,}/{total_quads:,} quads")
        print(f"    Quads encontrados: {quads_encontrados:,} ({quads_encontrados/total_quads*100:.1f}%)")
    
    return votos


def exibir_info_matching(votos, total_padroes):
    """
    Exibe informações sobre o matching (para debug).
    
    Args:
        votos (dict): Dicionário índice → número de votos
        total_padroes (int): Número total de padrões analisados
    """
    if not votos:
        print("  Nenhuma correspondência encontrada")
        return
    
    # Ordena por número de votos (decrescente)
    votos_ordenados = sorted(votos.items(), key=lambda x: x[1], reverse=True)
    
    total_votos = sum(votos.values())
    
    print(f"\n  Correspondências encontradas: {len(votos_ordenados)} índices")
    print(f"  Total de quads analisados: {total_padroes:,}")
    print(f"  Total de votos: {total_votos:,}")
    
    # Mostra os 10 melhores
    print("\n  Top 10 candidatos:")
    for i, (indice, n_votos) in enumerate(votos_ordenados[:10], 1):
        porcentagem = (n_votos / total_padroes) * 100 if total_padroes > 0 else 0
        print(f"    {i:2d}. {indice}: {n_votos:,} votos ({porcentagem:.1f}%)")


# ============================================================================
# TESTE (executado apenas se rodar este arquivo diretamente)
# ============================================================================

if __name__ == "__main__":
    import sys
    from ler_fits import carregar_imagem
    from melhorar_imagem import pre_processar
    from detectar_estrelas import detectar_estrelas
    from extrair_padroes import extrair_padroes
    
    if len(sys.argv) > 1:
        caminho_teste = sys.argv[1]
        print(f"Testando busca de matches: {caminho_teste}")
        print("-" * 50)
        
        try:
            # Pipeline completo
            img_raw, header = carregar_imagem(caminho_teste)
            img_proc = pre_processar(img_raw)
            
            # ============================================================
            # DETECÇÃO DE ESTRELAS (COM CONFIG)
            # ============================================================
            config_deteccao = {
                'num_stars': 40,
                'otsu_sensitivity': 1.0,
                'morph_open_size': 3,
                'morph_close_size': 3,
                'min_star_area': 3,
                'max_star_area': 50,
                'min_flux': 0.01,
            }
            estrelas = detectar_estrelas(img_proc, config_deteccao)
            print(f"Estrelas detectadas: {len(estrelas)}")
            
            # ============================================================
            # EXTRAÇÃO DE QUADS (COM TODOS OS PARÂMETROS)
            # ============================================================
            config_extrair = {
                'num_stars': 40,
                'max_stars_absolute': 50,      # ← ADICIONADO
                'max_quads': 100000,
                'sample_quads': False,
                'min_distance': 10.0,
                'max_distance': 500.0,
            }
            padroes = extrair_padroes(estrelas, config_extrair)
            print(f"Quads gerados: {len(padroes):,}")
            
            # ============================================================
            # BUSCA DE MATCHES
            # ============================================================
            config_buscar = {
                'data_dir': 'data',
                'max_quads_to_load': 100000,
                'verbose': True,
                'timeout_seconds': 60,
            }
            votos = buscar_matches(padroes, header, config_buscar)
            
            exibir_info_matching(votos, len(padroes))
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("Uso: python buscar_matches.py caminho/para/imagem.fits")