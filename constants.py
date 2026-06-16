"""
constants.py - Parâmetros constantes do sistema de astrometria

Este arquivo contém todas as configurações fixas do projeto:
- Parâmetros do telescópio Seestar S50
- Configurações do algoritmo (detecção, extração, matching)
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
# PARA TESTE (se rodar o arquivo diretamente)
# ============================================================================

if __name__ == "__main__":
    print(f"Distância focal: {FOCAL_LENGTH_MM} mm")
    print(f"Tamanho do pixel: {PIXEL_SIZE_UM} µm")
    print(f"Resolução: {SENSOR_WIDTH_PX} × {SENSOR_HEIGHT_PX} px")
    print(f"Escala de placa: {escala_arcsec_px():.2f} arcsec/px")
    print(f"FOV: {fov_width_arcmin():.1f}' × {fov_height_arcmin():.1f}'")