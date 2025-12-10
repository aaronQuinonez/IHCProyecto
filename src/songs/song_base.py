from abc import ABC, abstractmethod
import cv2
import time
from src.gameplay.rythm_game import RhythmGame

class BaseSong(ABC):
    """
    Clase base para todas las canciones.
    Define la estructura que deben tener los archivos en chart_files.
    """
    
    # --- Configuración por defecto de una canción ---
    name: str = "Canción sin nombre"
    bpm: int = 120
    difficulty: str = "Básico"  # Básico, Intermedio, Avanzado
    scroll_speed: float = 1.0   # Multiplicador de velocidad (1.0 = normal)
    music_key: str = "C"        # Tonalidad (ej: C Mayor)
    
    # La estructura de notas: { "time": segundo, "keys": ["tecla"] }
    # O formato compatible: [(key_number, hit_time), ...]
    chart: list = []

    def __init__(self):
        self.running = False
        self.start_time = 0
        self.score = 0
        self.active_chart = []  # Copia del chart para jugar
        self.rhythm_game = None  # Instancia de RhythmGame
        self.num_keys = 24  # Número de teclas del teclado virtual

    def _note_to_key_number(self, note_name, virtual_keyboard):
        """
        Convierte nombre de nota musical (C, D, E, etc.) a número de tecla (0-23)
        Usa el mapeo real del piano virtual basado en __keyboard_piano_map
        """
        # Mapeo inverso del __keyboard_piano_map del VirtualKeyboard
        # MIDI note -> key number (0-23)
        midi_to_key = {
            # Primera octava (C4=60 a B4=71) -> keys 0-11
            60: 0,  61: 1,  62: 2,  63: 3,  64: 4,  65: 5,  66: 6,  67: 7,
            68: 8,  69: 9,  70: 10, 71: 11,
            # Segunda octava (C5=72 a B5=83) -> keys 12-23
            72: 12, 73: 13, 74: 14, 75: 15, 76: 16, 77: 17, 78: 18, 79: 19,
            80: 20, 81: 21, 82: 22, 83: 23
        }
        
        # Mapeo de notas musicales a MIDI (C4=60 es la base)
        note_to_midi_base = {
            'C': 60, 'C#': 61, 'Db': 61,
            'D': 62, 'D#': 63, 'Eb': 63,
            'E': 64,
            'F': 65, 'F#': 66, 'Gb': 66,
            'G': 67, 'G#': 68, 'Ab': 68,
            'A': 69, 'A#': 70, 'Bb': 70,
            'B': 71
        }
        
        # Limpiar nombre de nota
        note_clean = note_name.strip().upper()
        
        # Detectar octava si está presente (ej: "C4", "C5")
        octave = 4  # Octava por defecto (primera octava del piano)
        if len(note_clean) > 1:
            # Verificar si el último carácter es un número
            if note_clean[-1].isdigit():
                octave = int(note_clean[-1])
                note_clean = note_clean[:-1]
            # Manejar sostenidos y bemoles
            elif len(note_clean) > 1 and note_clean[1] in ['#', 'B']:
                if note_clean[1] == '#':
                    note_clean = note_clean[0] + '#'
                else:
                    note_clean = note_clean[0] + 'b'
        
        # Obtener MIDI base de la nota
        midi_base = note_to_midi_base.get(note_clean, 60)
        
        # Calcular MIDI según octava (C4=60, C5=72, etc.)
        midi_note = midi_base + (octave - 4) * 12
        
        # Convertir MIDI a número de tecla usando el mapeo inverso
        key_number = midi_to_key.get(midi_note, 0)
        
        # Asegurar que esté en rango válido (0-23)
        return max(0, min(23, key_number))

    def _convert_chart_to_rhythm_format(self, chart, virtual_keyboard):
        """
        Convierte chart de formato dict a formato tupla para RhythmGame
        chart: [{ "time": 2.0, "keys": ["C"] }, ...]
        retorna: [(key_number, hit_time), ...]
        """
        rhythm_chart = []
        
        for item in chart:
            if isinstance(item, dict):
                # Formato nuevo: { "time": 2.0, "keys": ["C"] }
                hit_time = item.get("time", 0)
                keys = item.get("keys", [])
                
                # Si hay múltiples teclas, crear una nota por cada una
                for key_name in keys:
                    key_number = self._note_to_key_number(key_name, virtual_keyboard)
                    rhythm_chart.append((key_number, hit_time))
            elif isinstance(item, tuple) and len(item) >= 2:
                # Formato compatible: (key_number, hit_time) o (key_number, hit_time, duration)
                rhythm_chart.append(item)
        
        return rhythm_chart

    def start(self, virtual_keyboard=None, num_keys=24):
        """
        Reinicia el reloj y prepara las notas usando RhythmGame
        """
        self.running = True
        self.start_time = time.time()
        self.score = 0
        self.num_keys = num_keys
        self.active_chart = self.chart.copy()
        
        # Crear e inicializar RhythmGame
        self.rhythm_game = RhythmGame(num_keys=num_keys)
        
        # Convertir chart al formato de RhythmGame
        rhythm_chart = self._convert_chart_to_rhythm_format(self.chart, virtual_keyboard)
        
        # Iniciar el juego con el chart convertido
        self.rhythm_game.start_game(rhythm_chart)
        
        print(f"🎵 Iniciando: {self.name} ({self.bpm} BPM)")

    def stop(self):
        """Detiene la canción y el juego de ritmo"""
        self.running = False
        if self.rhythm_game:
            self.rhythm_game.stop_game()
        print(f"⏹ Deteniendo: {self.name}")

    def get_info(self):
        """Retorna información básica de la canción"""
        return {
            'name': self.name,
            'bpm': self.bpm,
            'difficulty': self.difficulty,
            'music_key': self.music_key
        }
    
    def get_song_state(self):
        """
        Devuelve el estado actual de la canción para PyQt6
        Similar a lesson.get_lesson_state()
        
        Returns:
            dict: Diccionario con 'score', 'combo', 'progress', 'stats'
        """
        if not self.rhythm_game:
            return {
                'score': 0,
                'combo': 0,
                'progress': 0,
                'stats': {}
            }
        
        # Calcular progreso basado en tiempo
        progress = 0
        if self.chart:
            current_time = time.time() - self.start_time
            last_note_time = max(item.get("time", 0) if isinstance(item, dict) else item[1] 
                                for item in self.chart)
            total_time = last_note_time + 2  # 2 segundos después de la última nota
            progress = min(100, int((current_time / total_time) * 100)) if total_time > 0 else 0
        
        return {
            'score': self.rhythm_game.score,
            'combo': self.rhythm_game.combo,
            'progress': progress,
            'stats': self.rhythm_game.get_final_score()
        }

    def run(self, frame_left, frame_right, virtual_keyboard, synth):
        """
        Actualiza el estado del juego de ritmo (NO dibuja)
        El dibujo se hace desde KeyboardProcessor usando rhythm_game.draw()
        
        Returns:
            (frame_left, frame_right, continue_song)
        """
        if not self.rhythm_game or not self.running:
            return frame_left, frame_right, False
        
        # Actualizar posición de notas
        self.rhythm_game.update()
        
        # Actualizar score desde rhythm_game
        self.score = self.rhythm_game.score
        
        # Verificar si el juego terminó
        if self.rhythm_game.is_game_finished():
            self.running = False
        
        return frame_left, frame_right, self.running
    
    # --- Ayudas Visuales (Igual que en Theory) ---

    def draw_header(self, frame):
        """Dibuja la barra superior con info de la canción"""
        h, w = frame.shape[:2]
        
        # Fondo oscuro semitransparente
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 60), (30, 20, 40), -1)
        cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)
        
        # Texto
        info_txt = f"{self.name} | BPM: {self.bpm} | Score: {self.score}"
        cv2.putText(frame, info_txt, (20, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Instrucciones de salida
        cv2.putText(frame, "Q: Salir", (w - 120, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        
        return frame