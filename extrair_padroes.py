"""
extrair_padroes.py - Módulo para extração de padrões geométricos (triângulos)

Este módulo é responsável pela: Extração de atributos e geração de 
padrões invariantes. Conceitos da disciplina: Reconhecimento de padrões e 
invariância geométrica.

Funcionalidades:
    - Seleção das N estrelas mais brilhantes
    - Geração de triângulos a partir de combinações de 3 estrelas
    - Cálculo de distâncias normalizadas entre pares
    - Criação de hash (chave) para cada triângulo

Autor: Eduardo Fonseca Morato
Contato: morato@alunos.utfpr.edu.br
Disciplina: ELTD2 - Processamento de Imagens UTFPR
"""

import numpy as np
from itertools import combinations


def extrair_padroes(estrelas, config=None):
    """
    Extrai padrões (triângulos) a partir das estrelas detectadas.
    
    Pipeline:
        1. Gera todas as combinações de 3 estrelas (triângulos)
        2. Para cada triângulo, calcula as 3 distâncias entre pares
        3. Normaliza as distâncias pelo maior lado (invariância a escala)
        4. Cria um hash (chave) para busca no banco de dados
    
    Args:
        estrelas (list): Lista de estrelas detectadas (ordenadas por brilho)
        config (dict, optional): Parâmetros de configuração.
    
    Returns:
        list: Lista de dicionários, cada um contendo:
              - hash (str): Chave identificadora (ex: "0.45_0.67_0.89")
              - vertices (list): Índices das 3 estrelas
              - lados (list): Distâncias normalizadas [d1, d2, d3]
              - lados_abs (list): Distâncias em pixels [d1, d2, d3]
              - area (float): Área do triângulo (normalizada)
    """
    
    # Configurações padrão
    if config is None:
        config = {
            'num_stars': 40,           # Número de estrelas mais brilhantes
            'hash_precision': 2,       # Casas decimais para discretização
            'normalize': True,         # Normalizar distâncias pelo maior lado
            'min_distance': 10.0,      # Distância mínima entre estrelas (pixels)
            'max_distance': 500.0,     # Distância máxima entre estrelas (pixels)
        }
    
    # Seleciona as N estrelas mais brilhantes
    
    # Gera triângulos a partir das combinações
    triangulos = gerar_triangulos(estrelas, config)
    
    return triangulos

def gerar_triangulos(estrelas, config):
    """
    Gera triângulos a partir de combinações de 3 estrelas.
    
    Conceito: 
        - Triângulos são invariantes a rotação e translação
        - Com normalização, tornam-se invariantes a escala
        - O hash permite busca rápida no banco de dados
    
    Args:
        estrelas (list): Lista de estrelas
        config (dict): Configurações com parâmetros
    
    Returns:
        list: Lista de dicionários representando triângulos
    """
    num_estrelas = len(estrelas)
    
    if num_estrelas < 3:
        return []
    
    # Limite máximo de combinações para evitar explosão computacional
    # C(40, 3) = 9880 triângulos, aceitável
    if num_estrelas > 50:
        print(f"⚠️ Muitas estrelas ({num_estrelas}), usando apenas as 50 mais brilhantes")
        estrelas = estrelas[:50]
        num_estrelas = 50
    
    triangulos = []
    indices = list(range(num_estrelas))
    
    # Gera todas as combinações de 3 estrelas
    for i, j, k in combinations(indices, 3):
        # Obtém coordenadas das 3 estrelas
        p1 = (estrelas[i]['x'], estrelas[i]['y'])
        p2 = (estrelas[j]['x'], estrelas[j]['y'])
        p3 = (estrelas[k]['x'], estrelas[k]['y'])
        
        # Calcula distâncias entre pares
        d12 = distancia(p1, p2)
        d23 = distancia(p2, p3)
        d31 = distancia(p3, p1)
        
        # Filtra distâncias inválidas
        if (d12 < config['min_distance'] or d23 < config['min_distance'] or d31 < config['min_distance']):
            continue
        if (d12 > config['max_distance'] or d23 > config['max_distance'] or d31 > config['max_distance']):
            continue
        
        # Ordena os lados (invariância a permutação)
        lados = sorted([d12, d23, d31])
        
        # Normaliza pelo maior lado (invariância a escala)
        if config['normalize']:
            lado_max = lados[2]  # O maior após ordenação
            if lado_max > 0:
                lados_norm = [l / lado_max for l in lados]
            else:
                continue  # Triângulo degenerado
        else:
            lados_norm = lados
        
        # Cria hash (discretiza os valores para busca)
        hash_tri = criar_hash(lados_norm, config['hash_precision'])
        
        # Calcula área (opcional, pode ser usada para filtragem)
        area = calcular_area(p1, p2, p3)
        
        triangulo = {
            'hash': hash_tri,
            'vertices': [i, j, k],
            'lados': lados_norm,
            'lados_abs': lados,
            'area': area,
            'estrelas': [estrelas[i], estrelas[j], estrelas[k]]
        }
        
        triangulos.append(triangulo)
    
    return triangulos


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


def calcular_area(p1, p2, p3):
    """
    Calcula a área de um triângulo usando a fórmula de Heron.
    
    Args:
        p1, p2, p3 (tuple): Coordenadas dos vértices (x, y)
    
    Returns:
        float: Área do triângulo
    """
    d12 = distancia(p1, p2)
    d23 = distancia(p2, p3)
    d31 = distancia(p3, p1)
    
    # Semiperímetro
    s = (d12 + d23 + d31) / 2.0
    
    # Fórmula de Heron
    try:
        area = np.sqrt(s * (s - d12) * (s - d23) * (s - d31))
    except ValueError:
        area = 0.0
    
    return area


def criar_hash(lados_norm, precisao=2):
    """
    Cria um hash (string) a partir dos lados normalizados.
    
    O hash é uma string que serve como chave para busca no banco de dados.
    A discretização (arredondamento) permite matching aproximado.
    
    Args:
        lados_norm (list): Lista de 3 valores normalizados
        precisao (int): Número de casas decimais
    
    Returns:
        str: Hash no formato "d1_d2_d3"
    
    Exemplo:
        >>> criar_hash([0.4567, 0.7890, 1.0], 2)
        '0.46_0.79_1.00'
    """
    # Arredonda para a precisão desejada
    lados_rounded = [round(l, precisao) for l in lados_norm]
    
    # Formata como string com zeros à direita
    lados_str = [f"{l:.{precisao}f}" for l in lados_rounded]
    
    # Junta com underscore
    return "_".join(lados_str)


def exibir_info_padroes(padroes):
    """
    Exibe informações sobre os padrões gerados (para debug).
    
    Args:
        padroes (list): Lista de triângulos
    """
    print(f"  Padrões gerados: {len(padroes)}")
    
    if padroes:
        # Amostra dos primeiros hashes
        hashes = [p['hash'] for p in padroes[:10]]
        print(f"    Hashes (amostra): {', '.join(hashes)}")
        
        # Estatísticas das distâncias
        dists = []
        for p in padroes:
            dists.extend(p['lados'])
        
        if dists:
            print(f"    Distâncias normalizadas: "
                  f"min={min(dists):.3f}, max={max(dists):.3f}, "
                  f"média={np.mean(dists):.3f}")
        
        # Contagem de hashes únicos
        hashes_unicos = len(set(p['hash'] for p in padroes))
        print(f"    Hashes únicos: {hashes_unicos} de {len(padroes)} "
              f"({hashes_unicos/len(padroes)*100:.1f}%)")


# ============================================================================
# TESTE (executado apenas se rodar este arquivo diretamente)
# ============================================================================

if __name__ == "__main__":
    import sys
    import matplotlib.pyplot as plt
    from ler_fits import carregar_imagem
    from melhorar_imagem import pre_processar
    from detectar_estrelas import detectar_estrelas
    
    if len(sys.argv) > 1:
        caminho_teste = sys.argv[1]
        print(f"Testando extração de padrões: {caminho_teste}")
        print("-" * 50)
        
        try:
            # Pipeline completo até detecção
            img_raw, header = carregar_imagem(caminho_teste)
            img_proc = pre_processar(img_raw)
            estrelas = detectar_estrelas(img_proc)
            
            print(f"Estrelas detectadas: {len(estrelas)}")
            
            # Extrai padrões
            config = {'num_stars': 40, 'hash_precision': 2}
            padroes = extrair_padroes(estrelas, config)
            exibir_info_padroes(padroes)
            
            # Mostra visualização dos triângulos (opcional)
            if padroes and len(estrelas) >= 3:
                # Pega os primeiros 5 triângulos para visualizar
                import random
                amostra = random.sample(padroes, min(5, len(padroes)))
                
                fig, ax = plt.subplots(1, 1, figsize=(10, 8))
                ax.imshow(img_proc, cmap='gray')
                
                # Desenha os triângulos amostrados
                cores = ['red', 'blue', 'green', 'yellow', 'magenta']
                for idx, tri in enumerate(amostra):
                    cor = cores[idx % len(cores)]
                    vertices = tri['estrelas']
                    
                    # Extrai coordenadas
                    pts = [(s['x'], s['y']) for s in vertices]
                    pts.append(pts[0])  # Fecha o triângulo
                    
                    xs, ys = zip(*pts)
                    ax.plot(xs, ys, color=cor, linewidth=1.5)
                    ax.text(pts[0][0], pts[0][1] - 10, tri['hash'][:8], 
                           color=cor, fontsize=8)
                
                ax.set_title(f'{len(padroes)} triângulos gerados (amostra de {len(amostra)})')
                plt.tight_layout()
                plt.show()
            
        except Exception as e:
            print(f"❌ Erro: {e}")
    else:
        print("Uso: python extrair_padroes.py caminho/para/imagem.fits")