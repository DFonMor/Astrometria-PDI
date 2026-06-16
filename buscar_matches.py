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
import gc
import time


# ============================================================================
# FUNÇÕES DE EXTRAÇÃO (SIMPLIFICADAS)
# ============================================================================

def extrair_quads(quad_data):
    """
    Extrai quads do HDU 1.
    
    Formato conhecido: S16 (16 bytes) = 4 inteiros de 32 bits little-endian
    """
    # Concatena todos os bytes
    bytes_total = b''.join(record[0] for record in quad_data)
    
    # Decodifica todos de uma vez
    n_quads = len(quad_data)
    quads = np.frombuffer(bytes_total, dtype=np.uint32).reshape(n_quads, 4)
    
    return quads


def extrair_decs(star_data):
    """
    Extrai Declinações do HDU 11.
    
    Formato conhecido: 12A (12 bytes) = RA + DEC + MAG
    """
    decs = []
    
    for record in star_data:
        data = record[0]
        if len(data) >= 12:
            # DEC está nos bytes 6-11
            dec_bytes = data[6:12]
            try:
                dec = float(dec_bytes.decode('utf-8').strip())
                if -90 <= dec <= 90:
                    decs.append(dec)
            except:
                continue
    
    return np.array(decs)


# ============================================================================
# FUNÇÕES PRINCIPAIS
# ============================================================================

def buscar_matches(padroes, header=None, config=None):
    """Busca correspondências entre os padrões da imagem e a base de dados."""
    
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
    """Carrega quads dos índices, filtrando por Declinação."""
    
    if config.get('verbose', True):
        print("\n  Carregando índices do astrometry.net...")
    
    data_dir = Path(config['data_dir'])
    
    if not data_dir.exists():
        if config.get('verbose', True):
            print(f"    ⚠️ Pasta data/ não encontrada")
        return {}
    
    arquivos_fits = list(data_dir.glob('*.fits'))
    
    if not arquivos_fits:
        if config.get('verbose', True):
            print(f"    ⚠️ Nenhum arquivo .fits encontrado")
        return {}
    
    # Filtra índices
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
    """Constrói a tabela hash a partir dos quads."""
    
    tabela_hash = {}
    max_quads = config.get('max_quads_to_load', 100000)
    verbose = config.get('verbose', True)
    timeout = config.get('timeout_seconds', 60)
    tempo_inicio = time.time()
    
    for arquivo in arquivos_indice:
        if time.time() - tempo_inicio > timeout:
            if verbose:
                print(f"    ⚠️ Tempo limite excedido ({timeout}s)")
            break
        
        if verbose:
            print(f"    Processando: {arquivo.name}")
        
        try:
            with fits.open(arquivo) as hdul:
                # ============================================================
                # HDU 1: Quads
                # ============================================================
                quad_data = hdul[1].data
                if quad_data is None or len(quad_data) == 0:
                    if verbose:
                        print(f"      ⚠️ HDU 1 vazio")
                    continue
                
                quads = extrair_quads(quad_data)
                n_quads = len(quads)
                
                if verbose:
                    print(f"      Quads: {n_quads:,}")
                
                # ============================================================
                # HDU 11: Estrelas (para filtrar por Dec)
                # ============================================================
                star_data = hdul[11].data if len(hdul) > 11 else None
                
                if star_data is None or len(star_data) == 0:
                    if verbose:
                        print(f"      ⚠️ HDU 11 vazio, pulando")
                    continue
                
                # Extrai Decs
                decs = extrair_decs(star_data)
                
                if len(decs) == 0:
                    if verbose:
                        print(f"      ⚠️ Nenhuma Dec válida, pulando")
                    continue
                
                dec_min_local = float(np.min(decs))
                dec_max_local = float(np.max(decs))
                
                if verbose:
                    print(f"      Dec range: {dec_min_local:.1f}° - {dec_max_local:.1f}°")
                
                # Verifica se o índice cobre a faixa de Dec desejada
                if dec_max_local < dec_min or dec_min_local > dec_max:
                    if verbose:
                        print(f"      ⚠️ Fora da faixa ({dec_min:.1f}° - {dec_max:.1f}°)")
                    continue
                
                # Limita número de quads
                if n_quads > max_quads:
                    if verbose:
                        print(f"      ⚠️ Limitando a {max_quads:,} quads")
                    quads = quads[:max_quads]
                    n_quads = len(quads)
                
                nome_indice = arquivo.name.replace('.fits', '')
                
                # Adiciona à tabela hash
                for i, quad in enumerate(quads):
                    hash_quad = tuple(quad.tolist())
                    
                    if hash_quad not in tabela_hash:
                        tabela_hash[hash_quad] = []
                    tabela_hash[hash_quad].append(nome_indice)
                    
                    if i % 10000 == 0:
                        gc.collect()
                
                if verbose:
                    print(f"      Adicionados {n_quads:,} quads")
                
        except Exception as e:
            if verbose:
                print(f"      ❌ Erro: {e}")
            continue
    
    return tabela_hash


def buscar_correspondencias(padroes, tabela_hash, config):
    """Busca correspondências entre os quads da imagem e a tabela hash."""
    
    votos = {}
    verbose = config.get('verbose', True)
    total_quads = len(padroes)
    
    if verbose:
        print(f"\n  Buscando {total_quads:,} quads...")
    
    quads_encontrados = 0
    
    for i, padrao in enumerate(padroes):
        hash_quad = padrao['hash']
        
        if hash_quad in tabela_hash:
            quads_encontrados += 1
            for nome_indice in tabela_hash[hash_quad]:
                votos[nome_indice] = votos.get(nome_indice, 0) + 1
        
        if verbose and (i + 1) % 1000 == 0:
            print(f"    {i+1:,}/{total_quads:,}...", end='\r')
    
    if verbose:
        print(f"    Quads encontrados: {quads_encontrados:,} ({quads_encontrados/total_quads*100:.1f}%)")
    
    return votos


def exibir_info_matching(votos, total_padroes):
    """Exibe informações sobre o matching."""
    
    if not votos:
        print("  Nenhuma correspondência encontrada")
        return
    
    votos_ordenados = sorted(votos.items(), key=lambda x: x[1], reverse=True)
    
    print(f"\n  Correspondências: {len(votos_ordenados)} índices")
    print(f"  Total de votos: {sum(votos.values()):,}")
    
    print("\n  Top 10 candidatos:")
    for i, (indice, n_votos) in enumerate(votos_ordenados[:10], 1):
        print(f"    {i:2d}. {indice}: {n_votos:,} votos")