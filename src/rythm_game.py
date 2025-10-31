"""
Rhythm Game
"""

import cv2
import numpy as np
import time

class Note:
    """Representa una nota que cae"""
    def __init__(self, key_number, spawn_time, hit_time):
        self.key = key_number  # Tecla 0-3
        self.spawn_time = spawn_time  # Cuándo aparece
        self.hit_time = hit_time  # Cuándo debe presionarse
        self.y_pos = 0  # Posición vertical
        self.hit = False  # Si fue presionada
        self.missed = False  # Si se perdió
        
class RhythmGame:
    """Lógica del juego de ritmo"""
    
    def __init__(self, num_keys=4):
        self.num_keys = num_keys
        self.notes = []  # Lista de notas activas
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.perfect_count = 0
        self.good_count = 0
        self.miss_count = 0
    
        # Configuración visual
        self.note_speed = 50  # Píxeles por segundo (reducido para facilitar aprendizaje)
        self.hit_zone_y = 400  # Posición Y de la zona de acierto
        self.hit_zone_height = 40
        
        # Ventanas de tiempo (en segundos) - Reducidas para mayor precisión
        self.perfect_window = 0.10  # ±100ms para perfecto
        self.good_window = 0.25  # ±250ms para bueno
        
        # Control de tiempo
        self.start_time = None
        self.is_playing = False
        
    def start_game(self, song_chart):
        """
        Inicia el juego con una canción
        song_chart: lista de tuplas (tecla, tiempo_en_segundos)
        """
        self.start_time = time.time()
        self.is_playing = True
        self.score = 0
        self.combo = 0
        self.notes = []
        
        # Crear notas desde el chart
        for key, hit_time in song_chart:
            # Calcular cuándo debe aparecer la nota
            travel_time = self.hit_zone_y / self.note_speed
            spawn_time = hit_time - travel_time
            self.notes.append(Note(key, spawn_time, hit_time))
            
    def update(self):
        """Actualiza la posición de las notas"""
        if not self.is_playing:
            return
            
        current_time = time.time() - self.start_time
        
        # Actualizar posición de cada nota - optimizado
        for note in self.notes:
            if not note.hit and not note.missed:
                # Calcular posición basada en tiempo
                time_since_spawn = current_time - note.spawn_time
                if time_since_spawn < 0:
                    continue  # Saltar notas que aún no deben aparecer
                    
                note.y_pos = int(time_since_spawn * self.note_speed)
                
                # Verificar si se pasó la nota (con margen aumentado)
                if current_time > note.hit_time + self.good_window * 1.5:
                    note.missed = True
                    self.miss_count += 1
                    self.combo = 0
                    
    def check_hit(self, key_pressed):
        """
        Verifica si se presionó la tecla correcta en el momento correcto
        Optimizado para respuesta inmediata
        key_pressed: número de tecla (0-12)
        """
        if not self.is_playing:
            return None
            
        current_time = time.time() - self.start_time
        
        # Buscar la nota más cercana en esa tecla - optimizado
        best_note = None
        best_diff = float('inf')
        
        # Filtrar solo notas relevantes (cerca del tiempo de hit)
        for note in self.notes:
            if note.key == key_pressed and not note.hit and not note.missed:
                # Solo considerar notas que están cerca del tiempo de hit
                time_to_hit = note.hit_time - current_time
                
                # Rango extendido: desde antes del hit hasta después
                if -self.good_window <= time_to_hit <= self.good_window:
                    time_diff = abs(time_to_hit)
                    
                    if time_diff < best_diff:
                        best_diff = time_diff
                        best_note = note
                    
        if best_note:
            best_note.hit = True
            self.combo += 1
            self.max_combo = max(self.max_combo, self.combo)
            
            # Determinar calificación
            if best_diff <= self.perfect_window:
                self.score += 100 * self.combo
                self.perfect_count += 1
                return "PERFECT"
            elif best_diff <= self.good_window:
                self.score += 50 * self.combo
                self.good_count += 1
                return "GOOD"
        else:
            # Presionó tecla incorrecta o fuera de tiempo
            # No romper combo si solo está fuera de rango
            pass
            
        return None
        
    def draw(self, frame, keyboard_x0, keyboard_x1, key_width):
        """
        Dibuja las notas cayendo y la zona de acierto
        frame: imagen donde dibujar
        keyboard_x0, keyboard_x1: límites horizontales del teclado
        key_width: ancho de cada tecla
        """
        if not self.is_playing:
            return frame
            
        # Dibujar líneas de separación de teclas
        for i in range(self.num_keys + 1):
            x = int(keyboard_x0 + i * key_width)
            cv2.line(frame, (x, 0), (x, self.hit_zone_y + 50), 
                    (100, 100, 100), 1)
        
        # Dibujar zona de acierto (barra inferior)
        cv2.rectangle(frame, 
                     (keyboard_x0, self.hit_zone_y),
                     (keyboard_x1, self.hit_zone_y + self.hit_zone_height),
                     (0, 255, 0), 2)
        
        # Dibujar notas - 13 colores para 13 teclas
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0),
                  (255, 0, 255), (0, 255, 255), (128, 0, 128),
                  (255, 165, 0), (255, 192, 203), (128, 128, 0),
                  (0, 128, 128), (128, 0, 0), (0, 0, 128)]
        
        for note in self.notes:
            # Solo dibujar notas visibles (optimización de rendimiento)
            if not note.hit and not note.missed and 0 <= note.y_pos <= self.hit_zone_y + 100:
                # Calcular posición horizontal de la nota
                # Para 13 teclas, mapear a las 8 teclas blancas principales
                # note.key es 0-12, mapear a posición en teclado de 8 blancas
                white_key_index = note.key % 8  # Mapeo simple a las 8 teclas blancas
                note_x0 = int(keyboard_x0 + white_key_index * key_width + 5)
                note_x1 = int(keyboard_x0 + (white_key_index + 1) * key_width - 5)
                note_y0 = note.y_pos
                note_y1 = note.y_pos + 30
                
                # Dibujar nota
                color = colors[note.key % len(colors)]
                cv2.rectangle(frame, (note_x0, note_y0), 
                            (note_x1, note_y1), color, -1)
                cv2.rectangle(frame, (note_x0, note_y0), 
                            (note_x1, note_y1), (255, 255, 255), 2)
        
        # Dibujar información del juego
        self.draw_ui(frame)
        
        return frame
        
    def draw_ui(self, frame):
        """Dibuja score, combo y estadísticas"""
        y_offset = 30
        
        # Score
        cv2.putText(frame, f'Score: {self.score}', (10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        y_offset += 30
        
        # Combo
        if self.combo > 0:
            cv2.putText(frame, f'Combo: {self.combo}x', (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        y_offset += 30
        
        # Estadísticas
        cv2.putText(frame, f'Perfect: {self.perfect_count}', (10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        y_offset += 25
        cv2.putText(frame, f'Good: {self.good_count}', (10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
        y_offset += 25
        cv2.putText(frame, f'Miss: {self.miss_count}', (10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)