"""
ler_fits.py - Modulo para leitura de arquivos FITS

Este modulo e responsavel pela aquisicao da imagem.
Conceitos da disciplina: Aquisicao e representacao de imagens digitais.

Funcionalidades:
    - Leitura de arquivos .fits (formato padrao em astronomia)
    - Extracao da matriz de pixels (dados da imagem)
    - Extracao dos metadados (cabecalho FITS)
    - Conversao para float64 e normalizacao basica

Autor: Eduardo Fonseca Morato
Contato: morato@alunos.utfpr.edu.br
Disciplina: ELTD2 - Processamento de Imagens UTFPR
"""

import numpy as np
from astropy.io import fits
from astropy.io.fits import ImageHDU


def carregar_imagem(caminho_arquivo):
    """
    Carrega uma imagem no formato FITS e retorna seus dados e cabecalho.
    
    O formato FITS (Flexible Image Transport System) e o padrao da astronomia.
    Ele armazena tanto os dados da imagem (matriz de pixels) quanto metadados
    como coordenadas, data da observacao, exposicao, etc.
    
    Args:
        caminho_arquivo (str): Caminho para o arquivo .fits
    
    Returns:
        tuple: (imagem, cabecalho)
            - imagem (numpy.ndarray): Matriz 2D float64 com os pixels normalizados
            - cabecalho (dict): Dicionario com os metadados do arquivo
    
    Raises:
        FileNotFoundError: Se o arquivo nao existir
        ValueError: Se o arquivo nao for um FITS valido ou nao tiver dados 2D
    """
    
    # Verifica se o arquivo existe
    from pathlib import Path
    if not Path(caminho_arquivo).exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {caminho_arquivo}")
    
    # Abre o arquivo FITS usando a astropy
    # O contexto 'with' garante que o arquivo seja fechado corretamente
    with fits.open(caminho_arquivo) as hdul:
        
        # Pega o primeiro HDU (Header Data Unit)
        imagem_hdu: ImageHDU = hdul[0]

        # O primeiro extension (HDUL[0]) contem os dados da imagem
        dados_raw = imagem_hdu.data 
        
        # Extrai o cabecalho (metadados) como dicionario
        cabecalho = dict(imagem_hdu.header) 
        
        # Verifica se os dados sao 2D (imagem) e nao 1D ou 3D
        if dados_raw is None:
            raise ValueError(f"Arquivo {caminho_arquivo} nao contem dados de imagem")
        
        if dados_raw.ndim != 2:
            raise ValueError(f"Esperada imagem 2D, mas tem dimensao {dados_raw.ndim}")
    
    # Converte para float64 para evitar problemas de overflow
    # e permite operacoes matematicas precisas
    imagem = dados_raw.astype(np.float64)
    
    # Normalizacao basica: garante que os valores estao no range apropriado
    imagem = normalizar_imagem(imagem)
    
    return imagem, cabecalho


def normalizar_imagem(imagem):
    """
    Normaliza a imagem para o intervalo [0, 1].
    
    Esta e uma transformacao ponto-a-ponto (conceito da Aula 03).
    A normalizacao preserva as relacoes relativas entre os pixels
    enquanto permite operacoes consistentes.

    Diferente de imagens JPEG/PNG, os dados FITS sao lineares e devem
    ser preservados como tais para analises cientificas (como astrometria).
    
    A formula utilizada e: S = (r - r_min) / (r_max - r_min)
    (conforme visto em sala na Aula 03)
    
    Args:
        imagem (numpy.ndarray): Imagem de entrada (qualquer escala)
    
    Returns:
        numpy.ndarray: Imagem normalizada no intervalo [0, 1]
    """

    if imagem.dtype != np.float64:
        imagem = imagem.astype(np.float64)

    r_min = np.min(imagem)
    r_max = np.max(imagem)
    
    # Evita divisao por zero se a imagem for constante
    if r_max == r_min:
        return np.zeros_like(imagem)
    
    return (imagem - r_min) / (r_max - r_min)


def obter_metadado_importante(cabecalho, chave, valor_padrao=None):
    """
    Extrai um metadado especifico do cabecalho FITS de forma segura.
    
    Alguns metadados uteis para esse projeto:
        - 'EXPTIME': tempo de exposicao
        - 'DATE-OBS': data da observacao
        - 'RA', 'DEC': coordenadas aproximadas (se disponiveis)
    
    Args:
        cabecalho (dict): Cabecalho FITS
        chave (str): Chave do metadado (ex: 'EXPTIME')
        valor_padrao: Valor a retornar se a chave nao existir
    
    Returns:
        Valor do metadado ou valor_padrao se nao encontrado
    """
    return cabecalho.get(chave, valor_padrao)


def exibir_info_imagem(imagem, cabecalho):
    """
    Exibe informacoes basicas sobre a imagem carregada (para debug).
    
    Args:
        imagem (numpy.ndarray): Imagem carregada
        cabecalho (dict): Cabecalho FITS
    """
    print(f"  Dimensoes: {imagem.shape[0]} x {imagem.shape[1]} pixels")
    print(f"  Tipo dos dados: {imagem.dtype}")
    print(f"  Faixa de valores: [{np.min(imagem):.3f}, {np.max(imagem):.3f}]")
    print(f"  Media: {np.mean(imagem):.3f}")
    print(f"  Desvio padrao: {np.std(imagem):.3f}")
    
    # Metadados comuns que podem ser uteis
    exptime = obter_metadado_importante(cabecalho, 'EXPTIME')
    if exptime:
        print(f"  Tempo de exposicao: {exptime} s")
    
    date_obs = obter_metadado_importante(cabecalho, 'DATE-OBS')
    if date_obs:
        print(f"  Data da observacao: {date_obs}")

    ra = obter_metadado_importante(cabecalho, 'RA')
    if ra:
        print(f"  Ascensao Reta: {ra}")

    dec = obter_metadado_importante(cabecalho, 'DEC')
    if dec:
        print(f"  Declinacao: {dec}")


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
            print("Imagem carregada com sucesso!")
            exibir_info_imagem(img, header)
            
        except Exception as e:
            print(f"Erro ao carregar: {e}")
    else:
        print("Uso: python ler_fits.py caminho/para/imagem.fits")
