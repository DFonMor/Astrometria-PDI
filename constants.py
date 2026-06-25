"""
constants.py - Parametros constantes do sistema de astrometria

Este arquivo contem todas as configuracoes fixas do projeto:
    - Parametros do telescopio Seestar S50
    - Configuracoes do algoritmo (deteccao, visualizacao, plate solving)
    - Parametros para leitura dos indices do astrometry.net

Autor: Eduardo Fonseca Morato
Contato: morato@alunos.utfpr.edu.br
Disciplina: ELTD2 - Processamento de Imagens UTFPR
"""

# ============================================================================
# PARAMETROS DO TELESCOPIO - SEESTAR S50
# ============================================================================

# Constantes fisicas do equipamento
FOCAL_LENGTH_MM = 250.0          # Distancia focal [mm]
PIXEL_SIZE_UM = 2.9              # Tamanho do pixel [micrometros]
SENSOR_WIDTH_PX = 1920           # Largura do sensor [pixels]
SENSOR_HEIGHT_PX = 1080          # Altura do sensor [pixels]

# Constantes derivadas (calculos automaticos)
def escala_arcsec_px():
    """Escala de placa em arcsegundos por pixel"""
    return 206.265 * PIXEL_SIZE_UM / FOCAL_LENGTH_MM

def fov_width_arcmin():
    """Campo de visao horizontal em minutos de arco"""
    return (escala_arcsec_px() * SENSOR_WIDTH_PX) / 60.0

def fov_height_arcmin():
    """Campo de visao vertical em minutos de arco"""
    return (escala_arcsec_px() * SENSOR_HEIGHT_PX) / 60.0


# ============================================================================
# CONFIGURACAO DE VISUALIZACAO (melhorar_imagem)
# ============================================================================

CONFIG_VISUALIZACAO = {
    'low_percent': 5,          # Percentil inferior (5 = mais contraste)
    'high_percent': 90,        # Percentil superior (90 = mais contraste)
    'use_clahe': False,        # True para usar CLAHE (contraste local)
    'clahe_clip_limit': 0.02,  # Limite de contraste do CLAHE
}


# ============================================================================
# CONFIGURACAO DE DETECCAO DE ESTRELAS (detectar_estrelas)
# ============================================================================

CONFIG_DETECCAO = {
    'fwhm': 3.0,               # Largura tipica da estrela (FWHM) em pixels
    'threshold': 3.0,          # Limiar em sigma (3 = 3-sigma)
    'n_brightest': 50,         # Numero maximo de estrelas a retornar
    'sharpness_range': (-1.0, 1.0),  # Faixa de nitidez
    'roundness_range': (-1.0, 1.0),  # Faixa de circularidade
    'box_size': 50,            # Tamanho da grade para estimativa de fundo
    'filter_size': 3,          # Tamanho do filtro para estimativa de fundo
}


# ============================================================================
# CONFIGURACAO DE PLATE SOLVING (plate_solve)
# ============================================================================

CONFIG_PLATE_SOLVE = {
    'indices_dir': '/home/dell/Astrometria-PDI/data',  # Caminho para os indices
    'scale_low': 0.3,          # Limite inferior da escala (graus)
    'scale_high': 1.0,         # Limite superior da escala (graus)
    'width': 1920,             # Largura da imagem (pixels)
    'height': 1080,            # Altura da imagem (pixels)
    'timeout': 120,            # Tempo maximo de execucao (segundos)
    'verbose': True,           # Exibir mensagens detalhadas
}


# ============================================================================
# CONFIGURACAO DE SAIDA (exibir_resultado)
# ============================================================================

CONFIG_SAIDA = {
    'salvar_imagens': True,    # Salvar imagens em disco
    'pasta_saida': 'resultados',  # Pasta para salvar os resultados
    'mostrar_imagens': True,   # Exibir imagens na tela
    'max_estrelas_mostrar': 50, # Numero maximo de estrelas a marcar
}


# ============================================================================
# PARA TESTE (se rodar o arquivo diretamente)
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("CONFIGURACOES DO SISTEMA")
    print("=" * 60)
    
    print("\nTELESCOPIO - Seestar S50:")
    print(f"  Distancia focal: {FOCAL_LENGTH_MM} mm")
    print(f"  Tamanho do pixel: {PIXEL_SIZE_UM} um")
    print(f"  Resolucao: {SENSOR_WIDTH_PX} x {SENSOR_HEIGHT_PX} px")
    print(f"  Escala de placa: {escala_arcsec_px():.2f} arcsec/px")
    print(f"  Campo de visao: {fov_width_arcmin():.1f}' x {fov_height_arcmin():.1f}'")
    
    print("\nVISUALIZACAO:")
    print(f"  Percentis: {CONFIG_VISUALIZACAO['low_percent']}% - {CONFIG_VISUALIZACAO['high_percent']}%")
    print(f"  CLAHE: {CONFIG_VISUALIZACAO['use_clahe']}")
    
    print("\nDETECCAO DE ESTRELAS:")
    print(f"  FWHM: {CONFIG_DETECCAO['fwhm']}")
    print(f"  Threshold: {CONFIG_DETECCAO['threshold']}-sigma")
    print(f"  N brightest: {CONFIG_DETECCAO['n_brightest']}")
    
    print("\nPLATE SOLVING:")
    print(f"  Indices: {CONFIG_PLATE_SOLVE['indices_dir']}")
    print(f"  Escala: {CONFIG_PLATE_SOLVE['scale_low']}° - {CONFIG_PLATE_SOLVE['scale_high']}°")
    print(f"  Timeout: {CONFIG_PLATE_SOLVE['timeout']}s")
    
    print("\n" + "=" * 60)
