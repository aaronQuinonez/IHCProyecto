#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ventana PyQt6 para lecciones de teoría musical
Embebe feed de cámaras OpenCV y muestra UI de la lección
"""

import sys
import cv2
import numpy as np
from typing import Optional
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QProgressBar, QTextEdit, QGridLayout, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap, QFont
from src.piano.keyboard_processor import KeyboardProcessor


class LessonWindow(QMainWindow):
    """
    Ventana principal para ejecutar lecciones de teoría musical.
    Muestra el feed de las cámaras y la UI de la lección en una sola ventana.
    """
    
    def __init__(self, lesson, camera_left, camera_right, synth, 
                 virtual_keyboard, hand_detector_left=None, hand_detector_right=None,
                 keyboard_mapper=None, angler=None, depth_estimator=None, octave_base=60,
                 keyboard_total_keys=24, camera_separation=9.07):
        super().__init__()
        
        self.lesson = lesson
        self.camera_left = camera_left
        self.camera_right = camera_right
        self.synth = synth
        self.virtual_keyboard = virtual_keyboard
        self.hand_detector_left = hand_detector_left
        self.hand_detector_right = hand_detector_right
        
        # Crear procesador de teclado centralizado
        if keyboard_mapper and angler:
            self.keyboard_processor = KeyboardProcessor(
                keyboard_mapper=keyboard_mapper,
                angler=angler,
                depth_estimator=depth_estimator,
                synth=synth,
                octave_base=octave_base,
                keyboard_total_keys=keyboard_total_keys,
                camera_separation=camera_separation
            )
        else:
            self.keyboard_processor = None
        
        self.continue_lesson = True
        self.timer = QTimer()
        
        # Configuración de ventana
        self.setWindowTitle(f"Teoría Musical - {lesson.name}")
        self.setMinimumSize(1400, 800)
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #000000;
            }
            QLabel#title {
                color: #ffffff;
                font-size: 20px;
                font-weight: bold;
                padding: 10px;
                background-color: #000000;
            }
            QLabel#subtitle {
                color: #ffffff;
                font-size: 12px;
                padding: 5px;
            }
            QLabel#instruction {
                color: #ffffff;
                font-size: 11px;
                padding: 3px;
            }
            QTextEdit {
                background-color: #000000;
                color: #ffffff;
                border: 1px solid #ffffff;
                font-size: 12px;
                padding: 10px;
            }
            QPushButton {
                background-color: #333333;
                color: #ffffff;
                font-size: 13px;
                font-weight: bold;
                padding: 8px 16px;
                border: 1px solid #ffffff;
            }
            QPushButton:hover {
                background-color: #555555;
            }
            QPushButton:pressed {
                background-color: #777777;
            }
            QPushButton#exitButton {
                background-color: #333333;
                border: 1px solid #ff0000;
                color: #ff0000;
            }
            QPushButton#exitButton:hover {
                background-color: #550000;
                color: #ffffff;
            }
            QProgressBar {
                border: 1px solid #ffffff;
                text-align: center;
                background-color: #000000;
                color: #ffffff;
            }
            QProgressBar::chunk {
                background-color: #ffffff;
            }
            QFrame#cameraFrame {
                border: 1px solid #ffffff;
                background-color: #000000;
            }
        """)
        
        self._build_ui()
        self._start_camera_feed()
    
    def _build_ui(self):
        """Construye la interfaz de usuario"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # ========== ENCABEZADO ==========
        header_layout = QHBoxLayout()
        
        title_label = QLabel(self.lesson.name)
        title_label.setObjectName("title")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        difficulty_label = QLabel(f"Dificultad: {self.lesson.difficulty}")
        difficulty_label.setObjectName("subtitle")
        header_layout.addWidget(difficulty_label)
        
        main_layout.addLayout(header_layout)
        
        # ========== CONTENIDO PRINCIPAL (Cámaras + Panel) ==========
        content_layout = QHBoxLayout()
        
        # --- Panel Izquierdo: Cámaras ---
        camera_container = QVBoxLayout()
        
        # Frame para las cámaras
        self.camera_frame = QFrame()
        self.camera_frame.setObjectName("cameraFrame")
        camera_frame_layout = QVBoxLayout(self.camera_frame)
        
        self.camera_label = QLabel()
        self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_label.setMinimumSize(960, 480)  # 640x480 x 2 cámaras
        self.camera_label.setScaledContents(False)
        camera_frame_layout.addWidget(self.camera_label)
        
        camera_container.addWidget(self.camera_frame)
        content_layout.addLayout(camera_container, 2)  # 2/3 del espacio
        
        # --- Panel Derecho: Información de la Lección ---
        info_panel = QVBoxLayout()
        info_panel.setSpacing(15)
        
        # Descripción
        desc_label = QLabel("Descripción:")
        desc_label.setObjectName("subtitle")
        info_panel.addWidget(desc_label)
        
        self.description_text = QTextEdit()
        self.description_text.setReadOnly(True)
        self.description_text.setMaximumHeight(80)
        self.description_text.setText(self.lesson.description)
        info_panel.addWidget(self.description_text)
        
        # Instrucciones (área dinámica)
        inst_label = QLabel("Instrucciones:")
        inst_label.setObjectName("subtitle")
        info_panel.addWidget(inst_label)
        
        self.instructions_text = QTextEdit()
        self.instructions_text.setReadOnly(True)
        self.instructions_text.setMinimumHeight(200)
        info_panel.addWidget(self.instructions_text)
        
        # Progreso
        progress_label = QLabel("Progreso:")
        progress_label.setObjectName("subtitle")
        info_panel.addWidget(progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        info_panel.addWidget(self.progress_bar)
        
        # Info adicional de la lección (personalizable)
        self.custom_info_label = QLabel("")
        self.custom_info_label.setObjectName("instruction")
        self.custom_info_label.setWordWrap(True)
        info_panel.addWidget(self.custom_info_label)
        
        info_panel.addStretch()
        
        # Botones de control
        button_layout = QVBoxLayout()
        button_layout.setSpacing(10)
        
        self.exit_button = QPushButton("SALIR DE LA LECCIÓN")
        self.exit_button.setObjectName("exitButton")
        self.exit_button.clicked.connect(self._exit_lesson)
        button_layout.addWidget(self.exit_button)
        
        info_panel.addLayout(button_layout)
        
        content_layout.addLayout(info_panel, 1)  # 1/3 del espacio
        
        main_layout.addLayout(content_layout)
        
        # ========== PIE DE PÁGINA ==========
        footer_label = QLabel("Presiona ESC o Q para salir | Sigue las instrucciones de la lección")
        footer_label.setObjectName("instruction")
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(footer_label)
    
    def _start_camera_feed(self):
        """Inicia el timer para actualizar el feed de las cámaras"""
        self.timer.timeout.connect(self._update_frame)
        self.timer.start(30)  # ~33 FPS
    
    def _update_frame(self):
        """Actualiza el frame de las cámaras y ejecuta la lección"""
        if not self.continue_lesson:
            self.close()
            return
        
        # Obtener frames de las cámaras usando el método next()
        finished_left, frame_left = self.camera_left.next(black=True, wait=1)
        finished_right, frame_right = self.camera_right.next(black=True, wait=1)
        
        if frame_left is None or frame_right is None:
            return
        
        # Procesar teclado virtual con el procesador centralizado
        if self.keyboard_processor and self.hand_detector_left and self.hand_detector_right:
            try:
                frame_left, frame_right = self.keyboard_processor.process_and_play(
                    frame_left=frame_left,
                    frame_right=frame_right,
                    virtual_keyboard=self.virtual_keyboard,
                    hand_detector_left=self.hand_detector_left,
                    hand_detector_right=self.hand_detector_right,
                    game_mode=False,
                    rhythm_game=None
                )
            except Exception as e:
                print(f"Error procesando teclado: {e}")
                import traceback
                traceback.print_exc()
        
        # Ejecutar lógica de la lección (sin dibujar en frames)
        # La lección debe actualizar su estado interno
        try:
            lesson_data = self.lesson.get_lesson_state()
            
            # Actualizar UI con datos de la lección
            if 'instructions' in lesson_data:
                self.instructions_text.setText(lesson_data['instructions'])
            
            if 'progress' in lesson_data:
                self.progress_bar.setValue(lesson_data['progress'])
            
            if 'custom_info' in lesson_data:
                self.custom_info_label.setText(lesson_data['custom_info'])
            
        except Exception as e:
            print(f"Error ejecutando lección: {e}")
        
        # Concatenar frames (sin overlays)
        h_frames = np.concatenate((frame_left, frame_right), axis=1)
        
        # Convertir a QPixmap y mostrar
        self._display_frame(h_frames)
    
    def _display_frame(self, frame):
        """Convierte frame OpenCV a QPixmap y lo muestra"""
        try:
            # Convertir BGR a RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            
            # Crear QImage
            q_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            
            # Escalar manteniendo aspect ratio
            pixmap = QPixmap.fromImage(q_img)
            scaled_pixmap = pixmap.scaled(
                self.camera_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.camera_label.setPixmap(scaled_pixmap)
            
        except Exception as e:
            print(f"Error mostrando frame: {e}")
    
    def _exit_lesson(self):
        """Maneja el botón de salir"""
        self.continue_lesson = False
        self.lesson.stop()
        self.close()
    
    def keyPressEvent(self, event):
        """Maneja eventos de teclado"""
        key = event.key()
        
        # ESC o Q para salir
        if key in (Qt.Key.Key_Escape, Qt.Key.Key_Q):
            self._exit_lesson()
            return
        
        # Pasar otras teclas a la lección
        try:
            # Convertir Qt.Key a código similar a OpenCV
            if key >= Qt.Key.Key_A and key <= Qt.Key.Key_Z:
                char_code = ord('a') + (key - Qt.Key.Key_A)
                self.lesson.handle_key(char_code, self.synth)
            elif key >= Qt.Key.Key_0 and key <= Qt.Key.Key_9:
                char_code = ord('0') + (key - Qt.Key.Key_0)
                self.lesson.handle_key(char_code, self.synth)
            elif key == Qt.Key.Key_Space:
                self.lesson.handle_key(ord(' '), self.synth)
            elif key == Qt.Key.Key_Left:  # Flecha izquierda
                self.lesson.handle_key(81, self.synth)  # Código OpenCV
            elif key == Qt.Key.Key_Right:  # Flecha derecha
                self.lesson.handle_key(83, self.synth)  # Código OpenCV
            elif key == Qt.Key.Key_Up:  # Flecha arriba
                self.lesson.handle_key(82, self.synth)  # Código OpenCV
            elif key == Qt.Key.Key_Down:  # Flecha abajo
                self.lesson.handle_key(84, self.synth)  # Código OpenCV
            elif key in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
                self.lesson.handle_key(ord('+'), self.synth)
            elif key == Qt.Key.Key_Minus:
                self.lesson.handle_key(ord('-'), self.synth)
            
        except Exception as e:
            print(f"Error manejando tecla: {e}")
    
    def closeEvent(self, event):
        """Maneja el cierre de la ventana"""
        self.timer.stop()
        self.continue_lesson = False
        if self.lesson:
            self.lesson.stop()
        event.accept()


def show_lesson_window(lesson, camera_left, camera_right, synth, 
                      virtual_keyboard, hand_detector_left=None, hand_detector_right=None,
                      keyboard_mapper=None, angler=None, depth_estimator=None,
                      octave_base=60, keyboard_total_keys=24, camera_separation=9.07):
    """
    Muestra la ventana de lección y bloquea hasta que termine
    
    Returns:
        bool: True si completó, False si salió
    """
    app = QApplication.instance()
    owns_app = False
    if app is None:
        app = QApplication(sys.argv)
        owns_app = True
    
    window = LessonWindow(lesson, camera_left, camera_right, synth,
                         virtual_keyboard, hand_detector_left, hand_detector_right,
                         keyboard_mapper, angler, depth_estimator, octave_base,
                         keyboard_total_keys, camera_separation)
    window.show()
    
    # Ejecutar hasta que se cierre la ventana
    if owns_app:
        app.exec()
    else:
        # Si ya existe QApplication, usar un loop local
        while window.isVisible():
            app.processEvents()
    
    result = window.continue_lesson
    
    if owns_app:
        app.quit()
    
    return result
