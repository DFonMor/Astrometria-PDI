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
import gc


def extrair_padroes(estrelas, config=None):
    """
    Extrai padrões (quads) a partir das estrelas detectadas.
    
    NOTA: As estrelas de entrada já devem estar selecionadas (as N mais brilhantes).
          O detectar_estrelas.py já retorna as estrelas ordenadas por brilho.
    
    Pipeline:
        1. Gera todas as combinações de 4 estrelas (quads)
        2. Para cada quad, o hash é o próprio conjunto de 4 índices
        3. Filtra quads com estrelas muito próximas/distantes
    
    Args:
        estrelas (list): Lista de estrelas detectadas (já ordenadas por brilho)
        config (dict, optional): Parâmetros de configuração.
    
    Returns:
        list: Lista de dicionários, cada um contendo:
              - hash (tuple): Chave = (star1, star2, star3, star4)
              - vertices (list): Índices das 4 estrelas
              - estrelas (list): Os objetos estrela completos
              - area (float): Área do quad (opcional)
              - distancias (list): Distâncias entre os pares
    """
    
    # Configurações padrão com limites de segurança
    if config is None:
        config = {
            'max_quads': 100000,        # Máximo de quads a gerar
            'sample_quads': False,      # Se True, amostra aleatória se exceder max_quads
            'min_distance': 10.0,       # Distância mínima entre estrelas (pixels)
            'max_distance': 500.0,      # Distância máxima entre estrelas (pixels)
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
    
    # Gera quads com controle de memória
    quads = gerar_quads_com_controle(estrelas, config)
    
    return quads


def gerar_quads_com_controle(estrelas, config):
    """
    Gera quads com controle de memória e progresso.
    
    Args:
        estrelas (list): Lista de estrelas
        config (dict): Configurações
    
    Returns:
        list: Lista de quads
    """
    num_estrelas = len(estrelas)
    
    # Calcula total de combinações
    total_combinacoes = math.comb(num_estrelas, 4)
    
    print(f"  Gerando quads de {num_estrelas} estrelas...")
    print(f"    Total de combinações: {total_combinacoes:,}")
    
    # Limites de segurança
    max_quads = config.get('max_quads', 100000)
    sample_quads = config.get('sample_quads', False)
    
    # Verifica se o número de combinações é excessivo
    if total_combinacoes > max_quads:
        print(f"    ⚠️ Combinações excedem limite de {max_quads:,}")
        
        if sample_quads:
            print(f"    → Amostrando aleatoriamente {max_quads:,} quads")
            return gerar_quads_amostrados(estrelas, config, total_combinacoes, max_quads)
        else:
            # Reduz o número de estrelas (pega as mais brilhantes)
            novas_estrelas = estrelas[:int(np.floor(num_estrelas * 0.9))]
            print(f"    → Reduzindo para {len(novas_estrelas)} estrelas e tentando novamente...")
            return gerar_quads_com_controle(novas_estrelas, config)
    
    # Geração completa (com barra de progresso)
    return gerar_quads_completo(estrelas, config, total_combinacoes)


def gerar_quads_completo(estrelas, config, total_combinacoes):
    """
    Gera todos os quads com barra de progresso.
    
    Args:
        estrelas (list): Lista de estrelas
        config (dict): Configurações
        total_combinacoes (int): Número total de combinações
    
    Returns:
        list: Lista de quads
    """
    num_estrelas = len(estrelas)
    indices = list(range(num_estrelas))
    quads = []
    
    min_dist = config['min_distance']
    max_dist = config['max_distance']
    
    # Contador para progresso
    processados = 0
    ultimo_progresso = 0
    
    # Gera todas as combinações de 4 estrelas
    for i, j, k, l in combinations(indices, 4):
        # Atualiza progresso a cada 1000 combinações
        processados += 1
        if processados - ultimo_progresso >= 1000:
            ultimo_progresso = processados
            percentual = (processados / total_combinacoes) * 100
            print(f"    Processando: {percentual:.1f}% ({processados:,}/{total_combinacoes:,})", end='\r')
        
        # Obtém coordenadas das 4 estrelas
        s1 = estrelas[i]
        s2 = estrelas[j]
        s3 = estrelas[k]
        s4 = estrelas[l]
        
        p1 = (s1['x'], s1['y'])
        p2 = (s2['x'], s2['y'])
        p3 = (s3['x'], s3['y'])
        p4 = (s4['x'], s4['y'])
        
        # Calcula distâncias entre pares (para filtrar)
        d12 = distancia(p1, p2)
        d23 = distancia(p2, p3)
        d34 = distancia(p3, p4)
        d41 = distancia(p4, p1)
        d13 = distancia(p1, p3)
        d24 = distancia(p2, p4)
        
        # Filtra distâncias inválidas
        distancias = [d12, d23, d34, d41, d13, d24]
        if min(distancias) < min_dist or max(distancias) > max_dist:
            continue
        
        # O hash do quad é o próprio conjunto de 4 índices
        hash_quad = (i, j, k, l)
        
        # Calcula área (opcional)
        area = calcular_area_quad(p1, p2, p3, p4)
        
        quad = {
            'hash': hash_quad,
            'vertices': [i, j, k, l],
            'estrelas': [s1, s2, s3, s4],
            'area': area,
            'distancias': distancias
        }
        
        quads.append(quad)
        
        # Libera memória periodicamente (a cada 10.000 quads)
        if len(quads) % 10000 == 0:
            gc.collect()
    
    print(f"    Processando: 100.0% ({processados:,}/{total_combinacoes:,})")
    print(f"    Quads gerados após filtragem: {len(quads):,}")
    
    return quads


def gerar_quads_amostrados(estrelas, config, total_combinacoes, max_quads):
    """
    Gera uma amostra aleatória de quads para evitar sobrecarga.
    
    Args:
        estrelas (list): Lista de estrelas
        config (dict): Configurações
        total_combinacoes (int): Número total de combinações
        max_quads (int): Número máximo de quads a gerar
    
    Returns:
        list: Lista de quads amostrados
    """
    num_estrelas = len(estrelas)
    indices = list(range(num_estrelas))
    quads = []
    
    min_dist = config['min_distance']
    max_dist = config['max_distance']
    
    # Gera uma amostra aleatória de combinações
    import random
    random.seed(42)  # Para reprodutibilidade
    
    # Amostra sem repetição
    amostra_indices = random.sample(list(combinations(indices, 4)), 
                                   min(max_quads, total_combinacoes))
    
    print(f"    Amostrando {len(amostra_indices):,} quads...")
    
    for i, j, k, l in amostra_indices:
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
        
        hash_quad = (i, j, k, l)
        area = calcular_area_quad(p1, p2, p3, p4)
        
        quad = {
            'hash': hash_quad,
            'vertices': [i, j, k, l],
            'estrelas': [s1, s2, s3, s4],
            'area': area,
            'distancias': distancias
        }
        
        quads.append(quad)
    
    print(f"    Quads amostrados após filtragem: {len(quads):,}")
    
    return quads


def distancia(ponto1, ponto2):
    """
    Calcula a distância Euclidiana entre dois pontos.
    
    Args:
        ponto1 (tuple): (x, y)
        ponto2 (tuple): (x, y)
    
    Returns:
        float: Distância Euclidiana
    """
    x1, y1 = ponto1
    x2, y2 = ponto2
    return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)


def calcular_area_quad(p1, p2, p3, p4):
    """
    Calcula a área de um quadrilátero usando a fórmula do shoelace.
    
    Args:
        p1, p2, p3, p4 (tuple): Coordenadas dos vértices (x, y)
    
    Returns:
        float: Área do quadrilátero
    """
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
    """
    Exibe informações sobre os padrões gerados (para debug).
    
    Args:
        padroes (list): Lista de quads
    """
    print(f"  Padrões gerados: {len(padroes)}")
    
    if padroes:
        # Amostra dos primeiros hashes
        hashes = [str(p['hash']) for p in padroes[:10]]
        print(f"    Hashes (amostra): {', '.join(hashes)}")
        
        # Estatísticas das distâncias
        dists = []
        for p in padroes:
            dists.extend(p['distancias'])
        
        if dists:
            print(f"    Distâncias: "
                  f"min={min(dists):.1f}, max={max(dists):.1f}, "
                  f"média={np.mean(dists):.1f}")
        
        # Contagem de hashes únicos
        hashes_unicos = len(set(p['hash'] for p in padroes))
        print(f"    Hashes únicos: {hashes_unicos} de {len(padroes)} "
              f"({hashes_unicos/len(padroes)*100:.1f}%)")


# ============================================================================
# TESTE (executado apenas se rodar este arquivo diretamente)
# ============================================================================

if __name__ == "__main__":
    import sys
    import json
    from pathlib import Path
    import matplotlib.pyplot as plt
    from ler_fits import carregar_imagem
    from melhorar_imagem import pre_processar
    
    if len(sys.argv) > 1:
        caminho_teste = sys.argv[1]
        print(f"Testando extração de padrões (quads): {caminho_teste}")
        print("-" * 50)
        
        try:
            # ============================================================
            # CARREGA AS ESTRELAS DO ARQUIVO GERADO PELO detectar_estrelas
            # ============================================================
            pasta_saida = Path("saidas_teste")
            arquivo_estrelas = pasta_saida / "estrelas_detectadas.json"
            
            if not arquivo_estrelas.exists():
                print(f"❌ Arquivo {arquivo_estrelas} não encontrado!")
                print("   Execute primeiro: python detectar_estrelas.py teste.fits")
                sys.exit(1)
            
            with open(arquivo_estrelas, 'r') as f:
                estrelas = json.load(f)
            
            print(f"Estrelas carregadas: {len(estrelas)}")
            
            # ============================================================
            # EXTRAI PADRÕES
            # ============================================================
            # Configuração vazia - os valores padrão serão usados
            config = {}
            padroes = extrair_padroes(estrelas, config)
            exibir_info_padroes(padroes)
            
            # ============================================================
            # SALVA OS QUADS
            # ============================================================
            if padroes:
                dados_quads = []
                for quad in padroes:
                    dados_quads.append({
                        'hash': list(quad['hash']),
                        'vertices': quad['vertices'],
                        'area': quad['area'],
                        'distancias': quad['distancias']
                    })
                
                with open(pasta_saida / "quads_gerados.json", 'w') as f:
                    json.dump(dados_quads, f, indent=2)
                print(f"💾 Quads salvos em: {pasta_saida / 'quads_gerados.json'}")
            
            # ============================================================
            # VISUALIZAÇÃO DOS QUADS
            # ============================================================
            if padroes and len(estrelas) >= 4:
                import random
                amostra = random.sample(padroes, min(5, len(padroes)))
                
                # Carrega a imagem original para visualização
                img_raw, header = carregar_imagem(caminho_teste)
                img_vis = pre_processar(img_raw)
                
                fig, ax = plt.subplots(1, 1, figsize=(10, 8))
                ax.imshow(img_vis, cmap='gray', origin='lower')
                ax.set_xlim(0, img_vis.shape[1])
                ax.set_ylim(0, img_vis.shape[0])
                
                # Desenha os quads amostrados
                cores = ['red', 'blue', 'green', 'yellow', 'magenta']
                for idx, quad in enumerate(amostra):
                    cor = cores[idx % len(cores)]
                    vertices = quad['estrelas']
                    
                    # Extrai coordenadas
                    pts = [(s['x'], s['y']) for s in vertices]
                    pts.append(pts[0])  # Fecha o quad
                    
                    xs, ys = zip(*pts)
                    ax.plot(xs, ys, color=cor, linewidth=1.5)
                    ax.text(pts[0][0], pts[0][1] - 10, str(quad['hash'])[:8], 
                           color=cor, fontsize=8)
                
                ax.set_title(f'{len(padroes)} quads gerados (amostra de {len(amostra)})')
                ax.axis('off')
                plt.tight_layout()
                plt.show()
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("Uso: python extrair_padroes.py caminho/para/imagem.fits")