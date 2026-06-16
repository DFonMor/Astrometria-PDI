"""
ler_fits.py - Módulo para leitura de arquivos FITS

Este módulo é responsável pela aquisição da imagem (Bloco 1 do pipeline).
Conceitos da disciplina: Aquisição e representação de imagens digitais.

Funcionalidades:
    - Leitura de arquivos .fits (formato padrão em astronomia)
    - Extração da matriz de pixels (dados da imagem)
    - Extração dos metadados (cabeçalho FITS)
    - Conversão para float64 e normalização básica

Autor: Eduardo Fonseca Morato
Contato: morato@alunos.utfpr.edu.br
Disciplina: ELTD2 - Processamento de Imagens UTFPR
"""

import numpy as np
from astropy.io import fits


def carregar_imagem(caminho_arquivo):
    """
    Carrega uma imagem no formato FITS e retorna seus dados e cabeçalho.
    
    O formato FITS (Flexible Image Transport System) é o padrão da astronomia.
    Ele armazena tanto os dados da imagem (matriz de pixels) quanto metadados
    como coordenadas, data da observação, exposição, etc.
    
    Args:
        caminho_arquivo (str): Caminho para o arquivo .fits
    
    Returns:
        tuple: (imagem, cabecalho)
            - imagem (numpy.ndarray): Matriz 2D float64 com os pixels normalizados
            - cabecalho (dict): Dicionário com os metadados do arquivo
    
    Raises:
        FileNotFoundError: Se o arquivo não existir
        ValueError: Se o arquivo não for um FITS válido ou não tiver dados 2D
    
    Exemplo:
        >>> imagem, header = carregar_imagem("orion.fits")
        >>> print(imagem.shape)
        (1080, 1920)
        >>> print(header.get('EXPTIME'))
        30.0
    """
    
    # Verifica se o arquivo existe
    from pathlib import Path
    if not Path(caminho_arquivo).exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")
    
    # Abre o arquivo FITS usando a astropy
    # O contexto 'with' garante que o arquivo seja fechado corretamente
    with fits.open(caminho_arquivo) as hdul:
        
        # O primeiro extension (HDUL[0]) contém os dados da imagem
        dados_raw = hdul[0].data
        
        # Extrai o cabeçalho (metadados) como dicionário
        cabecalho = dict(hdul[0].header)
        
        # Verifica se os dados são 2D (imagem) e não 1D ou 3D
        if dados_raw is None:
            raise ValueError(f"Arquivo {caminho_arquivo} não contém dados de imagem")
        
        if dados_raw.ndim != 2:
            raise ValueError(f"Esperada imagem 2D, mas tem dimensão {dados_raw.ndim}")
    
    # Converte para float64 para evitar problemas de overflow
    # e permite operações matemáticas precisas
    imagem = dados_raw.astype(np.float64)
    
    # Normalização básica: garante que os valores estão no range apropriado
    imagem = normalizar_imagem(imagem)
    
    return imagem, cabecalho


def normalizar_imagem(imagem):
    """
    Normaliza a imagem para o intervalo [0, 1].
    
    Esta é uma transformação ponto-a-ponto (conceito da Aula 03).
    A normalização preserva as relações relativas entre os pixels
    enquanto permite operações consistentes.
    
    A fórmula utilizada é: S = (r - r_min) / (r_max - r_min)
    (conforme slide 7 da Aula 03)
    
    Args:
        imagem (numpy.ndarray): Imagem de entrada (qualquer escala)
    
    Returns:
        numpy.ndarray: Imagem normalizada no intervalo [0, 1]
    """
    r_min = np.min(imagem)
    r_max = np.max(imagem)
    
    # Evita divisão por zero se a imagem for constante
    if r_max == r_min:
        return np.zeros_like(imagem)
    
    return (imagem - r_min) / (r_max - r_min)


def obter_metadado_importante(cabecalho, chave, valor_padrao=None):
    """
    Extrai um metadado específico do cabeçalho FITS de forma segura.
    
    Alguns metadados úteis para astrometria:
        - 'NAXIS1', 'NAXIS2': dimensões da imagem
        - 'EXPTIME': tempo de exposição
        - 'DATE-OBS': data da observação
        - 'RA', 'DEC': coordenadas aproximadas (se disponíveis)
        - 'FOCALLEN': distância focal (se registrada)
        - 'PIXSIZE': tamanho do pixel (se registrada)
    
    Args:
        cabecalho (dict): Cabeçalho FITS
        chave (str): Chave do metadado (ex: 'EXPTIME')
        valor_padrao: Valor a retornar se a chave não existir
    
    Returns:
        Valor do metadado ou valor_padrao se não encontrado
    """
    return cabecalho.get(chave, valor_padrao)


def exibir_info_imagem(imagem, cabecalho):
    """
    Exibe informações básicas sobre a imagem carregada (para debug).
    
    Args:
        imagem (numpy.ndarray): Imagem carregada
        cabecalho (dict): Cabeçalho FITS
    """
    print(f"  Dimensões: {imagem.shape[0]} × {imagem.shape[1]} pixels")
    print(f"  Tipo dos dados: {imagem.dtype}")
    print(f"  Faixa de valores: [{np.min(imagem):.3f}, {np.max(imagem):.3f}]")
    print(f"  Média: {np.mean(imagem):.3f}")
    print(f"  Desvio padrão: {np.std(imagem):.3f}")
    
    # Metadados comuns que podem ser úteis
    exptime = obter_metadado_importante(cabecalho, 'EXPTIME')
    if exptime:
        print(f"  Tempo de exposição: {exptime} s")
    
    date_obs = obter_metadado_importante(cabecalho, 'DATE-OBS')
    if date_obs:
        print(f"  Data da observação: {date_obs}")


# ============================================================================
# TESTE (executado apenas se rodar este arquivo diretamente)
# ============================================================================

if __name__ == "__main__":
    # Exemplo de uso - teste com um arquivo real
    import sys
    
    if len(sys.argv) > 1:
        caminho_teste = sys.argv[1]
        print(f"Testando leitura do arquivo: {caminho_teste}")
        print("-" * 50)
        
        try:
            img, header = carregar_imagem(caminho_teste)
            print("✅ Imagem carregada com sucesso!")
            exibir_info_imagem(img, header)
            
        except Exception as e:
            print(f"❌ Erro ao carregar: {e}")
    else:
        print("Uso: python ler_fits.py caminho/para/imagem.fits")