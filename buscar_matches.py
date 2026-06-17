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

import sys
import os
import json
import struct
import numpy as np
from astropy.io import fits
from pathlib import Path
import gc
import time
from tqdm import tqdm


# ============================================================================
# FUNÇÕES DE EXTRAÇÃO
# ============================================================================

def extrair_quads(quad_data):
    """
    Extrai quads de dados FITS preservando todos os bytes.
    
    Args:
        quad_data: Dados da tabela FITS (HDU 1)
    
    Returns:
        bytes: Todos os quads concatenados (cada quad com 16 bytes)
    """
    # A coluna 'quads' tem dados binários de 16 bytes cada
    return quad_data['quads'].view('S16').tobytes()


def hash_para_indices(hash_bytes):
    """
    Converte um hash de 16 bytes para 4 índices inteiros (little-endian).
    """
    if len(hash_bytes) != 16:
        raise ValueError(f"Hash deve ter 16 bytes, tem {len(hash_bytes)}")
    return struct.unpack('<4I', hash_bytes)


def indices_para_hash(indices):
    """
    Converte 4 índices inteiros para um hash de 16 bytes.
    """
    if len(indices) != 4:
        raise ValueError(f"Deve ter 4 índices, tem {len(indices)}")
    return struct.pack('<4I', *indices)


def extrair_decs(star_data):
    """
    Extrai Declinações do HDU 11.
    
    Args:
        star_data: Dados do HDU 11
    
    Returns:
        np.ndarray: Array de declinações
    """
    decs = []
    
    # Verifica se star_data é None ou vazio
    if star_data is None or len(star_data) == 0:
        return np.array(decs)
    
    # Tenta diferentes formas de acessar os dados
    try:
        # Caso 1: star_data é um array estruturado com colunas
        if hasattr(star_data, 'dtype') and star_data.dtype.names is not None:
            colunas = star_data.dtype.names
            print(f"      Colunas do HDU 11: {colunas}")
            
            # Procura coluna de Dec
            col_dec = None
            for nome in colunas:
                if 'dec' in nome.lower():
                    col_dec = nome
                    break
            
            if col_dec is None:
                # Se não encontrou Dec, tenta a primeira coluna que parece ser numérica
                for nome in colunas:
                    if 'ra' not in nome.lower() and 'mag' not in nome.lower():
                        col_dec = nome
                        break
            
            if col_dec is not None:
                for record in star_data:
                    try:
                        dec = float(record[col_dec])
                        if -90 <= dec <= 90:
                            decs.append(dec)
                    except:
                        continue
            else:
                print(f"      ⚠️ Coluna Dec não encontrada")
                return np.array(decs)
        
        # Caso 2: star_data é uma lista de registros
        elif isinstance(star_data, (list, tuple)):
            for record in star_data:
                try:
                    if len(record) >= 3:
                        # Tenta extrair Dec da terceira coluna
                        dec = float(record[2])
                        if -90 <= dec <= 90:
                            decs.append(dec)
                    elif len(record) >= 1:
                        # Tenta extrair Dec da primeira coluna
                        dec = float(record[0])
                        if -90 <= dec <= 90:
                            decs.append(dec)
                except:
                    continue
        
        # Caso 3: star_data é um array numpy
        elif isinstance(star_data, np.ndarray):
            # Tenta acessar como array estruturado com colunas
            if star_data.dtype.names is not None:
                colunas = star_data.dtype.names
                col_dec = None
                for nome in colunas:
                    if 'dec' in nome.lower():
                        col_dec = nome
                        break
                
                if col_dec is not None:
                    for record in star_data:
                        try:
                            dec = float(record[col_dec])
                            if -90 <= dec <= 90:
                                decs.append(dec)
                        except:
                            continue
                else:
                    # Usa a primeira coluna numérica
                    for col in colunas:
                        try:
                            for record in star_data:
                                dec = float(record[col])
                                if -90 <= dec <= 90:
                                    decs.append(dec)
                            break
                        except:
                            continue
            else:
                # Array simples
                for val in star_data:
                    try:
                        dec = float(val)
                        if -90 <= dec <= 90:
                            decs.append(dec)
                    except:
                        continue
        
        # Caso 4: Tentar acessar cada registro como bytes
        else:
            for record in star_data:
                try:
                    if isinstance(record, bytes):
                        # Tenta decodificar como string
                        data_str = record.decode('utf-8').strip()
                        # Tenta extrair números
                        parts = data_str.split()
                        if len(parts) >= 3:
                            dec = float(parts[2])
                            if -90 <= dec <= 90:
                                decs.append(dec)
                    elif hasattr(record, 'decode'):
                        data_str = record.decode('utf-8').strip()
                        parts = data_str.split()
                        if len(parts) >= 3:
                            dec = float(parts[2])
                            if -90 <= dec <= 90:
                                decs.append(dec)
                except:
                    continue
    
    except Exception as e:
        print(f"      ⚠️ Erro ao extrair Decs: {e}")
        return np.array(decs)
    
    return np.array(decs)


def extrair_decs_alternativo(star_data):
    """
    Extrai Declinações do HDU 11 usando uma abordagem mais robusta.
    """
    decs = []
    
    if star_data is None or len(star_data) == 0:
        return np.array(decs)
    
    # Tenta acessar como array de bytes
    try:
        for record in star_data:
            if isinstance(record, (bytes, bytearray)):
                try:
                    # Tenta decodificar como string
                    data_str = record.decode('utf-8').strip()
                    # Busca por padrão de número com sinal
                    import re
                    numeros = re.findall(r'[-+]?\d*\.?\d+', data_str)
                    if len(numeros) >= 3:
                        dec = float(numeros[2])
                        if -90 <= dec <= 90:
                            decs.append(dec)
                except:
                    continue
            elif isinstance(record, (list, tuple, np.ndarray)) and len(record) >= 3:
                try:
                    dec = float(record[2])
                    if -90 <= dec <= 90:
                        decs.append(dec)
                except:
                    continue
    except Exception as e:
        pass
    
    return np.array(decs)


# ============================================================================
# FUNÇÕES PRINCIPAIS
# ============================================================================

def buscar_matches(padroes, header=None, config=None):
    """Busca correspondências entre os padrões da imagem e a base de dados."""
    
    if config is None:
        config = {
            'data_dir': 'data',
            'max_quads_to_load': 50000,
            'verbose': True,
            'timeout_seconds': 120,
            'votos_minimos': 3,
        }
    
    if not padroes:
        if config.get('verbose', True):
            print("⚠️ Nenhum padrão para buscar")
        return {}
    
    # FILTRO POR LATITUDE
    dec_min = -90.0
    dec_max = 90.0
    
    if header:
        latitude = header.get('SITELAT', None)
        if latitude is not None:
            latitude = float(latitude)
            dec_min = -90.0
            dec_max = 90.0 - abs(latitude)
            
            if config.get('verbose', True):
                print(f"\n  📍 FILTRO POR LATITUDE (hemisfério sul):")
                print(f"    Latitude: {latitude:.2f}°")
                print(f"    Dec range: {dec_min:.2f}° - {dec_max:.2f}°")
    
    # CARREGAR QUADS
    tabela_hash = carregar_quads_com_filtro(config, dec_min, dec_max)
    
    if not tabela_hash:
        if config.get('verbose', True):
            print("⚠️ Nenhum índice carregado")
        return {}
    
    if config.get('verbose', True):
        print(f"    Tabela hash construída: {len(tabela_hash):,} chaves únicas")
    
    # BUSCAR CORRESPONDÊNCIAS
    votos = buscar_correspondencias(padroes, tabela_hash, config)
    
    return votos


def carregar_quads_com_filtro(config, dec_min, dec_max):
    """Carrega quads dos índices, filtrando por Declinação."""
    
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
    
    # Filtra índices das séries 4100 e 5206
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
    
    # Constrói tabela hash
    tabela_hash = construir_tabela_hash(indices_selecionados, config, dec_min, dec_max)
    
    return tabela_hash


def construir_tabela_hash(arquivos_indice, config, dec_min, dec_max):
    """Constrói a tabela hash a partir dos quads dos índices."""
    
    tabela_hash = {}
    max_quads = config.get('max_quads_to_load', None)
    verbose = config.get('verbose', True)
    timeout = config.get('timeout_seconds', 600)
    tempo_inicio = time.time()
    
    for arquivo in arquivos_indice:
        # Verifica timeout
        if time.time() - tempo_inicio > timeout:
            if verbose:
                print(f"\n    ⚠️ Tempo limite excedido ({timeout}s)")
            break
        
        nome_arquivo = arquivo.name
        
        try:
            with fits.open(arquivo, ignore_missing_end=True) as hdul:
                # HDU 1: Quads
                if len(hdul) < 2:
                    continue
                
                n_total = len(hdul[1].data)

                # Se max_quads for None, processa tudo
                if max_quads is None:
                    n_quads = n_total
                else:
                    n_quads = min(n_total, max_quads)
                
                # ============================================================
                # BARRA DE PROGRESSO PARA ESTE ARQUIVO
                # ============================================================
                print(f"\n    📄 {nome_arquivo}: {n_total:,} quads")
                
                if n_total > 500000:
                    print(f"      ⚠️ Arquivo grande! Processando {n_quads:,} quads...")

                nome_arquivo = arquivo.name.replace('.fits', '')
                
                # Processa em lotes
                batch_size = 10000
                quads_processados = 0
                
                pbar = tqdm(total=n_quads, desc=f"      Lendo {nome_arquivo[:20]}...", unit="quad")
                
                while quads_processados < n_quads:
                    fim_lote = min(quads_processados + batch_size, n_quads)
                    quad_data = hdul[1].data[quads_processados:fim_lote]
                    
                    try:
                        quads_bytes = extrair_quads(quad_data)
                        n_lote = len(quads_bytes) // 16
                    except Exception as e:
                        break
                    
                    # Adiciona à tabela hash
                    for i in range(n_lote):
                        offset = i * 16
                        hash_bytes = quads_bytes[offset:offset+16]
                        
                        if hash_bytes not in tabela_hash:
                            tabela_hash[hash_bytes] = []
                        tabela_hash[hash_bytes].append(nome_arquivo)
                        
                        if (quads_processados + i) % 10000 == 0:
                            gc.collect()
                    
                    quads_processados += n_lote
                    pbar.update(n_lote)
                
                pbar.close()
                
        except Exception as e:
            if verbose:
                print(f"      ⚠️ Erro ao processar {arquivo.name}: {e}")
            continue
    
    return tabela_hash


def buscar_correspondencias(padroes, tabela_hash, config):
    """Busca correspondências entre os quads da imagem e a tabela hash."""
    
    votos = {}
    verbose = config.get('verbose', True)
    total_quads = len(padroes)
    
    if verbose:
        print(f"\n  Buscando {total_quads:,} quads na tabela...")
    
    quads_encontrados = 0
    votos_minimos = config.get('votos_minimos', 3)
    
    for padrao in tqdm(padroes, desc="  Buscando quads", unit="quad"):
        hash_tuple = padrao['hash']
        hash_bytes = indices_para_hash(hash_tuple)
        
        if hash_bytes in tabela_hash:
            quads_encontrados += 1
            for nome_indice in tabela_hash[hash_bytes]:
                votos[nome_indice] = votos.get(nome_indice, 0) + 1
    
    if verbose:
        print(f"\n    Quads encontrados: {quads_encontrados:,} ({quads_encontrados/total_quads*100:.1f}%)")
    
    votos_filtrados = {k: v for k, v in votos.items() if v >= votos_minimos}
    
    return votos_filtrados


def exibir_info_matching(votos, total_padroes):
    """Exibe informações sobre o matching."""
    
    if not votos:
        print("  Nenhuma correspondência encontrada")
        return
    
    votos_ordenados = sorted(votos.items(), key=lambda x: x[1], reverse=True)
    total_votos = sum(votos.values())
    
    print(f"\n  Correspondências: {len(votos_ordenados)} índices")
    print(f"  Total de quads analisados: {total_padroes:,}")
    print(f"  Total de votos: {total_votos:,}")
    
    print("\n  Top 10 candidatos:")
    for i, (indice, n_votos) in enumerate(votos_ordenados[:10], 1):
        porcentagem = (n_votos / total_padroes) * 100 if total_padroes > 0 else 0
        print(f"    {i:2d}. {indice}: {n_votos:,} votos ({porcentagem:.1f}%)")


# ============================================================================
# TESTE
# ============================================================================

if __name__ == "__main__":
    import sys
    import json
    from pathlib import Path
    from ler_fits import carregar_imagem
    
    if len(sys.argv) > 1:
        caminho_teste = sys.argv[1]
        print(f"Testando busca de matches: {caminho_teste}")
        print("-" * 50)
        
        try:
            pasta_saida = Path("saidas_teste")
            arquivo_quads = pasta_saida / "quads_gerados.json"
            
            if not arquivo_quads.exists():
                print(f"❌ Arquivo {arquivo_quads} não encontrado!")
                print("   Execute primeiro: python extrair_padroes.py teste.fits")
                sys.exit(1)
            
            with open(arquivo_quads, 'r') as f:
                quads_data = json.load(f)
            
            padroes = []
            for q in quads_data:
                padroes.append({
                    'hash': tuple(q['hash']),
                    'vertices': q['vertices'],
                    'area': q['area'],
                    'distancias': q['distancias']
                })
            
            print(f"Quads carregados: {len(padroes):,}")
            
            img_raw, header = carregar_imagem(caminho_teste)
            
            config_buscar = {
                'data_dir': 'data',
                'max_quads_to_load': None,
                'verbose': True,
                'timeout_seconds': 600,
                'votos_minimos': 3,
            }
            
            votos = buscar_matches(padroes, header, config_buscar)
            exibir_info_matching(votos, len(padroes))
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("Uso: python buscar_matches.py caminho/para/imagem.fits")