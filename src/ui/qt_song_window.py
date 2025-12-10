#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ventana PyQt6 para jugar canciones en modo ritmo
Embebe feed de cámaras OpenCV y muestra UI del juego
"""

import sys
import cv2
import numpy as np
import time
from typing import Optional
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QProgressBar, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap, QFont
from src.piano.keyboard_processor import KeyboardProcessor


class SongWindow(QMainWindow):
    """
    Ventana principal para jugar canciones en modo ritmo.
    Muestra el feed de las cámaras con las notas cayendo.
    """
    
    def __init__(self, song, camera_left, camera_right, synth, 
                 virtual_keyboard, hand_detector_left=None, hand_detector_right=None,
                 keyboard_mapper=None, angler=None, depth_estimator=None, octave_base=60,
                 keyboard_total_keys=24, camera_separation=9.07):
        super().__init__()
        
        self.song = song
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
        
        self.continue_song = True
        self.timer = QTimer()
        
        # Configuración de ventana
        self.setWindowTitle(f"Modo Ritmo - {song.name}")
        self.setMinimumSize(1400, 800)
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #000000;
            }
            QLabel#title {
                color: #ffffff;
                font-size: 18px;
                font-weight: bold;
                padding: 8px;
                background-color: #000000;
            }
            QLabel#info {
                color: #ffffff;
                font-size: 13px;
                padding: 5px;
            }
            QLabel#score {
                color: #00ff00;
                font-size: 24px;
                font-weight: bold;
                padding: 5px;
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
                max-height: 20px;
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
        self._start_game()
    
    def _build_ui(self):
        """Construye la interfaz de usuario"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # ========== CABECERA ==========
        header_layout = QHBoxLayout()
        
        # Título de la canción
        title_label = QLabel(f"♪ {self.song.name}")
        title_label.setObjectName("title")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Info de la canción
        info_label = QLabel(f"{self.song.bpm} BPM  •  {self.song.difficulty}")
        info_label.setObjectName("info")
        header_layout.addWidget(info_label)
        
        header_layout.addSpacing(20)
        
        # Score
        self.score_label = QLabel("Score: 0")
        self.score_label.setObjectName("score")
        header_layout.addWidget(self.score_label)
        
        main_layout.addLayout(header_layout)
        
        # ========== ÁREA DE CÁMARAS (con notas dibujadas) ==========
        camera_frame = QFrame()
        camera_frame.setObjectName("cameraFrame")
        camera_layout = QVBoxLayout(camera_frame)
        camera_layout.setContentsMargins(0, 0, 0, 0)
        
        self.camera_label = QLabel()
        self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_label.setMinimumSize(1280, 480)
        camera_layout.addWidget(self.camera_label)
        
        main_layout.addWidget(camera_frame, 1)
        
        # ========== BARRA DE PROGRESO ==========
        progress_layout = QHBoxLayout()
        progress_label = QLabel("Progreso:")
        progress_label.setObjectName("info")
        progress_layout.addWidget(progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar, 1)
        
        main_layout.addLayout(progress_layout)
        
        # ========== PIE DE PÁGINA ==========
        footer_layout = QHBoxLayout()
        
        footer_label = QLabel("ESC o Q para salir  •  Toca las teclas del piano cuando aparezcan las notas")
        footer_label.setObjectName("info")
        footer_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        footer_layout.addWidget(footer_label)
        
        footer_layout.addStretch()
        
        exit_btn = QPushButton("Salir")
        exit_btn.setObjectName("exitButton")
        exit_btn.clicked.connect(self._exit_song)
        footer_layout.addWidget(exit_btn)
        
        main_layout.addLayout(footer_layout)
    
    def _start_game(self):
        """Inicia el juego"""
        self.song.start()
        self.timer.timeout.connect(self._update_frame)
        self.timer.start(30)  # ~33 FPS
    
    def _update_frame(self):
        """Actualiza el frame de las cámaras y ejecuta la canción"""
        if not self.continue_song or not self.song.running:
            self.close()
            return
        
        # Obtener frames de las cámaras
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
                    game_mode=False,  # Songs usa modo libre
                    rhythm_game=None
                )
            except Exception as e:
                print(f"Error procesando teclado: {e}")
                import traceback
                traceback.print_exc()
        
        # Ejecutar lógica de la canción (dibuja en los frames)
        try:
            frame_left, frame_right, continue_running = self.song.run(
                frame_left, frame_right, self.virtual_keyboard, self.synth
            )
            
            if not continue_running:
                self.continue_song = False
                print("✓ Canción terminada")
            
            # Actualizar score
            self.score_label.setText(f"Score: {self.song.score}")
            
            # Actualizar progreso (basado en tiempo)
            if hasattr(self.song, 'chart') and self.song.chart:
                current_time = time.time() - self.song.start_time
                last_note_time = self.song.chart[-1]["time"]
                progress = min(100, int((current_time / (last_note_time + 2)) * 100))
                self.progress_bar.setValue(progress)
            
        except Exception as e:
            print(f"Error ejecutando canción: {e}")
            import traceback
            traceback.print_exc()
        
        # Aplicar flip horizontal para corregir efecto espejo
        frame_left = cv2.flip(frame_left, 1)
        frame_right = cv2.flip(frame_right, 1)
        
        # Concatenar frames en orden correcto (derecha primero, izquierda después)
        h_frames = np.concatenate((frame_right, frame_left), axis=1)
        
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
    
    def _exit_song(self):
        """Maneja el botón de salir"""
        self.continue_song = False
        self.song.stop()
        self.close()
    
    def keyPressEvent(self, event):
        """Maneja eventos de teclado"""
        key = event.key()
        
        # ESC o Q para salir
        if key in (Qt.Key.Key_Escape, Qt.Key.Key_Q):
            self._exit_song()
            return
    
    def closeEvent(self, event):
        """Maneja el cierre de la ventana"""
        self.timer.stop()
        self.continue_song = False
        if self.song:
            self.song.stop()
        event.accept()


def show_song_window(song, camera_left, camera_right, synth, 
                     virtual_keyboard, hand_detector_left=None, hand_detector_right=None,
                     keyboard_mapper=None, angler=None, depth_estimator=None, 
                     octave_base=60, keyboard_total_keys=24, camera_separation=9.07):
    """
    Muestra la ventana de juego de canción y bloquea hasta que termine
    
    Returns:
        bool: True si completó, False si salió
    """
    app = QApplication.instance()
    owns_app = False
    if app is None:
        app = QApplication(sys.argv)
        owns_app = True
    
    window = SongWindow(song, camera_left, camera_right, synth,
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
    
    result = window.continue_song
    
    if owns_app:
        app.quit()
    
    return result
