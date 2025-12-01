#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuración centralizada para visión estereoscópica
Contiene todos los parámetros de hardware y calibración

@author: mherrera
"""


class StereoConfig:
    """Clase de configuración para el sistema estéreo"""
    
    # ==================== CÁMARAS ====================
    LEFT_CAMERA_SOURCE = 1          # ID de cámara izquierda
    RIGHT_CAMERA_SOURCE = 2         # ID de cámara derecha
    PIXEL_WIDTH = 640               # Ancho en píxeles
    PIXEL_HEIGHT = 480              # Alto en píxeles
    FRAME_RATE = 30                 # FPS objetivo
    
    # ==================== CALIBRACIÓN ÓPTICA ====================
    # Logi C920s HD Pro Webcam
    CAMERA_H_FOV = 70.42            # Campo de visión horizontal (grados)
    CAMERA_V_FOV = 43.3             # Campo de visión vertical (grados)
    H_FOV_RECTIFICATION = 21.42     # Corrección de FoV horizontal
    V_FOV_RECTIFICATION = (CAMERA_V_FOV * H_FOV_RECTIFICATION / CAMERA_H_FOV)
    
    # Ángulos efectivos después de corrección
    ANGLE_WIDTH = CAMERA_H_FOV - H_FOV_RECTIFICATION
    ANGLE_HEIGHT = CAMERA_V_FOV - V_FOV_RECTIFICATION
    
    # ==================== GEOMETRÍA ESTÉREO ====================
    CAMERA_SEPARATION = 14.21       # Distancia entre cámaras (cm)
    VKB_CENTER_DISTANCE = 71        # Distancia del teclado virtual (cm)
    
    # ==================== DETECCIÓN DE PROFUNDIDAD ====================
    DEPTH_THRESHOLD = 2.5           # Umbral de profundidad para presión (cm)
                                     # Rango recomendado: 2.0-4.0 cm
    
    # ==================== PARÁMETROS DE DETECCIÓN ====================
    HAND_DETECTION_CONFIDENCE = 0.75  # Confianza para detectar mano
    HAND_TRACKING_CONFIDENCE = 0.5    # Confianza para rastrear mano
    MAX_HANDS = 2                     # Máximo de manos a detectar
    
    # ==================== UI ====================
    CAMERA_IN_FRONT_OF_YOU = True   # Vista frontal (True) o lateral (False)
    DISPLAY_DASHBOARD_DEFAULT = False  # Mostrar dashboard por defecto
    
    # ==================== RUTA DE AUDIO ====================
    SOUNDFONT_PATH = r"C:\CodingWindows\IHC_Proyecto_Fork\IHCProyecto\utils\fluid\FluidR3_GM.sf2"
    
    # ==================== TECLADO VIRTUAL ====================
    KEYBOARD_TOTAL_KEYS = 24        # 2 octavas completas: C-B x2
    KEYBOARD_WHITE_KEYS = 14        # 7 teclas blancas por octava
    OCTAVE_BASE = 0                 # Octava base
    # ==================== MÉTODOS ====================
    
    @staticmethod
    def print_config():
        """Imprime la configuración actual en pantalla"""
        print("\n" + "="*60)
        print("CONFIGURACIÓN ESTÉREO ACTUAL")
        print("="*60)
        print(f"Cámaras: LEFT={StereoConfig.LEFT_CAMERA_SOURCE}, RIGHT={StereoConfig.RIGHT_CAMERA_SOURCE}")
        print(f"Resolución: {StereoConfig.PIXEL_WIDTH}x{StereoConfig.PIXEL_HEIGHT} @ {StereoConfig.FRAME_RATE}fps")
        print(f"FoV: H={StereoConfig.CAMERA_H_FOV}°, V={StereoConfig.CAMERA_V_FOV}°")
        print(f"Ángulos efectivos: W={StereoConfig.ANGLE_WIDTH:.2f}°, H={StereoConfig.ANGLE_HEIGHT:.2f}°")
        print(f"Separación cámaras: {StereoConfig.CAMERA_SEPARATION} cm")
        print(f"Distancia teclado: {StereoConfig.VKB_CENTER_DISTANCE} cm")
        print(f"Umbral profundidad: {StereoConfig.DEPTH_THRESHOLD} cm")
        print(f"Confianza detección: {StereoConfig.HAND_DETECTION_CONFIDENCE}")
        print(f"Confianza rastreo: {StereoConfig.HAND_TRACKING_CONFIDENCE}")
        print(f"Teclado: {StereoConfig.KEYBOARD_WHITE_KEYS} blancas + "
              f"{StereoConfig.KEYBOARD_TOTAL_KEYS - StereoConfig.KEYBOARD_WHITE_KEYS} negras")
        print("="*60 + "\n")
    
    @staticmethod
    def update_depth_threshold(new_threshold):
        """Actualiza dinámicamente el umbral de profundidad"""
        if new_threshold < 0.5:
            print("⚠ Umbral muy bajo (mínimo 0.5 cm)")
            return False
        if new_threshold > 10:
            print("⚠ Umbral muy alto (máximo 10 cm)")
            return False
        StereoConfig.DEPTH_THRESHOLD = new_threshold
        print(f"✓ Umbral actualizado a: {new_threshold:.2f} cm")
        return True
    
    @staticmethod
    def update_camera_sources(left_id, right_id):
        """Actualiza las fuentes de cámara"""
        StereoConfig.LEFT_CAMERA_SOURCE = left_id
        StereoConfig.RIGHT_CAMERA_SOURCE = right_id
        print(f"✓ Cámaras actualizadas: LEFT={left_id}, RIGHT={right_id}")
