#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de ayuda para interfaz de usuario mejorada
"""

import cv2
import numpy as np


class UIHelper:
    """Clase para crear interfaz más amigable"""
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.show_instructions = True
        self.instructions_timeout = 300  # frames (10 segundos a 30fps)
        self.frame_count = 0
        
    def draw_welcome_screen(self, frame):
        """Dibuja pantalla de bienvenida moderna con diseño mejorado"""
        frame_height = frame.shape[0]
        frame_width = frame.shape[1]
        
        # Fondo con gradiente oscuro elegante
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (frame_width, frame_height), (15, 15, 30), -1)
        frame = cv2.addWeighted(frame, 0.2, overlay, 0.8, 0)
        
        # ========== TÍTULO PRINCIPAL ==========
        title = "PIANO VIRTUAL"
        title_font_scale = 2.2
        title_thickness = 4
        (title_w, title_h), _ = cv2.getTextSize(title, cv2.FONT_HERSHEY_SIMPLEX, 
                                                  title_font_scale, title_thickness)
        title_x = (frame_width - title_w) // 2
        title_y = 100
        
        # Sombra del título
        cv2.putText(frame, title, (title_x + 3, title_y + 3),
                   cv2.FONT_HERSHEY_SIMPLEX, title_font_scale, (0, 0, 0), title_thickness)
        # Título principal con gradiente de colores (amarillo a naranja)
        cv2.putText(frame, title, (title_x, title_y),
                   cv2.FONT_HERSHEY_SIMPLEX, title_font_scale, (0, 200, 255), title_thickness)
        
        # Subtitle - Mensaje de inicio
        subtitle = "Presione cualquier tecla"
        (sub_w, sub_h), _ = cv2.getTextSize(subtitle, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
        sub_x = (frame_width - sub_w) // 2
        
        # ========== DISENO DE DOS COLUMNAS ==========
        col_y_start = 180
        col_spacing = 20
        col_width = (frame_width - col_spacing * 3) // 2
        left_col_x = col_spacing
        right_col_x = col_width + col_spacing * 2
        
        # ========== COLUMNA IZQUIERDA: INSTRUCCIONES ==========
        left_panel_h = 280
        
        left_bg = frame.copy()
        cv2.rectangle(left_bg, (left_col_x, col_y_start), 
                     (left_col_x + col_width, col_y_start + left_panel_h), (30, 30, 50), -1)
        cv2.rectangle(left_bg, (left_col_x, col_y_start), 
                     (left_col_x + col_width, col_y_start + left_panel_h), (0, 200, 255), 3)
        frame = cv2.addWeighted(frame, 0.6, left_bg, 0.4, 0)
        
        # Titulo de instrucciones
        section_title = "INSTRUCCIONES"
        cv2.putText(frame, section_title, (left_col_x + 20, col_y_start + 35),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
        
        # Linea decorativa
        cv2.line(frame, (left_col_x + 20, col_y_start + 45), 
                (left_col_x + col_width - 20, col_y_start + 45), (0, 200, 255), 2)
        
        # Instrucciones
        instructions = [
            "Coloca tus manos sobre la mesa",
            "Toca las teclas virtuales",
            "Manten contacto con la mesa",
            "Usa ambos dedos para tocar"
        ]
        
        y_offset = col_y_start + 70
        for instruction in instructions:
            cv2.circle(frame, (left_col_x + 35, y_offset - 5), 4, (0, 200, 255), -1)
            cv2.putText(frame, instruction, (left_col_x + 50, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
            y_offset += 35
        
        # ========== COLUMNA DERECHA: CONTROLES ==========
        right_panel_h = 280
        
        right_bg = frame.copy()
        cv2.rectangle(right_bg, (right_col_x, col_y_start), 
                     (right_col_x + col_width, col_y_start + right_panel_h), (30, 30, 50), -1)
        cv2.rectangle(right_bg, (right_col_x, col_y_start), 
                     (right_col_x + col_width, col_y_start + right_panel_h), (255, 200, 0), 3)
        frame = cv2.addWeighted(frame, 0.6, right_bg, 0.4, 0)
        
        # Titulo de controles
        controls_title = "CONTROLES"
        cv2.putText(frame, controls_title, (right_col_x + 20, col_y_start + 35),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 200, 0), 2)
        
        # Linea decorativa
        cv2.line(frame, (right_col_x + 20, col_y_start + 45), 
                (right_col_x + col_width - 20, col_y_start + 45), (255, 200, 0), 2)
        
        # Controles
        controls = [
            "[G] Juego de ritmo",
            "[F] Modo libre",
            "[D] Dashboard",
            "[T] Subir mesa",
            "[B] Bajar mesa",
            "[Q] Salir"
        ]
        
        y_ctrl = col_y_start + 70
        for i, ctrl in enumerate(controls):
            key_bg_x = right_col_x + 25
            key_bg_y = y_ctrl + i * 35 - 20
            key_bg_w = col_width - 50
            key_bg_h = 22
            
            # Fondo destacado
            key_overlay = frame.copy()
            cv2.rectangle(key_overlay, (key_bg_x, key_bg_y), 
                         (key_bg_x + key_bg_w, key_bg_y + key_bg_h), (40, 40, 60), -1)
            frame = cv2.addWeighted(frame, 0.8, key_overlay, 0.2, 0)
            
            cv2.putText(frame, ctrl, (right_col_x + 30, y_ctrl + i * 35),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
        
        # ========== MENSAJE DE INICIO (ya movido arriba, solo agregamos efecto visual) ==========
        # Efecto parpadeante para el subtítulo
        blink_alpha = 0.3 + 0.2 * np.sin(self.frame_count * 0.1)
        blink_bg = frame.copy()
        cv2.rectangle(blink_bg, (sub_x - 15, title_y + 50 - sub_h - 10), 
                     (sub_x + sub_w + 15, title_y + 50 + 10), (0, 255, 255), -1)
        frame = cv2.addWeighted(frame, 1 - blink_alpha, blink_bg, blink_alpha, 0)
        
        # Redibujar el texto del subtítulo sobre el fondo parpadeante
        cv2.putText(frame, subtitle, (sub_x, title_y + 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 3)
        cv2.putText(frame, subtitle, (sub_x, title_y + 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (180, 180, 255), 2)
        
        return frame
    
    def draw_instructions_bar(self, frame, game_mode):
        """Dibuja barra de instrucciones en la parte superior"""
        bar_height = 40
        frame_height = frame.shape[0]
        frame_width = frame.shape[1]
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (frame_width, bar_height), (20, 20, 20), -1)
        frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)
        
        # Modo actual
        mode_text = "MODO JUEGO" if game_mode else "MODO LIBRE"
        mode_color = (0, 255, 0) if game_mode else (255, 255, 0)
        cv2.putText(frame, mode_text, (10, 28),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, mode_color, 2)
        
        # Teclas disponibles
        if not game_mode:
            help_text = "G: Juego | F: Libre | D: Dashboard | Q: Salir"
        else:
            help_text = "F: Salir del juego | D: Dashboard | Q: Salir"
        
        frame_width = frame.shape[1]
        text_size = cv2.getTextSize(help_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
        cv2.putText(frame, help_text, (frame_width - text_size[0] - 10, 28),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        return frame
    
    def draw_improved_dashboard(self, frame, fps1, fps2, cps, X, Y, Z, D, Dr):
        """Dibuja dashboard mejorado con mejor diseño"""
        # Panel semi-transparente
        panel_width = 280
        panel_height = 200
        panel_x = 10
        panel_y = self.height - panel_height - 10
        
        overlay = frame.copy()
        cv2.rectangle(overlay, 
                     (panel_x, panel_y), 
                     (panel_x + panel_width, panel_y + panel_height),
                     (0, 0, 0), -1)
        frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)
        
        # Borde del panel
        cv2.rectangle(frame,
                     (panel_x, panel_y),
                     (panel_x + panel_width, panel_y + panel_height),
                     (0, 255, 0), 2)
        
        # Título
        cv2.putText(frame, "STATUS", (panel_x + 10, panel_y + 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Información
        y_offset = panel_y + 50
        line_height = 25
        
        # FPS con indicador de color
        fps_color = (0, 255, 0) if (fps1 + fps2) / 2 > 20 else (0, 165, 255) if (fps1 + fps2) / 2 > 15 else (0, 0, 255)
        fps_text = f"FPS: {fps1}/{fps2} (Prom: {(fps1+fps2)//2})"
        cv2.putText(frame, fps_text, (panel_x + 10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, fps_color, 1)
        y_offset += line_height
        
        cv2.putText(frame, f"CPS: {cps}", (panel_x + 10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        y_offset += line_height
        
        cv2.putText(frame, f"Posicion: X:{X:.1f} Y:{Y:.1f}", 
                   (panel_x + 10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        y_offset += line_height
        
        cv2.putText(frame, f"Distancia: {D:.1f}cm (Ajuste: {Dr:.1f}cm)",
                   (panel_x + 10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame
    
    def draw_key_indicators(self, frame, active_keys, keyboard_x0, keyboard_y0, keyboard_x1, keyboard_y1):
        """Dibuja indicadores visuales de teclas presionadas"""
        if len(active_keys) == 0:
            return frame
        
        keyboard_width = keyboard_x1 - keyboard_x0
        key_width = keyboard_width / 8  # 8 teclas blancas
        
        for key_num in active_keys:
            if 0 <= key_num < 13:
                # Calcular posición de la tecla (simplificado - necesita mapeo correcto)
                key_x = int(keyboard_x0 + (key_num % 8) * key_width)
                key_w = int(key_width)
                
                # Dibujar highlight verde cuando está activa
                overlay = frame.copy()
                cv2.rectangle(overlay, (key_x, keyboard_y0), 
                             (key_x + key_w, keyboard_y1), (0, 255, 0), -1)
                frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)
        
        return frame
    
    def draw_fps_indicator(self, frame, fps, position=(10, 30)):
        """Dibuja indicador de FPS grande y visible"""
        fps_color = (0, 255, 0) if fps >= 25 else (0, 165, 255) if fps >= 20 else (0, 0, 255)
        
        # Fondo para el texto
        text = f"FPS: {fps}"
        (text_width, text_height), baseline = cv2.getTextSize(
            text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
        
        overlay = frame.copy()
        cv2.rectangle(overlay,
                     (position[0] - 5, position[1] - text_height - 5),
                     (position[0] + text_width + 5, position[1] + 5),
                     (0, 0, 0), -1)
        frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)
        
        cv2.putText(frame, text, position,
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, fps_color, 2)
        
        return frame
    
    def update(self):
        """Actualiza contador interno"""
        self.frame_count += 1
        if self.frame_count > self.instructions_timeout:
            self.show_instructions = False
    
    def reset_instructions(self):
        """Reinicia la pantalla de instrucciones"""
        self.show_instructions = True
        self.frame_count = 0

