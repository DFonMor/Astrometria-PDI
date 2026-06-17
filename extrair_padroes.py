"""
extrair_padroes.py - Módulo para extração de padrões geométricos (quads)

Este módulo é responsável pela: Extração de atributos e geração de 
padrões invariantes. Conceitos da disciplina: Reconhecimento de padrões e 
invariância geométrica.

Funcionalidades:
    - Geração de quads a partir de combinações de 4 estrelas
    - Cálculo do hash (4 índices das estrelas)
    - Controle de memória para evitar crash

Autor: Eduardo Fonseca Morato
Contato: morato@alunos.utfpr.edu.br
Disciplina: ELTD2 - Processamento de Imagens UTFPR
"""

import numpy as np
import math
from itertools import combinations
import struct
import gc
import json
from pathlib import Path


def extrair_padroes(estrelas, config=None):
    """
    Extrai padrões (quads) a partir das estrelas detectadas.
    
    Gera hashes compatíveis com o astrometry.net:
        - Cada quad é composto por 4 estrelas
        - O hash é calculado a partir das distâncias entre as estrelas
        - O formato é 4 inteiros de 32 bits (16 bytes)
    """
    
    # Configurações padrão com limites de segurança
    if config is None:
        config = {
            'max_quads': 100000,
            'sample_quads': False,
            'min_distance': 10.0,
            'max_distance': 500.0,
        }
    else:
        # Garante que todas as chaves existam
        config.setdefault('max_quads', 100000)
        config.setdefault('sample_quads', False)
        config.setdefault('min_distance', 10.0)
        config.setdefault('max_distance', 500.0)
    
    if len(estrelas) < 4:
        print(f"⚠️ Apenas {len(estrelas)} estrelas disponíveis. Mínimo: 4")
        return []
    
    # Gera quads
    quads = gerar_quads_com_controle(estrelas, config)
    
    return quads


def gerar_hash_quad(estrelas, indices):
    """
    Gera um hash compatível com o astrometry.net para um quad de 4 estrelas.
    
    O hash é baseado nas distâncias entre as estrelas, normalizado e discretizado.
    """
    # Obtém as 4 estrelas
    s1 = estrelas[indices[0]]
    s2 = estrelas[indices[1]]
    s3 = estrelas[indices[2]]
    s4 = estrelas[indices[3]]
    
    # Calcula distâncias entre pares (6 distâncias)
    p1 = (s1['x'], s1['y'])
    p2 = (s2['x'], s2['y'])
    p3 = (s3['x'], s3['y'])
    p4 = (s4['x'], s4['y'])
    
    d12 = distancia(p1, p2)
    d13 = distancia(p1, p3)
    d14 = distancia(p1, p4)
    d23 = distancia(p2, p3)
    d24 = distancia(p2, p4)
    d34 = distancia(p3, p4)
    
    # Ordena as distâncias
    distancias = sorted([d12, d13, d14, d23, d24, d34])
    
    # Normaliza pela maior distância (invariância a escala)
    max_dist = distancias[-1]
    if max_dist == 0:
        return None
    
    distancias_norm = [d / max_dist for d in distancias]
    
    # Discretiza para inteiros (escala de 0 a 1023)
    hash_values = []
    for d in distancias_norm:
        val = int(round(d * 1023))
        val = max(0, min(1023, val))
        hash_values.append(val)
    
    # Empacota os 6 valores em 4 inteiros de 32 bits
    hash_int1 = (hash_values[0] << 10) | hash_values[1]
    hash_int2 = (hash_values[2] << 10) | hash_values[3]
    hash_int3 = (hash_values[4] << 10) | hash_values[5]
    hash_int4 = 0
    
    return (hash_int1, hash_int2, hash_int3, hash_int4)


def gerar_quads_com_controle(estrelas, config):
    """Gera quads com controle de memória e progresso."""
    num_estrelas = len(estrelas)
    total_combinacoes = math.comb(num_estrelas, 4)
    
    print(f"  Gerando quads de {num_estrelas} estrelas...")
    print(f"    Total de combinações: {total_combinacoes:,}")
    
    max_quads = config.get('max_quads', 100000)
    sample_quads = config.get('sample_quads', False)
    
    if total_combinacoes > max_quads and sample_quads:
        print(f"    ⚠️ Limitando a {max_quads:,} quads (amostragem aleatória)")
        import random
        random.seed(42)
        indices = list(range(num_estrelas))
        amostra = random.sample(list(combinations(indices, 4)), max_quads)
        return gerar_quads_amostrados(estrelas, amostra, config)
    elif total_combinacoes > max_quads:
        print(f"    ⚠️ Reduzindo para {int(num_estrelas * 0.9)} estrelas...")
        novas_estrelas = estrelas[:int(num_estrelas * 0.9)]
        return gerar_quads_com_controle(novas_estrelas, config)
    
    return gerar_quads_completo(estrelas, config, total_combinacoes)


def gerar_quads_completo(estrelas, config, total_combinacoes):
    """Gera todos os quads com barra de progresso."""
    from tqdm import tqdm
    
    num_estrelas = len(estrelas)
    indices = list(range(num_estrelas))
    quads = []
    
    min_dist = config['min_distance']
    max_dist = config['max_distance']
    
    for i, j, k, l in tqdm(combinations(indices, 4), 
                           total=total_combinacoes, 
                           desc="  Gerando quads", 
                           unit="quad"):
        
        s1 = estrelas[i]
        s2 = estrelas[j]
        s3 = estrelas[k]
        s4 = estrelas[l]
        
        p1 = (s1['x'], s1['y'])
        p2 = (s2['x'], s2['y'])
        p3 = (s3['x'], s3['y'])
        p4 = (s4['x'], s4['y'])
        
        d12 = distancia(p1, p2)
        d23 = distancia(p2, p3)
        d34 = distancia(p3, p4)
        d41 = distancia(p4, p1)
        d13 = distancia(p1, p3)
        d24 = distancia(p2, p4)
        
        distancias = [d12, d23, d34, d41, d13, d24]
        if min(distancias) < min_dist or max(distancias) > max_dist:
            continue
        
        hash_quad = gerar_hash_quad(estrelas, [i, j, k, l])
        if hash_quad is None:
            continue
        
        area = calcular_area_quad(p1, p2, p3, p4)
        
        quad = {
            'hash': hash_quad,
            'vertices': [i, j, k, l],
            'estrelas': [s1, s2, s3, s4],
            'distancias': distancias,
            'area': area
        }
        
        quads.append(quad)
        
        if len(quads) % 10000 == 0:
            gc.collect()
    
    print(f"    Quads gerados após filtragem: {len(quads):,}")
    return quads


def gerar_quads_amostrados(estrelas, amostra, config):
    """Gera quads a partir de uma amostra aleatória."""
    from tqdm import tqdm
    
    quads = []
    min_dist = config['min_distance']
    max_dist = config['max_distance']
    
    for i, j, k, l in tqdm(amostra, desc="  Gerando quads (amostra)", unit="quad"):
        s1 = estrelas[i]
        s2 = estrelas[j]
        s3 = estrelas[k]
        s4 = estrelas[l]
        
        p1 = (s1['x'], s1['y'])
        p2 = (s2['x'], s2['y'])
        p3 = (s3['x'], s3['y'])
        p4 = (s4['x'], s4['y'])
        
        d12 = distancia(p1, p2)
        d23 = distancia(p2, p3)
        d34 = distancia(p3, p4)
        d41 = distancia(p4, p1)
        d13 = distancia(p1, p3)
        d24 = distancia(p2, p4)
        
        distancias = [d12, d23, d34, d41, d13, d24]
        if min(distancias) < min_dist or max(distancias) > max_dist:
            continue
        
        hash_quad = gerar_hash_quad(estrelas, [i, j, k, l])
        if hash_quad is None:
            continue
        
        area = calcular_area_quad(p1, p2, p3, p4)
        
        quad = {
            'hash': hash_quad,
            'vertices': [i, j, k, l],
            'estrelas': [s1, s2, s3, s4],
            'distancias': distancias,
            'area': area
        }
        
        quads.append(quad)
        
        if len(quads) % 10000 == 0:
            gc.collect()
    
    print(f"    Quads gerados (amostra): {len(quads):,}")
    return quads


def distancia(ponto1, ponto2):
    """Calcula a distância Euclidiana entre dois pontos."""
    x1, y1 = ponto1
    x2, y2 = ponto2
    return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)


def calcular_area_quad(p1, p2, p3, p4):
    """Calcula a área de um quadrilátero usando a fórmula do shoelace."""
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4
    
    area = 0.5 * abs(
        x1*y2 + x2*y3 + x3*y4 + x4*y1 -
        y1*x2 - y2*x3 - y3*x4 - y4*x1
    )
    
    return area


def exibir_info_padroes(padroes):
    """Exibe informações sobre os padrões gerados."""
    print(f"  Padrões gerados: {len(padroes)}")
    
    if padroes:
        hashes = [str(p['hash']) for p in padroes[:10]]
        print(f"    Hashes (amostra): {', '.join(hashes)}")


# ============================================================================
# TESTE
# ============================================================================

if __name__ == "__main__":
    import sys
    import json
    from pathlib import Path
    from detectar_estrelas import detectar_estrelas
    from ler_fits import carregar_imagem
    
    if len(sys.argv) > 1:
        caminho_teste = sys.argv[1]
        print(f"Testando extração de padrões (quads): {caminho_teste}")
        print("-" * 50)
        
        try:
            pasta_saida = Path("saidas_teste")
            arquivo_estrelas = pasta_saida / "estrelas_detectadas.json"
            
            if not arquivo_estrelas.exists():
                print(f"❌ Arquivo {arquivo_estrelas} não encontrado!")
                print("   Execute primeiro: python detectar_estrelas.py teste.fits")
                sys.exit(1)
            
            with open(arquivo_estrelas, 'r') as f:
                estrelas = json.load(f)
            
            print(f"Estrelas carregadas: {len(estrelas)}")
            
            # Configuração com todos os parâmetros
            config = {
                'max_quads': 300000,  # Suficiente para 50 estrelas
                'sample_quads': False,
                'min_distance': 10.0,
                'max_distance': 500.0,
            }
            padroes = extrair_padroes(estrelas, config)
            exibir_info_padroes(padroes)
            
            if padroes:
                dados_quads = []
                for quad in padroes:
                    dados_quads.append({
                        'hash': list(quad['hash']),
                        'vertices': quad['vertices'],
                        'area': quad.get('area', 0),
                        'distancias': quad['distancias']
                    })
                
                with open(pasta_saida / "quads_gerados.json", 'w') as f:
                    json.dump(dados_quads, f, indent=2)
                print(f"💾 Quads salvos em: {pasta_saida / 'quads_gerados.json'}")
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("Uso: python extrair_padroes.py caminho/para/imagem.fits")