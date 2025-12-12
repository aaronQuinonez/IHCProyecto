#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestor de Calibración con PyQt6
Versión adaptada que usa interfaz PyQt6 en lugar de OpenCV directo
"""

import cv2
import numpy as np
import json
import sys
import time
from PyQt6.QtWidgets import QApplication, QInputDialog
from PyQt6.QtCore import QTimer, pyqtSignal, QObject
from pathlib import Path

from .calibration_config import CalibrationConfig
from .camera_calibrator import CameraCalibrator
from .stereo_calibrator import StereoCalibrator
from .depth_calibrator import DepthCalibrator
from .qt_calibration_window import CalibrationWindow
from .qt_config_dialog import CalibrationConfigDialog

# Importaciones de visión (ajustar rutas según estructura)
try:
    from ..vision.hand_detector import HandDetector
    from ..vision.depth_estimator import load_depth_estimator
except ImportError:
    # Fallback por si la estructura de directorios es diferente
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from vision.hand_detector import HandDetector
    from vision.depth_estimator import load_depth_estimator


class QtCalibrationManager(QObject):
    """
    Gestor de calibración que usa PyQt6 para la interfaz
    OpenCV solo se usa para captura y procesamiento
    """
    
    finished = pyqtSignal(bool)  # Señal cuando termina (éxito/fallo)
    
    def __init__(self, cam_left_id, cam_right_id, resolution=(1280, 720)):
        super().__init__()
        
        self.cam_left_id = cam_left_id
        self.cam_right_id = cam_right_id
        self.resolution = resolution
        
        # Parámetros del tablero (fijo: 8x8 = 7x7 esquinas)
        self.board_cols = 7
        self.board_rows = 7
        self.square_size_mm = CalibrationConfig.DEFAULT_SQUARE_SIZE_MM
        
        # Calibradores
        self.calibrator_left = None
        self.calibrator_right = None
        self.stereo_calibrator = None
        self.depth_calibrator = None
        
        # Herramientas de visión para Fase 3
        self.hand_detector = None
        self.depth_estimator = None
        
        # Ventana PyQt6
        self.window = CalibrationWindow(width=resolution[0], height=resolution[1])
        
        # Cámaras
        self.cap_left = None
        self.cap_right = None
        
        # Estado
        self.current_phase = "intro"
        self.current_camera = None
        self.photo_count = 0
        self.total_photos = CalibrationConfig.get_total_photos()
        self.pair_count = 0
        self.detection_frames = 0
        self.last_capture_time = 0
        
        # Timer para actualizar frames
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_frame)
        
        # Resultados
        self.calibration_data = {}
        
        # Conectar señales
        self.window.capture_requested.connect(self._on_capture)
        self.window.cancel_requested.connect(self._on_cancel)
        self.window.continue_requested.connect(self._on_continue)
        
        # Asegurar directorios
        CalibrationConfig.ensure_directories()
    
    def run_calibration(self, start_phase=None):
        """
        Inicia el proceso de calibración
        
        Args:
            start_phase: Ignorado, se usa el diálogo para determinar la fase
        """
        print("[DEBUG] run_calibration() iniciado")
        
        # Verificar qué fases están completas para habilitar opciones
        file_exists = CalibrationConfig.CALIBRATION_FILE.exists()
        has_phase1 = False
        has_phase2 = False
        if file_exists:
            try:
                with open(CalibrationConfig.CALIBRATION_FILE, 'r') as f:
                    prev_data = json.load(f)
                # Verifica que existan datos de Fase 1
                has_left = 'left_camera' in prev_data and 'camera_matrix' in prev_data['left_camera']
                has_right = 'right_camera' in prev_data and 'camera_matrix' in prev_data['right_camera']
                has_phase1 = has_left and has_right
                # Verifica que existan datos de Fase 2
                has_phase2 = 'stereo_config' in prev_data and prev_data['stereo_config'] is not None
            except Exception as e:
                print(f"[DEBUG] Error leyendo calibración previa: {e}")
        print(f"[DEBUG] Archivo existe: {file_exists}, has_phase1: {has_phase1}, has_phase2: {has_phase2}")
        
        # Procesar eventos pendientes antes de mostrar diálogo
        QApplication.processEvents()
        
        # ========== CONFIGURACIÓN DE TABLERO ==========
        # SIEMPRE pedir configuración al usuario para permitir recalibración
        dialog = CalibrationConfigDialog(
            default_rows=self.board_rows,
            default_cols=self.board_cols,
            default_size_mm=self.square_size_mm,
            enable_phase2=has_phase1,
            enable_phase3=has_phase2
        )
        
        print("[DEBUG] Diálogo de configuración creado, mostrando...")
        
        # Asegurar que el diálogo tenga foco y esté visible
        dialog.raise_()
        dialog.activateWindow()
        dialog.setFocus()
        
        # Procesar eventos para que el diálogo se muestre
        QApplication.processEvents()
        
        result = dialog.exec()
        print(f"[DEBUG] Resultado del diálogo de configuración: {result}")
        
        print(f"[DEBUG] dialog.exec() retornó: {result} (tipo: {type(result)})")
        
        if result:
            new_rows, new_cols, new_size_mm, selected_phase = dialog.get_values()
            print(f"[DEBUG] Valores del diálogo:")
            print(f"  - new_rows: {new_rows} (tipo: {type(new_rows)})")
            print(f"  - new_cols: {new_cols} (tipo: {type(new_cols)})")
            print(f"  - new_size_mm: {new_size_mm} (tipo: {type(new_size_mm)})")
            print(f"  - selected_phase: {selected_phase} (tipo: {type(selected_phase)})")
            print(f"✓ Configuración: {new_cols}x{new_rows}, {new_size_mm}mm - Iniciando en Fase {selected_phase}")

            # Cargar configuración previa si existe
            prev_config = None
            if CalibrationConfig.CALIBRATION_FILE.exists():
                try:
                    with open(CalibrationConfig.CALIBRATION_FILE, 'r') as f:
                        prev_data = json.load(f)
                        prev_config = prev_data.get('board_config', {})
                except Exception as e:
                    print(f"[DEBUG] No se pudo leer calibración previa: {e}")

            # Si el usuario cambió filas, columnas o tamaño de casilla, forzar recalibración completa
            if prev_config:
                prev_rows = prev_config.get('rows')
                prev_cols = prev_config.get('cols')
                prev_size = prev_config.get('square_size_mm')
                
                # Verificar si algún valor previo es None o si hay diferencias
                config_changed = False
                if prev_rows is None or prev_cols is None or prev_size is None:
                    # Si falta algún valor, considerar que cambió
                    config_changed = True
                else:
                    # Comparar valores
                    try:
                        config_changed = (prev_rows != new_rows) or (prev_cols != new_cols) or (abs(float(prev_size) - float(new_size_mm)) > 1e-3)
                    except (TypeError, ValueError):
                        # Si hay error en la conversión, considerar que cambió
                        config_changed = True
                
                if config_changed:
                    print("[DEBUG] El usuario cambió el tamaño del tablero. Borrando calibración previa...")
                    try:
                        CalibrationConfig.CALIBRATION_FILE.unlink()
                        print("[DEBUG] Archivo de calibración eliminado.")
                    except Exception as e:
                        print(f"[DEBUG] No se pudo borrar calibración previa: {e}")
                    # Resetear flags
                    has_phase1 = False
                    has_phase2 = False

            self.board_rows = new_rows
            self.board_cols = new_cols
            self.square_size_mm = new_size_mm
        else:
            print("Cancelado por usuario en diálogo de configuración")
            self.finished.emit(False)
            return

        # Mostrar ventana
        self.window.show()

        # Verificar que selected_phase tiene un valor válido
        if selected_phase is None:
            print("[DEBUG] WARNING: selected_phase es None, usando fase 1 por defecto")
            selected_phase = 1

        # Iniciar según la fase seleccionada en el diálogo
        print(f"[DEBUG] Iniciando fase: {selected_phase}")
        if selected_phase == 3:
            print("\n✓ Iniciando directamente en Fase 3...")
            print("  Cargando Fase 1...")
            phase1_ok = self._load_phase1_calibration()
            print(f"  Fase 1 cargada: {phase1_ok}")
            if phase1_ok:
                print("  Cargando Fase 2...")
                phase2_ok = self._load_phase2_calibration()
                print(f"  Fase 2 cargada: {phase2_ok}")
                if phase2_ok:
                    print("  Iniciando Fase 3...")
                    self._start_phase3()
                else:
                    print("✗ Error al cargar Fase 2, volviendo a Fase 1")
                    self._start_intro()
            else:
                print("✗ Error al cargar Fase 1, volviendo a Fase 1")
                self._start_intro()
        elif selected_phase == 2:
            print("\n✓ Iniciando directamente en Fase 2...")
            phase1_ok = self._load_phase1_calibration()
            if phase1_ok:
                # Verificar que los calibradores están correctamente inicializados
                if self.calibrator_left and self.calibrator_left.is_calibrated and \
                   self.calibrator_right and self.calibrator_right.is_calibrated:
                    self._load_board_config()
                    print("✓ Calibración previa de Fase 1 válida. Iniciando Fase 2...")
                    # Reiniciar timer y estado por seguridad
                    if self.timer.isActive():
                        self.timer.stop()
                    self.current_phase = None
                    self._start_phase2()
                else:
                    print("✗ Calibración previa de Fase 1 incompleta o inválida. Volviendo a Fase 1.")
                    self.window.set_status("No se encontró calibración previa válida de Fase 1. Debes completarla antes de Fase 2.", "#FF0000")
                    self._start_intro()
            else:
                print("✗ Error al cargar datos previos, volviendo a Fase 1")
                self.window.set_status("Error al cargar calibración previa. Debes completar Fase 1.", "#FF0000")
                self._start_intro()
        else:
            # Fase 1 (Default)
            self._start_intro()
    
    def _start_intro(self):
        """Muestra la pantalla de introducción"""
        self.current_phase = "intro"
        
        instructions = [
            f"Usaremos un tablero de ajedrez de <b>{self.board_cols+1}x{self.board_rows+1}</b>",
            f"Se detectarán <b>{self.board_cols}x{self.board_rows} esquinas internas</b>",
            f"Tamaño de cuadrado configurado: <b>{self.square_size_mm} mm</b>",
            "El proceso tiene 2 fases: calibración individual y calibración estéreo",
            "Prepara tu tablero y buena iluminación"
        ]
        
        self.window.show_intro_screen(
            "CALIBRACIÓN ESTEREOSCÓPICA - FASE 1",
            instructions
        )
        
        # Crear frames negros para visualización
        black_frame = np.zeros((self.resolution[1]//2, self.resolution[0]//2, 3), dtype=np.uint8)
        self.window.update_frames(black_frame, black_frame)
    
    def _on_continue(self):
        """Maneja el botón de continuar"""
        if self.current_phase == "intro":
            self._start_camera_calibration("left")
        elif self.current_phase == "left_complete":
            self._start_camera_calibration("right")
        elif self.current_phase == "phase1_complete":
            self._start_phase2()
        elif self.current_phase == "stereo_intro":
            self._on_stereo_continue()
        elif self.current_phase == "phase2_complete":
            self._start_phase3()
        elif self.current_phase == "depth_intro":
            self._start_depth_capture()
        elif self.current_phase == "phase3_complete":
            self._finish_calibration(True)
    
    def _start_camera_calibration(self, camera_name):
        """
        Inicia la calibración de una cámara individual
        
        Args:
            camera_name: 'left' o 'right'
        """
        self.current_camera = camera_name
        self.photo_count = 0
        
        # Determinar ID de cámara
        camera_id = self.cam_left_id if camera_name == "left" else self.cam_right_id
        display_name = "IZQUIERDA" if camera_name == "left" else "DERECHA"
        
        # Crear calibrador
        if camera_name == "left":
            self.calibrator_left = CameraCalibrator(
                camera_id=camera_id,
                camera_name=camera_name,
                board_size=(self.board_cols, self.board_rows),
                square_size_mm=self.square_size_mm
            )
            self.current_calibrator = self.calibrator_left
        else:
            self.calibrator_right = CameraCalibrator(
                camera_id=camera_id,
                camera_name=camera_name,
                board_size=(self.board_cols, self.board_rows),
                square_size_mm=self.square_size_mm
            )
            self.current_calibrator = self.calibrator_right
        
        # Mostrar estado de carga
        self.window.set_status(f"Iniciando cámara {display_name}...", "#FFA500")
        QApplication.processEvents()
        
        # Abrir cámara
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            print(f"✗ No se pudo abrir la cámara {camera_id}")
            self._finish_calibration(False)
            return
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
        cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
        
        # Warmup: Leer algunos frames para estabilizar
        for _ in range(5):
            cap.read()
            QApplication.processEvents()
        
        if camera_name == "left":
            self.cap_left = cap
        else:
            self.cap_right = cap
        
        # Actualizar UI
        self.current_phase = f"capture_{camera_name}"
        self.window.set_phase(self.current_phase, f"FASE 1 - CÁMARA {display_name}")
        self.window.update_progress(0, self.total_photos)
        
        # Mostrar primera instrucción
        cat_title, specific_instr, objective = CalibrationConfig.get_instruction_for_photo(0)
        self.window.show_capture_instructions(
            cat_title, specific_instr, objective, 0, self.total_photos
        )
        
        # Iniciar actualización de frames
        self.timer.start(33)  # ~30 FPS
    
    def _update_frame(self):
        """Actualiza los frames de las cámaras (llamado por timer)"""
        if self.current_phase.startswith("capture_"):
            self._update_single_camera_frame()
        elif self.current_phase == "stereo_capture":
            self._update_stereo_frame()
        elif self.current_phase == "depth_capture":
            self._update_depth_frame()
    
    def _update_single_camera_frame(self):
        """Actualiza frame para calibración de cámara individual"""
        camera_name = self.current_camera
        cap = self.cap_left if camera_name == "left" else self.cap_right
        
        if cap is None or not cap.isOpened():
            return
        
        ret, frame = cap.read()
        if not ret:
            return
        
        # Importar configuración estéreo
        from ..vision.stereo_config import StereoConfig

        # Aplicar transformación según configuración
        # IMPORTANTE: Debe coincidir con la transformación usada en las UIs
        if hasattr(StereoConfig, 'ROTATE_CAMERAS_180') and StereoConfig.ROTATE_CAMERAS_180:
            frame = cv2.flip(frame, -1)
        elif hasattr(StereoConfig, 'MIRROR_HORIZONTAL') and StereoConfig.MIRROR_HORIZONTAL:
            frame = cv2.flip(frame, 1)

        # Detectar tablero
        detected, corners, frame_overlay = self.current_calibrator.detect_chessboard(frame)
        
        # Guardar para captura
        self.last_detected = detected
        self.last_corners = corners
        self.last_frame = frame
        
        # Actualizar estado
        if detected:
            self.window.set_status("✓ Tablero detectado - Presiona CAPTURAR", "#00FF00")
            self.window.enable_capture(True)
        else:
            self.window.set_status("Buscando tablero...", "#FFA500")
            self.window.enable_capture(False)
        
        # Mostrar frame
        if camera_name == "left":
            self.window.update_frames(frame_left=frame_overlay)
        else:
            self.window.update_frames(frame_right=frame_overlay)
    
    def _on_capture(self):
        """Maneja el evento de captura"""
        if self.current_phase.startswith("capture_"):
            self._capture_single_photo()
        elif self.current_phase == "stereo_capture":
            self._capture_stereo_pair()
        elif self.current_phase == "depth_capture":
            self._capture_depth_measurement()
    
    def _capture_single_photo(self):
        """Captura una foto para calibración individual"""
        if not self.last_detected:
            return
        
        # Capturar imagen
        self.current_calibrator.capture_image(self.last_frame, self.last_corners)
        self.photo_count += 1
        
        print(f"✓ Foto {self.photo_count}/{self.total_photos} capturada")
        
        # Actualizar progreso
        self.window.update_progress(self.photo_count, self.total_photos)
        
        # Actualizar instrucciones para la siguiente foto
        if self.photo_count < self.total_photos:
            cat_title, specific_instr, objective = CalibrationConfig.get_instruction_for_photo(self.photo_count)
            self.window.show_capture_instructions(
                cat_title, specific_instr, objective, self.photo_count, self.total_photos
            )
        else:
            # Captura completa, procesar calibración
            self._process_single_camera_calibration()
    
    def _process_single_camera_calibration(self):
        """Procesa la calibración de la cámara actual"""
        self.timer.stop()
        
        # Cerrar cámara
        if self.current_camera == "left" and self.cap_left:
            self.cap_left.release()
            self.cap_left = None
        elif self.current_camera == "right" and self.cap_right:
            self.cap_right.release()
            self.cap_right = None
        
        # Ejecutar calibración
        print(f"\n{'='*70}")
        print(f"PROCESANDO CALIBRACIÓN - CÁMARA {self.current_camera.upper()}")
        print(f"{'='*70}")
        
        result = self.current_calibrator.calibrate()
        
        if result is None:
            print("✗ La calibración falló")
            self._finish_calibration(False)
            return
        
        # Mostrar resumen
        camera_display = "IZQUIERDA" if self.current_camera == "left" else "DERECHA"
        summary_html = f"<h3 style='color: #00FF00;'>CÁMARA {camera_display} CALIBRADA</h3>"
        summary_html += "<table style='width: 100%; color: #FFFFFF;'>"
        summary_html += f"<tr><td><b>Configuración:</b></td><td>{self.board_cols}x{self.board_rows} esquinas ({self.square_size_mm} mm)</td></tr>"
        summary_html += f"<tr><td><b>Imágenes capturadas:</b></td><td>{self.photo_count}</td></tr>"
        summary_html += f"<tr><td><b>Error de reproyección:</b></td><td>{result['reprojection_error']:.6f} px</td></tr>"
        summary_html += "</table>"
        summary_html += "<p style='color: #00FF00; margin-top: 20px;'><b>Presiona CONTINUAR o ENTER</b></p>"
        
        self.window.set_instructions(summary_html)
        self.window.set_status("✓ Calibración completada", "#00FF00")
        self.window.show_continue_button(True)
        
        # Actualizar fase
        if self.current_camera == "left":
            self.current_phase = "left_complete"
        else:
            self.current_phase = "phase1_complete"
            # Guardar Fase 1
            self._save_phase1_only()
    
    def _start_phase2(self):
        """Inicia la Fase 2: calibración estéreo"""
        # Reiniciar timer si está activo
        if self.timer.isActive():
            self.timer.stop()
        self.current_phase = "stereo_intro"
        instructions = [
            "Ahora calibraremos el <b>par estéreo</b>",
            "Coloca el tablero visible en <b>AMBAS cámaras</b> simultáneamente",
            "Necesitamos capturar <b>10 pares</b> de imágenes",
            "Varía la posición y orientación del tablero entre capturas",
            "Asegúrate de que el tablero esté completamente visible en ambas vistas"
        ]
        self.window.show_intro_screen(
            "FASE 2 - CALIBRACIÓN ESTÉREO",
            instructions
        )
        self.current_phase = "stereo_intro"
    
    def _on_stereo_continue(self):
        """Inicia la captura estéreo después de la introducción"""
        # Crear calibrador estéreo
        self.stereo_calibrator = StereoCalibrator(self.calibrator_left, self.calibrator_right)
        
        # Mostrar estado
        self.window.set_status("Iniciando cámaras estéreo...", "#FFA500")
        QApplication.processEvents()
        
        # Abrir ambas cámaras
        self.cap_left = cv2.VideoCapture(self.cam_left_id)
        self.cap_right = cv2.VideoCapture(self.cam_right_id)
        
        if not self.cap_left.isOpened() or not self.cap_right.isOpened():
            print("✗ Error al abrir las cámaras")
            self._finish_calibration(False)
            return
        
        # Configurar resolución y warmup
        for cap in [self.cap_left, self.cap_right]:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            # Warmup
            for _ in range(5):
                cap.read()
                QApplication.processEvents()
        
        # Actualizar UI
        self.current_phase = "stereo_capture"
        self.window.set_phase(self.current_phase, "FASE 2 - CALIBRACIÓN ESTÉREO")
        self.pair_count = 0
        self.window.show_stereo_instructions(0, 10)
        
        # Iniciar timer
        self.timer.start(33)
    
    def _update_stereo_frame(self):
        """Actualiza frames para calibración estéreo"""
        if not self.cap_left or not self.cap_right:
            return
        
        ret_left, frame_left = self.cap_left.read()
        ret_right, frame_right = self.cap_right.read()
        
        if not ret_left or not ret_right:
            return
        
        # Importar configuración estéreo
        from ..vision.stereo_config import StereoConfig

        # Aplicar transformación según configuración (igual que en UIs)
        if hasattr(StereoConfig, 'ROTATE_CAMERAS_180') and StereoConfig.ROTATE_CAMERAS_180:
            frame_left = cv2.flip(frame_left, -1)
            frame_right = cv2.flip(frame_right, -1)
        elif hasattr(StereoConfig, 'MIRROR_HORIZONTAL') and StereoConfig.MIRROR_HORIZONTAL:
            frame_left = cv2.flip(frame_left, 1)
            frame_right = cv2.flip(frame_right, 1)

        # Detectar tablero en ambas cámaras
        detected_both, corners_left, corners_right, display_left, display_right = \
            self.stereo_calibrator.detect_chessboard_pair(frame_left, frame_right)
        
        # Guardar para captura
        self.last_detected_stereo = detected_both
        self.last_corners_left = corners_left
        self.last_corners_right = corners_right
        self.last_frame_left = frame_left
        self.last_frame_right = frame_right
        
        # Contar frames de detección consecutivos
        if detected_both:
            self.detection_frames += 1
        else:
            self.detection_frames = 0
        
        # Actualizar estado
        current_time = time.time()
        can_capture = (current_time - self.last_capture_time) > 1.0
        
        if detected_both and self.detection_frames >= 5 and can_capture:
            self.window.set_status("✓ Tablero detectado en AMBAS - Presiona CAPTURAR", "#00FF00")
            self.window.enable_capture(True)
        elif detected_both:
            self.window.set_status(f"Estabilizando... {self.detection_frames}/5", "#00C8FF")
            self.window.enable_capture(False)
        else:
            self.window.set_status("Buscando tablero en ambas cámaras...", "#FFA500")
            self.window.enable_capture(False)
        
        # Mostrar frames
        self.window.update_frames(display_left, display_right)
    
    def _capture_stereo_pair(self):
        """Captura un par estéreo"""
        if not self.last_detected_stereo or self.detection_frames < 5:
            return
        
        # Capturar par
        self.stereo_calibrator.capture_stereo_pair(
            self.last_frame_left, self.last_frame_right,
            self.last_corners_left, self.last_corners_right
        )
        self.pair_count += 1
        
        print(f"✓ Par {self.pair_count} capturado")
        
        # Actualizar progreso
        self.window.show_stereo_instructions(self.pair_count, 10)
        
        # Resetear detección
        self.detection_frames = 0
        self.last_capture_time = time.time()
        
        # Si tenemos suficientes pares, finalizar automáticamente
        if self.pair_count >= 10:
            self._on_stereo_complete()
    
    def _on_stereo_complete(self):
        """Procesa la calibración estéreo"""
        self.timer.stop()
        
        # Cerrar cámaras
        if self.cap_left:
            self.cap_left.release()
            self.cap_left = None
        if self.cap_right:
            self.cap_right.release()
            self.cap_right = None
        
        # Ejecutar calibración estéreo
        print("\n⏳ Procesando calibración estéreo...")
        stereo_result = self.stereo_calibrator.calibrate_stereo_pair()
        
        if stereo_result is None:
            print("✗ Error en calibración estéreo")
            self._finish_calibration(False)
            return
        
        # Calcular rectificación
        print("⏳ Calculando parámetros de rectificación...")
        self.stereo_calibrator.compute_rectification()
        
        # Recopilar datos finales
        self._compile_calibration_data()
        
        # Guardar
        self._save_calibration()
        
        # Mostrar resumen
        summary_data = {
            'board_config': f"{self.board_cols}x{self.board_rows} ({self.square_size_mm} mm)",
            'left_error': self.calibrator_left.reprojection_error,
            'right_error': self.calibrator_right.reprojection_error,
            'stereo_error': self.stereo_calibrator.stereo_error,
            'baseline': np.linalg.norm(self.stereo_calibrator.T) * 100
        }
        
        self.window.show_summary_screen(summary_data)
        self.current_phase = "phase2_complete"

    def _start_phase3(self):
        """Inicia la Fase 3: calibración de profundidad"""
        self.current_phase = "depth_intro"
        
        instructions = [
            "Finalmente, calibraremos la <b>distancia del teclado</b>",
            "Pon tu <b>mano</b> en el lugar donde tocarás las teclas",
            "Mantén la mano <b>apoyada</b> sobre el teclado/mesa",
            "El sistema medirá la distancia automáticamente",
            "Capturaremos <b>5 muestras</b> para mayor precisión"
        ]
        
        self.window.show_intro_screen(
            "FASE 3 - CALIBRACIÓN DE DISTANCIA",
            instructions
        )
    
    def _start_depth_capture(self):
        """Inicia la captura de profundidad simplificada"""
        try:
            # Inicializar componentes de visión
            if self.hand_detector is None:
                self.window.set_status("Cargando detector de manos...", "#FFA500")
                QApplication.processEvents()
                self.hand_detector = HandDetector(maxHands=2)
            
            if self.depth_estimator is None:
                self.window.set_status("Cargando estimador de profundidad...", "#FFA500")
                QApplication.processEvents()
                # Cargar estimador base (sin calibración fina aún)
                self.depth_estimator = load_depth_estimator()
            
            # Inicializar calibrador de profundidad
            self.depth_calibrator = DepthCalibrator(self.depth_estimator)
            
            # Configurar número de muestras (simplificado)
            self.keyboard_samples_needed = 5
            self.keyboard_samples_collected = 0

            # Mostrar estado
            self.window.set_status("Iniciando cámaras...", "#FFA500")
            QApplication.processEvents()
            
            # Abrir cámaras si están cerradas
            if self.cap_left is None:
                self.cap_left = cv2.VideoCapture(self.cam_left_id)
                self.cap_left.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
                self.cap_left.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
                # Warmup
                for _ in range(5):
                    self.cap_left.read()
                    QApplication.processEvents()
                
            if self.cap_right is None:
                self.cap_right = cv2.VideoCapture(self.cam_right_id)
                self.cap_right.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
                self.cap_right.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
                # Warmup
                for _ in range(5):
                    self.cap_right.read()
                    QApplication.processEvents()
                
            if not self.cap_left.isOpened() or not self.cap_right.isOpened():
                print("✗ Error al abrir las cámaras para profundidad")
                self._finish_calibration(False)
                return
                
            # Actualizar UI
            self.current_phase = "depth_capture"
            self.window.set_phase(self.current_phase, "FASE 3 - DISTANCIA DEL TECLADO")
            self.window.set_status("Pon tu mano sobre el teclado y presiona ESPACIO o CAPTURAR", "#00BFFF")
            self.window.set_instructions(
                f"<b>Muestra {self.keyboard_samples_collected + 1} de {self.keyboard_samples_needed}</b><br>"
                "Mantén la mano apoyada en el plano del teclado<br>"
                "<span style='color: #FFD700;'>Nota: El valor mostrado puede parecer incorrecto, es normal</span>"
            )
            self.window.show_continue_button(False)  # Mostrar botón de captura, no continuar
            self.window.enable_capture(True)  # Habilitar captura desde el inicio
            
            # Iniciar timer
            if not self.timer.isActive():
                self.timer.start(33)
                
        except Exception as e:
            print(f"✗ Error crítico al iniciar Fase 3: {e}")
            import traceback
            traceback.print_exc()
            self.window.set_status(f"Error: {str(e)}", "#FF0000")
            self._finish_calibration(False)

    def _update_depth_frame(self):
        """Actualiza frame para calibración de profundidad"""
        if not self.cap_left or not self.cap_right:
            return
            
        ret_left, frame_left = self.cap_left.read()
        ret_right, frame_right = self.cap_right.read()
        
        if not ret_left or not ret_right:
            return
        
        # Importar configuración estéreo
        from ..vision.stereo_config import StereoConfig

        # Aplicar transformación según configuración (igual que en UIs)
        if hasattr(StereoConfig, 'ROTATE_CAMERAS_180') and StereoConfig.ROTATE_CAMERAS_180:
            frame_left = cv2.flip(frame_left, -1)
            frame_right = cv2.flip(frame_right, -1)
        elif hasattr(StereoConfig, 'MIRROR_HORIZONTAL') and StereoConfig.MIRROR_HORIZONTAL:
            frame_left = cv2.flip(frame_left, 1)
            frame_right = cv2.flip(frame_right, 1)

        # Copias para visualización
        display_left = frame_left.copy()
        display_right = frame_right.copy()
        
        # Detectar manos
        found_left = self.hand_detector.findHands(display_left)
        landmarks_left = None
        if found_left and self.hand_detector.results.multi_hand_landmarks:
            landmarks_left = self.hand_detector.results.multi_hand_landmarks[0]
            self.hand_detector.drawHands(display_left)
            
        found_right = self.hand_detector.findHands(display_right)
        landmarks_right = None
        if found_right and self.hand_detector.results.multi_hand_landmarks:
            landmarks_right = self.hand_detector.results.multi_hand_landmarks[0]
            self.hand_detector.drawHands(display_right)
            
        # Calcular profundidad si hay manos en ambas
        self.last_depth_value = None
        
        if landmarks_left and landmarks_right:
            depth = self.depth_calibrator.calculate_depth(landmarks_left, landmarks_right)
            
            if depth is not None and depth > 0:
                self.last_depth_value = depth
                self.window.set_status(
                    f"✓ Mano detectada - Distancia: {depth:.1f} cm - ¡PRESIONA ESPACIO o CAPTURAR!", 
                    "#00FF00"
                )
                self.window.enable_capture(True)
            elif depth is not None:
                # Profundidad negativa o cero - problema de triangulación
                self.last_depth_value = abs(depth) if depth != 0 else 50  # Valor temporal
                self.window.set_status(
                    f"⚠ Distancia estimada: {abs(depth):.1f} cm - Puedes capturar", 
                    "#FFA500"
                )
                self.window.enable_capture(True)
            else:
                self.window.set_status("Calculando profundidad...", "#FFA500")
                self.window.enable_capture(False)
        else:
            status_msg = "Muestra tu mano en "
            if not landmarks_left:
                status_msg += "CÁMARA IZQUIERDA "
            if not landmarks_right:
                status_msg += "CÁMARA DERECHA"
            self.window.set_status(status_msg, "#FFA500")
            self.window.enable_capture(False)
            
        # Guardar landmarks para captura
        self.last_landmarks_left = landmarks_left
        self.last_landmarks_right = landmarks_right
        
        # Mostrar frames
        self.window.update_frames(display_left, display_right)

    def _capture_depth_measurement(self):
        """Captura una muestra de la distancia del teclado"""
        if self.last_depth_value is None:
            return
            
        # Agregar muestra de distancia del teclado
        self.depth_calibrator.add_keyboard_distance_sample(self.last_depth_value)
        self.keyboard_samples_collected += 1
        
        # Actualizar UI
        if self.keyboard_samples_collected < self.keyboard_samples_needed:
            self.window.set_instructions(
                f"<b>Muestra {self.keyboard_samples_collected + 1} de {self.keyboard_samples_needed}</b><br>"
                f"Última medición: {self.last_depth_value:.1f} cm<br>"
                "Mantén la mano apoyada y presiona CAPTURAR"
            )
            self.window.set_status(f"✓ Muestra {self.keyboard_samples_collected} capturada", "#00FF00")
        else:
            # Finalizar
            self._finish_phase3()

    def _finish_phase3(self):
        """Finaliza la Fase 3"""
        self.timer.stop()
        
        # Calcular distancia del teclado
        keyboard_distance = self.depth_calibrator.calculate_keyboard_distance()
        
        if keyboard_distance is None:
            print("✗ Error en calibración de distancia")
            self._finish_calibration(False)
            return
        
        # Guardar la distancia del teclado
        self.depth_calibrator.save_keyboard_distance_only()
            
        # Recopilar datos para el resumen
        summary_data = {
            'board_config': f"{self.board_cols}x{self.board_rows} ({self.square_size_mm}mm)",
            'left_error': self.calibrator_left.reprojection_error if self.calibrator_left else 'N/A',
            'right_error': self.calibrator_right.reprojection_error if self.calibrator_right else 'N/A',
            'keyboard_distance': keyboard_distance
        }
        
        # Agregar datos estéreo si existen
        if self.stereo_calibrator:
            if hasattr(self.stereo_calibrator, 'stereo_error') and self.stereo_calibrator.stereo_error is not None:
                summary_data['stereo_error'] = self.stereo_calibrator.stereo_error
            
            if self.stereo_calibrator.T is not None:
                # T está en mm, convertir a cm
                baseline_mm = np.linalg.norm(self.stereo_calibrator.T)
                summary_data['baseline'] = baseline_mm / 10.0
        
        # Mostrar pantalla de resumen
        self.window.show_summary_screen(summary_data)
        self.current_phase = "phase3_complete"
    
    def _on_cancel(self):
        """Maneja la cancelación"""
        print("\n✗ Calibración cancelada por el usuario")
        self._cleanup()
        self.finished.emit(False)
        self.window.close()
    
    def _finish_calibration(self, success):
        """Finaliza el proceso de calibración"""
        self._cleanup()
        self.finished.emit(success)
        
        if success:
            print("\n🎉 ¡Calibración completa exitosa!")
        else:
            print("\n❌ La calibración no se completó.")
    
    def _cleanup(self):
        """Limpia recursos (cámaras, timers, etc.)"""
        if self.timer.isActive():
            self.timer.stop()
        
        if self.cap_left:
            self.cap_left.release()
            self.cap_left = None
        
        if self.cap_right:
            self.cap_right.release()
            self.cap_right = None
    
    # Métodos auxiliares (verificación, carga, guardado)
    
    def _check_phase1_complete(self):
        """Verifica si la Fase 1 está completa"""
        if not CalibrationConfig.CALIBRATION_FILE.exists():
            return False
        
        try:
            with open(CalibrationConfig.CALIBRATION_FILE, 'r') as f:
                data = json.load(f)
            
            has_left = 'left_camera' in data and 'camera_matrix' in data['left_camera']
            has_right = 'right_camera' in data and 'camera_matrix' in data['right_camera']
            
            return has_left and has_right
        except:
            return False
    
    def _check_phase2_complete(self):
        """Verifica si la Fase 2 está completa"""
        if not CalibrationConfig.CALIBRATION_FILE.exists():
            return False
        
        try:
            with open(CalibrationConfig.CALIBRATION_FILE, 'r') as f:
                data = json.load(f)
            
            has_stereo = 'stereo' in data and data['stereo'] is not None
            if has_stereo:
                return 'rotation_matrix' in data['stereo'] and 'translation_vector' in data['stereo']
            
            return False
        except:
            return False
    
    def _check_phase3_complete(self):
        """Verifica si la Fase 3 (Profundidad) está completa"""
        if not CalibrationConfig.CALIBRATION_FILE.exists():
            return False
        
        try:
            with open(CalibrationConfig.CALIBRATION_FILE, 'r') as f:
                data = json.load(f)
            
            # Verificar si existe configuración de profundidad
            if 'depth_config' in data and data['depth_config'] is not None:
                return 'coefficients' in data['depth_config']
            
            return False
        except:
            return False
    
    def _load_phase1_calibration(self):
        """Carga calibraciones de Fase 1"""
        try:
            with open(CalibrationConfig.CALIBRATION_FILE, 'r') as f:
                data = json.load(f)
            
            board_config = data['board_config']
            board_size = (board_config['cols'], board_config['rows'])
            square_size = board_config['square_size_mm']
            
            # Calibrador izquierdo
            self.calibrator_left = CameraCalibrator(
                camera_id=self.cam_left_id,
                camera_name='left',
                board_size=board_size,
                square_size_mm=square_size
            )
            self.calibrator_left.camera_matrix = np.array(data['left_camera']['camera_matrix'])
            self.calibrator_left.distortion_coeffs = np.array(data['left_camera']['distortion_coeffs'])
            self.calibrator_left.reprojection_error = data['left_camera']['reprojection_error']
            self.calibrator_left.image_size = (data['left_camera']['image_width'], data['left_camera']['image_height'])
            self.calibrator_left.obj_points = [None] * data['left_camera']['num_images']
            self.calibrator_left.is_calibrated = True
            
            # Calibrador derecho
            self.calibrator_right = CameraCalibrator(
                camera_id=self.cam_right_id,
                camera_name='right',
                board_size=board_size,
                square_size_mm=square_size
            )
            self.calibrator_right.camera_matrix = np.array(data['right_camera']['camera_matrix'])
            self.calibrator_right.distortion_coeffs = np.array(data['right_camera']['distortion_coeffs'])
            self.calibrator_right.reprojection_error = data['right_camera']['reprojection_error']
            self.calibrator_right.image_size = (data['right_camera']['image_width'], data['right_camera']['image_height'])
            self.calibrator_right.obj_points = [None] * data['right_camera']['num_images']
            self.calibrator_right.is_calibrated = True
            
            return True
        except Exception as e:
            print(f"✗ Error al cargar Fase 1: {e}")
            return False

    def _load_phase2_calibration(self):
        """Carga calibración estéreo de Fase 2"""
        try:
            with open(CalibrationConfig.CALIBRATION_FILE, 'r') as f:
                data = json.load(f)
            
            if 'stereo' not in data or data['stereo'] is None:
                return False
                
            # Crear calibrador estéreo si no existe
            if self.stereo_calibrator is None:
                self.stereo_calibrator = StereoCalibrator(self.calibrator_left, self.calibrator_right)
            
            # Cargar matrices
            stereo = data['stereo']
            self.stereo_calibrator.R = np.array(stereo['rotation_matrix'])
            self.stereo_calibrator.T = np.array(stereo['translation_vector'])
            self.stereo_calibrator.E = np.array(stereo['essential_matrix'])
            self.stereo_calibrator.F = np.array(stereo['fundamental_matrix'])
            
            # Cargar error si existe
            if 'rms_error' in stereo:
                self.stereo_calibrator.stereo_error = stereo['rms_error']
            
            # Calcular rectificación para tener mapas listos
            self.stereo_calibrator.compute_rectification()
            
            return True
        except Exception as e:
            print(f"✗ Error al cargar Fase 2: {e}")
            return False
    
    def _load_board_config(self):
        """Carga configuración del tablero"""
        try:
            with open(CalibrationConfig.CALIBRATION_FILE, 'r') as f:
                data = json.load(f)
            
            board_config = data['board_config']
            self.board_cols = board_config['cols']
            self.board_rows = board_config['rows']
            self.square_size_mm = board_config['square_size_mm']
        except:
            self.board_cols = 7
            self.board_rows = 7
            self.square_size_mm = CalibrationConfig.DEFAULT_SQUARE_SIZE_MM
    
    def _save_phase1_only(self):
        """Guarda solo Fase 1"""
        self.calibration_data = {
            'version': '2.0',
            'board_config': {
                'cols': self.board_cols,
                'rows': self.board_rows,
                'square_size_mm': self.square_size_mm
            },
            'left_camera': self.calibrator_left.get_calibration_data(),
            'right_camera': self.calibrator_right.get_calibration_data(),
            'stereo': None,
            'camera_ids': {
                'left': self.cam_left_id,
                'right': self.cam_right_id
            },
            'resolution': {
                'width': self.resolution[0],
                'height': self.resolution[1]
            }
        }
        
        with open(CalibrationConfig.CALIBRATION_FILE, 'w') as f:
            json.dump(self.calibration_data, f, indent=4)
        
        print(f"\n✓ Fase 1 guardada")
    
    def _compile_calibration_data(self):
        """Recopila todos los datos de calibración"""
        stereo_data = self.stereo_calibrator.get_calibration_data()
        left_camera_data = self.calibrator_left.get_calibration_data()
        right_camera_data = self.calibrator_right.get_calibration_data()
        
        # Agregar transformaciones al mundo
        if stereo_data and 'rotation_matrix' in stereo_data:
            left_camera_data['world_rotation'] = [[1.0, 0.0, 0.0],
                                                   [0.0, 1.0, 0.0],
                                                   [0.0, 0.0, 1.0]]
            left_camera_data['world_translation'] = [[0.0], [0.0], [0.0]]
            
            right_camera_data['world_rotation'] = stereo_data['rotation_matrix']
            right_camera_data['world_translation'] = stereo_data['translation_vector']
        
        self.calibration_data = {
            'version': '2.0',
            'board_config': {
                'cols': self.board_cols,
                'rows': self.board_rows,
                'square_size_mm': self.square_size_mm
            },
            'left_camera': left_camera_data,
            'right_camera': right_camera_data,
            'stereo': stereo_data,
            'camera_ids': {
                'left': self.cam_left_id,
                'right': self.cam_right_id
            },
            'resolution': {
                'width': self.resolution[0],
                'height': self.resolution[1]
            }
        }
    
    def _save_calibration(self):
        """Guarda calibración completa"""
        output_file = CalibrationConfig.CALIBRATION_FILE
        
        with open(output_file, 'w') as f:
            json.dump(self.calibration_data, f, indent=4)
        
        print(f"\n✓ Calibración guardada en: {output_file}")


def run_qt_calibration(cam_left_id=1, cam_right_id=2):
    """
    Función para ejecutar calibración con PyQt6
    
    Args:
        cam_left_id: ID de cámara izquierda
        cam_right_id: ID de cámara derecha
    
    Returns:
        bool: True si fue exitosa
    """
    from PyQt6.QtCore import QEventLoop
    
    # Reutilizar QApplication existente si ya hay una
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    print("[DEBUG] Creando QtCalibrationManager...")
    
    manager = QtCalibrationManager(
        cam_left_id=cam_left_id,
        cam_right_id=cam_right_id,
        resolution=(1280, 720)
    )
    
    # Variable para capturar resultado
    result = [False]
    finished_flag = [False]
    
    def on_finished(success):
        print(f"[DEBUG] Calibración terminada con resultado: {success}")
        result[0] = success
        finished_flag[0] = True
    
    manager.finished.connect(on_finished)
    
    print("[DEBUG] Ejecutando run_calibration()...")
    
    # Iniciar calibración
    manager.run_calibration()
    
    # Si ya terminó (usuario canceló el diálogo de configuración), retornar
    if finished_flag[0]:
        print("[DEBUG] Calibración terminó inmediatamente (diálogo cancelado)")
        return result[0]
    
    print("[DEBUG] Entrando en event loop local...")
    
    # Usar un event loop local que no afecte la app principal
    loop = QEventLoop()
    
    def exit_loop(success):
        loop.quit()
    
    manager.finished.connect(exit_loop)
    loop.exec()
    
    print(f"[DEBUG] Event loop terminado, resultado: {result[0]}")
    
    return result[0]


if __name__ == '__main__':
    print("\n" + "="*70)
    print("CALIBRACIÓN ESTEREOSCÓPICA CON PYQT6")
    print("="*70)
    
    success = run_qt_calibration(cam_left_id=1, cam_right_id=2)
    
    if success:
        print("\n🎉 ¡Calibración completa exitosa!")
    else:
        print("\n❌ La calibración no se completó.")
