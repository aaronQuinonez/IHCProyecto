#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Menú de selección de lecciones de teoría musical con PyQt6
"""

import sys
from typing import Optional
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSpacerItem, QSizePolicy, QScrollArea, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap, QPainter


class TheoryMenuDialog(QDialog):
    """
    Diálogo para seleccionar una lección de teoría musical
    """

    def __init__(self, lessons):
        """
        Args:
            lessons: Lista de tuplas (lesson_id, lesson_instance)
        """
        super().__init__()
        
        self.lessons = lessons
        self.selected_lesson_id: Optional[str] = None
        self.selected_index = 0
        
        self.setWindowTitle("Teoría Musical - Selección de Lección")
        self.setMinimumSize(900, 600)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a2e;
            }
            QLabel#title {
                color: #ffffff;
                font-size: 36px;
                font-weight: bold;
            }
            QLabel#subtitle {
                color: #16c79a;
                font-size: 18px;
            }
            QLabel#lessonName {
                color: #ffffff;
                font-size: 20px;
                font-weight: bold;
            }
            QLabel#lessonDesc {
                color: #cccccc;
                font-size: 14px;
            }
            QLabel#difficulty {
                font-size: 14px;
                font-weight: bold;
                padding: 4px 12px;
                border-radius: 4px;
            }
            QLabel#difficultyBasic {
                color: #00ff00;
                background-color: rgba(0, 255, 0, 0.15);
            }
            QLabel#difficultyIntermediate {
                color: #ffa500;
                background-color: rgba(255, 165, 0, 0.15);
            }
            QLabel#difficultyAdvanced {
                color: #ff4444;
                background-color: rgba(255, 68, 68, 0.15);
            }
            QPushButton {
                background-color: #0f3460;
                color: #ffffff;
                font-size: 16px;
                padding: 12px 20px;
                border: 2px solid #16c79a;
                border-radius: 8px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #16c79a;
                border-color: #ffffff;
            }
            QPushButton#selected {
                background-color: #16c79a;
                border-color: #ffffff;
                border-width: 3px;
            }
            QPushButton#backButton {
                background-color: #c70039;
                border-color: #c70039;
                text-align: center;
            }
            QPushButton#backButton:hover {
                background-color: #ff5757;
                border-color: #ffffff;
            }
        """)
        
        self._build_ui()
        self._update_focus()
    
    def _build_ui(self):
        """Construye la interfaz de usuario"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(20)
        
        # Título
        title = QLabel("TEORÍA MUSICAL")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)
        
        # Subtítulo
        subtitle = QLabel("Selecciona una lección para comenzar")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(subtitle)
        
        # Área de scroll para lecciones
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #0f3460;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #16c79a;
                border-radius: 6px;
            }
        """)
        
        # Widget contenedor para las lecciones
        lessons_widget = QWidget()
        lessons_layout = QVBoxLayout(lessons_widget)
        lessons_layout.setSpacing(10)
        
        # Crear botones para cada lección
        self.lesson_buttons = []
        for i, (lesson_id, lesson) in enumerate(self.lessons):
            # Contenedor horizontal para cada lección
            lesson_container = QHBoxLayout()
            
            # Botón principal de la lección
            btn = QPushButton()
            btn.setMinimumHeight(70)
            btn.clicked.connect(lambda checked, idx=i: self._select_lesson(idx))
            
            # Layout interno del botón
            btn_layout = QVBoxLayout()
            
            # Fila superior: número y nombre
            top_row = QHBoxLayout()
            
            num_label = QLabel(f"{i + 1}.")
            num_label.setStyleSheet("color: #16c79a; font-weight: bold; font-size: 18px;")
            top_row.addWidget(num_label)
            
            name_label = QLabel(lesson.name)
            name_label.setObjectName("lessonName")
            top_row.addWidget(name_label)
            
            top_row.addStretch()
            
            # Etiqueta de dificultad
            difficulty_label = QLabel(lesson.difficulty)
            difficulty_label.setObjectName("difficulty")
            
            # Aplicar estilo según dificultad
            if lesson.difficulty == "Básico":
                difficulty_label.setProperty("class", "difficultyBasic")
                difficulty_label.setObjectName("difficultyBasic")
            elif lesson.difficulty == "Intermedio":
                difficulty_label.setProperty("class", "difficultyIntermediate")
                difficulty_label.setObjectName("difficultyIntermediate")
            else:
                difficulty_label.setProperty("class", "difficultyAdvanced")
                difficulty_label.setObjectName("difficultyAdvanced")
            
            top_row.addWidget(difficulty_label)
            
            btn_layout.addLayout(top_row)
            
            # Descripción
            desc_label = QLabel(lesson.description)
            desc_label.setObjectName("lessonDesc")
            desc_label.setWordWrap(True)
            btn_layout.addWidget(desc_label)
            
            # Aplicar layout al botón (nota: en PyQt6 no se puede directamente)
            # En su lugar, usamos un contenedor
            btn_widget = QWidget()
            btn_inner = QVBoxLayout(btn_widget)
            btn_inner.setContentsMargins(15, 10, 15, 10)
            
            btn_inner.addLayout(top_row)
            btn_inner.addWidget(desc_label)
            
            # Agregar widget al layout principal
            lesson_container.addWidget(btn)
            
            lessons_layout.addWidget(btn)
            self.lesson_buttons.append(btn)
        
        lessons_layout.addStretch()
        scroll_area.setWidget(lessons_widget)
        main_layout.addWidget(scroll_area)
        
        # Instrucciones
        instructions = QLabel("↑/↓: Navegar  |  ENTER: Seleccionar  |  ESC: Volver")
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions.setStyleSheet("color: #999999; font-size: 13px;")
        main_layout.addWidget(instructions)
        
        # Botón de volver
        back_button = QPushButton("VOLVER AL MENÚ PRINCIPAL")
        back_button.setObjectName("backButton")
        back_button.clicked.connect(self.reject)
        main_layout.addWidget(back_button)
        
        self.setLayout(main_layout)
    
    def _update_focus(self):
        """Actualiza el estilo del botón seleccionado"""
        for i, btn in enumerate(self.lesson_buttons):
            if i == self.selected_index:
                btn.setObjectName("selected")
                btn.setFocus()
            else:
                btn.setObjectName("")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
    
    def _select_lesson(self, index):
        """Selecciona una lección y cierra el diálogo"""
        self.selected_index = index
        lesson_id, _ = self.lessons[index]
        self.selected_lesson_id = lesson_id
        self.accept()
    
    def keyPressEvent(self, event):
        """Manejo de teclas para navegación"""
        if event.key() in (Qt.Key.Key_Up, Qt.Key.Key_W):
            self.selected_index = max(0, self.selected_index - 1)
            self._update_focus()
        elif event.key() in (Qt.Key.Key_Down, Qt.Key.Key_S):
            self.selected_index = min(len(self.lessons) - 1, self.selected_index + 1)
            self._update_focus()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._select_lesson(self.selected_index)
        elif event.key() in (Qt.Key.Key_Escape, Qt.Key.Key_Q):
            self.reject()
        elif event.key() >= Qt.Key.Key_1 and event.key() <= Qt.Key.Key_9:
            # Selección directa por número
            num = event.key() - Qt.Key.Key_1
            if 0 <= num < len(self.lessons):
                self._select_lesson(num)
        else:
            super().keyPressEvent(event)


def show_theory_menu(lessons) -> Optional[str]:
    """
    Muestra el menú de selección de lecciones de teoría
    
    Args:
        lessons: Lista de tuplas (lesson_id, lesson_instance)
    
    Returns:
        lesson_id seleccionado o None si se cancela
    """
    app = QApplication.instance()
    owns_app = False
    if app is None:
        app = QApplication(sys.argv)
        owns_app = True
    
    dlg = TheoryMenuDialog(lessons)
    result = dlg.exec()
    
    lesson_id = dlg.selected_lesson_id if result == QDialog.DialogCode.Accepted else None
    
    if owns_app:
        app.quit()
    
    return lesson_id
