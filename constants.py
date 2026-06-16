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

import numpy as np

# ============================================================================
# PARÂMETROS DO TELESCÓPIO - SEESTAR S50 
# ============================================================================

class Telescopio:
    """Parâmetros ópticos e do sensor do telescópio Seestar S50"""
    
    # Óptica
    FOCAL_LENGTH_MM = 250.0          # Distância focal [mm]
    APERTURE_MM = 50.0               # Abertura [mm]
    F_RATIO = 5.0                    # Relação focal (focal/abertura)
    
    # Sensor (Sony IMX462)
    PIXEL_SIZE_UM = 2.9              # Tamanho do pixel [micrômetros]
    SENSOR_WIDTH_PX = 1920           # Largura do sensor [pixels]
    SENSOR_HEIGHT_PX = 1080          # Altura do sensor [pixels]
    
    # Propriedades calculadas
    @staticmethod
    def escala_arcsec_px():
        """Escala de placa em arcsegundos por pixel"""
        # 206.265 = constante de conversão (radianos para arcsec × 1000)
        return 206.265 * Telescopio.PIXEL_SIZE_UM / Telescopio.FOCAL_LENGTH_MM
    
    @staticmethod
    def fov_width_arcmin():
        """Campo de visão horizontal em minutos de arco"""
        return (Telescopio.escala_arcsec_px() * Telescopio.SENSOR_WIDTH_PX) / 60.0
    
    @staticmethod
    def fov_height_arcmin():
        """Campo de visão vertical em minutos de arco"""
        return (Telescopio.escala_arcsec_px() * Telescopio.SENSOR_HEIGHT_PX) / 60.0
    
    @staticmethod
    def fov_width_deg():
        """Campo de visão horizontal em graus"""
        return Telescopio.fov_width_arcmin() / 60.0
    
    @staticmethod
    def fov_height_deg():
        """Campo de visão vertical em graus"""
        return Telescopio.fov_height_arcmin() / 60.0
