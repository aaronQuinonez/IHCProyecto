from src.songs.song_base import BaseSong

class MelodyComplexSong(BaseSong):
    """
    Canción compleja y larga para probar el sistema
    Incluye melodía, acordes y patrones rítmicos variados
    """
    name = "Melodía Compleja"
    bpm = 140
    difficulty = "Avanzado"
    music_key = "C Major"
    scroll_speed = 1.0

    # Melodía completa con patrones variados
    chart = [
        # Introducción (0-4 segundos)
        { "time": 1.0, "keys": ["C"] },
        { "time": 1.5, "keys": ["E"] },
        { "time": 2.0, "keys": ["G"] },
        { "time": 2.5, "keys": ["C5"] },
        
        # Primera frase melódica (4-8 segundos)
        { "time": 4.0, "keys": ["C"] },
        { "time": 4.3, "keys": ["D"] },
        { "time": 4.6, "keys": ["E"] },
        { "time": 5.0, "keys": ["F"] },
        { "time": 5.3, "keys": ["G"] },
        { "time": 5.6, "keys": ["A"] },
        { "time": 6.0, "keys": ["B"] },
        { "time": 6.5, "keys": ["C5"] },
        
        # Acordes y melodía (8-12 segundos)
        { "time": 8.0, "keys": ["C", "E", "G"] },  # C mayor
        { "time": 8.5, "keys": ["C"] },
        { "time": 9.0, "keys": ["A", "C", "E"] },  # Am
        { "time": 9.5, "keys": ["A"] },
        { "time": 10.0, "keys": ["F", "A", "C"] },  # F
        { "time": 10.5, "keys": ["F"] },
        { "time": 11.0, "keys": ["G", "B", "D"] },  # G
        { "time": 11.5, "keys": ["G"] },
        
        # Patrón rítmico rápido (12-16 segundos)
        { "time": 12.0, "keys": ["C"] },
        { "time": 12.2, "keys": ["E"] },
        { "time": 12.4, "keys": ["G"] },
        { "time": 12.6, "keys": ["C5"] },
        { "time": 13.0, "keys": ["D"] },
        { "time": 13.2, "keys": ["F"] },
        { "time": 13.4, "keys": ["A"] },
        { "time": 13.6, "keys": ["C5"] },
        { "time": 14.0, "keys": ["E"] },
        { "time": 14.2, "keys": ["G"] },
        { "time": 14.4, "keys": ["B"] },
        { "time": 14.6, "keys": ["D5"] },
        { "time": 15.0, "keys": ["C", "E", "G", "C5"] },  # Acorde completo
        
        # Melodía con saltos (16-20 segundos)
        { "time": 16.0, "keys": ["C"] },
        { "time": 16.5, "keys": ["G"] },
        { "time": 17.0, "keys": ["C5"] },
        { "time": 17.5, "keys": ["G"] },
        { "time": 18.0, "keys": ["E"] },
        { "time": 18.5, "keys": ["C"] },
        { "time": 19.0, "keys": ["G"] },
        { "time": 19.5, "keys": ["C5"] },
        
        # Progresión de acordes (20-24 segundos)
        { "time": 20.0, "keys": ["C", "E", "G"] },
        { "time": 20.8, "keys": ["A", "C", "E"] },
        { "time": 21.6, "keys": ["F", "A", "C"] },
        { "time": 22.4, "keys": ["G", "B", "D"] },
        { "time": 23.2, "keys": ["C", "E", "G"] },
        
        # Final con escalas (24-28 segundos)
        { "time": 24.0, "keys": ["C"] },
        { "time": 24.2, "keys": ["D"] },
        { "time": 24.4, "keys": ["E"] },
        { "time": 24.6, "keys": ["F"] },
        { "time": 24.8, "keys": ["G"] },
        { "time": 25.0, "keys": ["A"] },
        { "time": 25.2, "keys": ["B"] },
        { "time": 25.4, "keys": ["C5"] },
        { "time": 25.6, "keys": ["D5"] },
        { "time": 25.8, "keys": ["E5"] },
        { "time": 26.0, "keys": ["C", "E", "G", "C5", "E5"] },  # Acorde extendido
        { "time": 26.5, "keys": ["C5"] },
        { "time": 27.0, "keys": ["G"] },
        { "time": 27.5, "keys": ["E"] },
        { "time": 28.0, "keys": ["C"] },
    ]
    
    # No necesita método run() personalizado
    # El dibujo se hace automáticamente desde RhythmGame

