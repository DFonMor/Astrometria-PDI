"""
constants.py - Parâmetros constantes do sistema de astrometria

Este arquivo contém todas as configurações fixas do projeto:
    - Parâmetros do telescópio Seestar S50
    - Configurações do algoritmo (detecção, visualização, plate solving)
    - Parâmetros para leitura dos índices do astrometry.net

Autor: Eduardo Fonseca Morato
Contato: morato@alunos.utfpr.edu.br
Disciplina: ELTD2 - Processamento de Imagens UTFPR
"""

# ============================================================================
# PARÂMETROS DO TELESCÓPIO - SEESTAR S50
# ============================================================================

# Constantes físicas do equipamento
FOCAL_LENGTH_MM = 250.0          # Distância focal [mm]
PIXEL_SIZE_UM = 2.9              # Tamanho do pixel [micrômetros]
SENSOR_WIDTH_PX = 1920           # Largura do sensor [pixels]
SENSOR_HEIGHT_PX = 1080          # Altura do sensor [pixels]

# Constantes derivadas (cálculos automáticos)
def escala_arcsec_px():
    """Escala de placa em arcsegundos por pixel"""
    return 206.265 * PIXEL_SIZE_UM / FOCAL_LENGTH_MM

def fov_width_arcmin():
    """Campo de visão horizontal em minutos de arco"""
    return (escala_arcsec_px() * SENSOR_WIDTH_PX) / 60.0

def fov_height_arcmin():
    """Campo de visão vertical em minutos de arco"""
    return (escala_arcsec_px() * SENSOR_HEIGHT_PX) / 60.0


# ============================================================================
# CONFIGURAÇÃO DE VISUALIZAÇÃO (melhorar_imagem)
# ============================================================================

CONFIG_VISUALIZACAO = {
    'low_percent': 5,          # Percentil inferior (5 = mais contraste)
    'high_percent': 90,        # Percentil superior (90 = mais contraste)
    'use_clahe': False,        # True para usar CLAHE (contraste local)
    'clahe_clip_limit': 0.02,  # Limite de contraste do CLAHE
}


# ============================================================================
# CONFIGURAÇÃO DE DETECÇÃO DE ESTRELAS (detectar_estrelas)
# ============================================================================

CONFIG_DETECCAO = {
    'fwhm': 3.0,               # Largura típica da estrela (FWHM) em pixels
    'threshold': 3.0,          # Limiar em sigma (3 = 3-sigma)
    'n_brightest': 50,         # Número máximo de estrelas a retornar
    'sharpness_range': (-1.0, 1.0),  # Faixa de nitidez
    'roundness_range': (-1.0, 1.0),  # Faixa de circularidade
    'box_size': 50,            # Tamanho da grade para estimativa de fundo
    'filter_size': 3,          # Tamanho do filtro para estimativa de fundo
}


# ============================================================================
# CONFIGURAÇÃO DE PLATE SOLVING (plate_solve)
# ============================================================================

CONFIG_PLATE_SOLVE = {
    'indices_dir': '/home/dell/Astrometria-PDI/data',  # Caminho para os índices
    'scale_low': 0.3,          # Limite inferior da escala (graus)
    'scale_high': 1.0,         # Limite superior da escala (graus)
    'width': 1920,             # Largura da imagem (pixels)
    'height': 1080,            # Altura da imagem (pixels)
    'timeout': 120,            # Tempo máximo de execução (segundos)
    'verbose': True,           # Exibir mensagens detalhadas
}


# ============================================================================
# CONFIGURAÇÃO DE SAÍDA (exibir_resultado)
# ============================================================================

CONFIG_SAIDA = {
    'salvar_imagens': True,    # Salvar imagens em disco
    'pasta_saida': 'resultados',  # Pasta para salvar os resultados
    'mostrar_imagens': True,   # Exibir imagens na tela
    'max_estrelas_mostrar': 50, # Número máximo de estrelas a marcar
}


# ============================================================================
# PARA TESTE (se rodar o arquivo diretamente)
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("CONFIGURAÇÕES DO SISTEMA")
    print("=" * 60)
    
    print("\n📷 TELESCÓPIO - Seestar S50:")
    print(f"  Distância focal: {FOCAL_LENGTH_MM} mm")
    print(f"  Tamanho do pixel: {PIXEL_SIZE_UM} µm")
    print(f"  Resolução: {SENSOR_WIDTH_PX} × {SENSOR_HEIGHT_PX} px")
    print(f"  Escala de placa: {escala_arcsec_px():.2f} arcsec/px")
    print(f"  Campo de visão: {fov_width_arcmin():.1f}' × {fov_height_arcmin():.1f}'")
    
    print("\n🎨 VISUALIZAÇÃO:")
    print(f"  Percentis: {CONFIG_VISUALIZACAO['low_percent']}% - {CONFIG_VISUALIZACAO['high_percent']}%")
    print(f"  CLAHE: {CONFIG_VISUALIZACAO['use_clahe']}")
    
    print("\n⭐ DETECÇÃO DE ESTRELAS:")
    print(f"  FWHM: {CONFIG_DETECCAO['fwhm']}")
    print(f"  Threshold: {CONFIG_DETECCAO['threshold']}-sigma")
    print(f"  N brightest: {CONFIG_DETECCAO['n_brightest']}")
    
    print("\n🔭 PLATE SOLVING:")
    print(f"  Índices: {CONFIG_PLATE_SOLVE['indices_dir']}")
    print(f"  Escala: {CONFIG_PLATE_SOLVE['scale_low']}° - {CONFIG_PLATE_SOLVE['scale_high']}°")
    print(f"  Timeout: {CONFIG_PLATE_SOLVE['timeout']}s")
    
    print("\n" + "=" * 60)
