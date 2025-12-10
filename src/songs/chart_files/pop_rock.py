from src.songs.song_base import BaseSong

class PopRockSong(BaseSong):
    """
    Canción estilo Pop Rock con ritmo intermedio
    """
    name = "Pop Rock Style"
    bpm = 120
    difficulty = "Intermedio"
    music_key = "A Minor"
    scroll_speed = 1.2  # Un poco más rápido

    # El "mapa" de la canción
    chart = [
        { "time": 1.0, "keys": ["A"] },
        { "time": 1.5, "keys": ["A"] },
        { "time": 2.0, "keys": ["C"] },
        { "time": 3.0, "keys": ["E"] },
        { "time": 4.0, "keys": ["A", "C", "E"] },  # Acorde Am
        { "time": 5.0, "keys": ["G"] },
        { "time": 5.5, "keys": ["G"] },
        { "time": 6.0, "keys": ["A"] },
    ]
    
    # No necesita método run() personalizado
    # El dibujo se hace automáticamente desde RhythmGame