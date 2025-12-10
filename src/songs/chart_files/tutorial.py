from src.songs.song_base import BaseSong

class TutorialSong(BaseSong):
    """
    Canción tutorial básica para aprender
    """
    name = "Tutorial Básico"
    bpm = 100
    difficulty = "Básico"
    music_key = "C"
    
    # Definimos cuando caen las notas
    # Formato: { "time": segundos_desde_inicio, "keys": ["nota1", "nota2", ...] }
    chart = [
        { "time": 2.0, "keys": ["C"] },
        { "time": 3.0, "keys": ["D"] },
        { "time": 4.0, "keys": ["E"] },
        { "time": 5.0, "keys": ["F"] },
        { "time": 6.0, "keys": ["G"] },
        { "time": 7.0, "keys": ["A"] },
        { "time": 8.0, "keys": ["B"] },
        { "time": 9.0, "keys": ["C", "E", "G"] },  # Acorde C mayor
    ]
    
    # No necesita método run() personalizado
    # El dibujo se hace automáticamente desde RhythmGame