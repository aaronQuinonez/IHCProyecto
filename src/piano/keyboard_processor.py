#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo centralizado para procesar el teclado virtual
Maneja detección de manos, triangulación 3D, y reproducción de audio
"""

import numpy as np
from collections import deque
from src.config.app_config import AppConfig


class KeyboardProcessor:
    """
    Clase que centraliza todo el procesamiento del teclado virtual:
    - Detección de manos
    - Triangulación 3D de profundidad
    - Mapeo de contactos con teclas
    - Reproducción de audio
    """
    
    def __init__(self, keyboard_mapper, angler, depth_estimator, 
                 synth, octave_base, keyboard_total_keys, camera_separation,
                 use_stereo_calibration=True):
        """
        Args:
            keyboard_mapper: Instancia de KeyboardMap
            angler: Instancia de Frame_Angles para triangulación
            depth_estimator: DepthEstimator para cálculo 3D (opcional)
            synth: Sintetizador FluidSynth
            octave_base: Nota base (MIDI)
            keyboard_total_keys: Número total de teclas
            camera_separation: Separación entre cámaras (cm)
            use_stereo_calibration: Usar calibración estéreo si está disponible
        """
        self.km = keyboard_mapper
        self.angler = angler
        self.depth_estimator = depth_estimator
        self.synth = synth
        self.octave_base = octave_base
        self.keyboard_total_keys = keyboard_total_keys
        self.camera_separation = camera_separation
        self.use_stereo_calibration = use_stereo_calibration and depth_estimator is not None
        
        # Buffer de suavizado temporal para reducir jitter
        if self.depth_estimator and not hasattr(self.depth_estimator, 'finger_position_history'):
            self.depth_estimator.finger_position_history = {}
        
    def process_and_play(self, frame_left, frame_right, virtual_keyboard, 
                        hand_detector_left, hand_detector_right, 
                        game_mode=False, rhythm_game=None):
        """
        Procesa ambos frames, detecta manos, calcula profundidad y reproduce audio
        
        Args:
            frame_left: Frame de cámara izquierda
            frame_right: Frame de cámara derecha
            virtual_keyboard: Instancia de VirtualKeyboard
            hand_detector_left: Detector de manos izquierdo
            hand_detector_right: Detector de manos derecho
            game_mode: Si está en modo juego (rhythm game)
            rhythm_game: Instancia de RhythmGame (si game_mode=True)
            
        Returns:
            tuple: (frame_left, frame_right) con dibujos del teclado y manos
        """
        # === PASO 1: Detectar manos (sin dibujar todavía) ===
        hands_detected_left = hand_detector_left.findHands(frame_left)
        hands_detected_right = hand_detector_right.findHands(frame_right)
        
        hands_left_image = []
        fingers_left_image = []
        hands_right_image = []
        fingers_right_image = []
        
        if hands_detected_left:
            hands_left_image, fingers_left_image = hand_detector_left.getFingerTipsPos()
        
        if hands_detected_right:
            hands_right_image, fingers_right_image = hand_detector_right.getFingerTipsPos()
        
        # === PASO 2: Dibujar teclado PRIMERO (debajo de las manos) ===
        virtual_keyboard.draw_virtual_keyboard(frame_left)
        
        # === PASO 3: Si es modo juego, dibujar notas cayendo ===
        if game_mode and rhythm_game:
            rhythm_game.update()
            frame_left = rhythm_game.draw(
                frame_left,
                virtual_keyboard.kb_x0,
                virtual_keyboard.kb_x1,
                virtual_keyboard.white_key_width
            )
        
        # === PASO 4: Dibujar manos AL FINAL (encima del teclado y notas) ===
        if hands_detected_left:
            hand_detector_left.drawHands(frame_left)
            hand_detector_left.drawTips(frame_left)
        
        if hands_detected_right:
            hand_detector_right.drawHands(frame_right)
            hand_detector_right.drawTips(frame_right)
        
        # === PASO 5: Procesar contactos con teclado si hay dedos detectados ===
        if len(fingers_left_image) > 0 and len(fingers_right_image) > 0:
            finger_depths_dict = {}
            
            # Rectificar imágenes si usamos calibración estéreo
            if self.use_stereo_calibration and self.depth_estimator:
                try:
                    frame_left_rect, frame_right_rect = self.depth_estimator.rectify_images(
                        frame_left, frame_right
                    )
                except:
                    frame_left_rect, frame_right_rect = frame_left, frame_right
            else:
                frame_left_rect, frame_right_rect = frame_left, frame_right
            
            # Calcular profundidades 3D para cada par de dedos
            for finger_left in fingers_left_image:
                for finger_right in fingers_right_image:
                    # Verificar si son el mismo dedo (mismo hand_id y tip_id)
                    if finger_left[0] == finger_right[0] and finger_left[1] == finger_right[1]:
                        depth_corrected = self._calculate_depth(finger_left, finger_right)
                        
                        # Guardar profundidad
                        finger_id = (finger_left[0], finger_left[1])
                        finger_depths_dict[finger_id] = depth_corrected
            
            # Obtener mapa de teclas presionadas
            on_map, off_map = self.km.get_kayboard_map(
                virtual_keyboard=virtual_keyboard,
                fingertips_pos=fingers_left_image,
                finger_depths=finger_depths_dict,
                keyboard_n_key=self.keyboard_total_keys
            )
            
            # === PASO 6: Reproducir audio según el modo ===
            if game_mode and rhythm_game:
                # Modo juego: verificar aciertos
                active_keys = np.where(on_map)[0]
                for k_pos in active_keys:
                    hit_result = rhythm_game.check_hit(k_pos)
                    if hit_result:
                        self.synth.noteon(
                            chan=0,
                            key=virtual_keyboard.note_from_key(k_pos) + self.octave_base,
                            vel=127 * 2 // 3
                        )
            else:
                # Modo libre/songs: reproducir todas las teclas
                if np.any(on_map):
                    for k_pos, on_key in enumerate(on_map):
                        if on_key:
                            self.synth.noteon(
                                chan=0,
                                key=virtual_keyboard.note_from_key(k_pos) + self.octave_base,
                                vel=127 * 2 // 3
                            )
                
                if np.any(off_map):
                    for k_pos, off_key in enumerate(off_map):
                        if off_key:
                            self.synth.noteoff(
                                chan=0,
                                key=virtual_keyboard.note_from_key(k_pos) + self.octave_base
                            )
        
        # === PASO 7: Dibujar centros de cámara ===
        self.angler.frame_add_crosshairs(frame_left)
        self.angler.frame_add_crosshairs(frame_right)
        
        return frame_left, frame_right
    
    def _calculate_depth(self, finger_left, finger_right):
        """
        Calcula la profundidad 3D de un dedo usando triangulación
        
        Args:
            finger_left: Datos del dedo en cámara izquierda (hand_id, tip_id, x, y)
            finger_right: Datos del dedo en cámara derecha (hand_id, tip_id, x, y)
            
        Returns:
            float: Profundidad corregida en cm
        """
        if self.use_stereo_calibration and self.depth_estimator:
            # ========== MÉTODO PRECISO: Calibración Estéreo ==========
            try:
                point_left = (finger_left[2], finger_left[3])
                point_right = (finger_right[2], finger_right[3])
                
                # Triangular con calibración completa
                result_3d = self.depth_estimator.triangulate_point(point_left, point_right)
                
                if result_3d is not None:
                    X_raw, Y_raw, Z_raw = result_3d
                    
                    # APLICAR FACTOR DE CORRECCIÓN DE PROFUNDIDAD (0.74)
                    # Basado en mediciones empíricas (43cm real / 58cm medido)
                    DEPTH_CORRECTION_FACTOR = 0.74
                    X_local = X_raw
                    Y_local = Y_raw
                    Z_local = Z_raw * DEPTH_CORRECTION_FACTOR
                    
                    # APLICAR SUAVIZADO TEMPORAL para reducir jitter
                    finger_id = (finger_left[0], finger_left[1])
                    
                    # Inicializar buffer de suavizado si no existe
                    if finger_id not in self.depth_estimator.finger_position_history:
                        self.depth_estimator.finger_position_history[finger_id] = deque(maxlen=5)
                    
                    # Agregar posición actual al buffer
                    self.depth_estimator.finger_position_history[finger_id].append(
                        (X_local, Y_local, Z_local)
                    )
                    
                    # Calcular promedio de últimas 5 posiciones
                    if len(self.depth_estimator.finger_position_history[finger_id]) > 0:
                        history = np.array(list(self.depth_estimator.finger_position_history[finger_id]))
                        X_local, Y_local, Z_local = np.mean(history, axis=0)
                    
                    return Z_local  # Profundidad = coordenada Z
                else:
                    # Fallback si falla triangulación
                    return 0
            except Exception as e:
                # Fallback al método de ángulos si hay error
                return self._triangulate_angles(finger_left, finger_right)
        else:
            # ========== MÉTODO FALLBACK: Triangulación por ángulos ==========
            return self._triangulate_angles(finger_left, finger_right)
    
    def _triangulate_angles(self, finger_left, finger_right):
        """
        Triangulación usando ángulos (método fallback)
        
        Args:
            finger_left: Datos del dedo en cámara izquierda
            finger_right: Datos del dedo en cámara derecha
            
        Returns:
            float: Profundidad corregida en cm
        """
        # Obtener ángulos desde los centros de cámara
        xlangle, ylangle = self.angler.angles_from_center(
            x=finger_left[2], y=finger_left[3],
            top_left=True, degrees=True
        )
        xrangle, yrangle = self.angler.angles_from_center(
            x=finger_right[2], y=finger_right[3],
            top_left=True, degrees=True
        )
        
        # Triangular
        X_local, Y_local, Z_local, D_local = self.angler.location(
            self.camera_separation,
            (xlangle, ylangle),
            (xrangle, yrangle),
            center=True,
            degrees=True
        )
        
        # Normalización de ángulo
        delta_y = (0.006509695290859 * X_local * X_local + 
                  0.039473684210526 * -1 * X_local)
        depth_corrected = D_local - delta_y
        
        return depth_corrected
