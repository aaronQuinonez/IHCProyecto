# Formato de Canciones para el Modo Ritmo

## Estructura Básica

Cada canción debe ser una clase que herede de `BaseSong`:

```python
from src.songs.song_base import BaseSong

class MiCancion(BaseSong):
    name = "Nombre de la Canción"
    bpm = 120  # Beats por minuto
    difficulty = "Básico"  # "Básico", "Intermedio", "Avanzado"
    music_key = "C Major"  # Tonalidad
    scroll_speed = 1.0  # Velocidad de scroll (1.0 = normal)
    
    chart = [
        { "time": 1.0, "keys": ["C"] },
        { "time": 2.0, "keys": ["D", "E"] },  # Acorde
        # ... más notas
    ]
```

## Formato del Chart

El `chart` es una lista de diccionarios con la siguiente estructura:

```python
{ "time": segundos_desde_inicio, "keys": ["nota1", "nota2", ...] }
```

### Parámetros:

- **time**: Tiempo en segundos desde el inicio de la canción (float)
- **keys**: Lista de notas musicales a tocar simultáneamente (lista de strings)

### Notas Musicales Soportadas:

- **Notas básicas**: `"C"`, `"D"`, `"E"`, `"F"`, `"G"`, `"A"`, `"B"`
- **Sostenidos**: `"C#"`, `"D#"`, `"F#"`, `"G#"`, `"A#"`
- **Bemoles**: `"Db"`, `"Eb"`, `"Gb"`, `"Ab"`, `"Bb"`
- **Octavas**: `"C4"`, `"C5"`, etc. (por defecto es C4)

### Ejemplos:

```python
# Nota simple
{ "time": 1.0, "keys": ["C"] }

# Acorde (múltiples notas simultáneas)
{ "time": 2.0, "keys": ["C", "E", "G"] }

# Nota con sostenido
{ "time": 3.0, "keys": ["C#"] }

# Nota en segunda octava
{ "time": 4.0, "keys": ["C5"] }

# Patrón rítmico rápido
{ "time": 5.0, "keys": ["C"] },
{ "time": 5.2, "keys": ["E"] },
{ "time": 5.4, "keys": ["G"] },
```

## Mapeo de Teclas del Piano

El piano virtual tiene **24 teclas** (0-23) que cubren 2 octavas:

- **Teclas 0-11**: Primera octava (C4=60 a B4=71 en MIDI)
- **Teclas 12-23**: Segunda octava (C5=72 a B5=83 en MIDI)

### Mapeo de Notas a Teclas:

| Nota | Tecla | MIDI | Nota | Tecla | MIDI |
|------|-------|------|------|-------|------|
| C    | 0     | 60   | C5   | 12    | 72   |
| C#   | 1     | 61   | C#5  | 13    | 73   |
| D    | 2     | 62   | D5   | 14    | 74   |
| D#   | 3     | 63   | D#5  | 15    | 75   |
| E    | 4     | 64   | E5   | 16    | 76   |
| F    | 5     | 65   | F5   | 17    | 77   |
| F#   | 6     | 66   | F#5  | 18    | 78   |
| G    | 7     | 67   | G5   | 19    | 79   |
| G#   | 8     | 68   | G#5  | 20    | 80   |
| A    | 9     | 69   | A5   | 21    | 81   |
| A#   | 10    | 70   | A#5  | 22    | 82   |
| B    | 11    | 71   | B5   | 23    | 83   |

## Consejos para Crear Canciones

1. **Tiempo**: Usa valores decimales para tiempos precisos (ej: 1.5, 2.3)
2. **Acordes**: Puedes tocar múltiples notas simultáneamente
3. **Patrones**: Crea patrones rítmicos variados para hacer la canción interesante
4. **Dificultad**: 
   - **Básico**: Notas simples, tiempos espaciados (1-2 segundos)
   - **Intermedio**: Acordes, patrones rítmicos, tiempos más cercanos (0.5-1 segundo)
   - **Avanzado**: Acordes complejos, patrones rápidos, tiempos muy cercanos (0.2-0.5 segundos)

## Ejemplo Completo

```python
from src.songs.song_base import BaseSong

class MiCancionEjemplo(BaseSong):
    name = "Mi Canción de Prueba"
    bpm = 120
    difficulty = "Intermedio"
    music_key = "C Major"
    
    chart = [
        # Introducción
        { "time": 1.0, "keys": ["C"] },
        { "time": 2.0, "keys": ["E"] },
        { "time": 3.0, "keys": ["G"] },
        
        # Acorde
        { "time": 4.0, "keys": ["C", "E", "G"] },
        
        # Patrón rítmico
        { "time": 5.0, "keys": ["C"] },
        { "time": 5.5, "keys": ["E"] },
        { "time": 6.0, "keys": ["G"] },
        { "time": 6.5, "keys": ["C5"] },
        
        # Final
        { "time": 7.0, "keys": ["C", "E", "G", "C5"] },
    ]
```

## Notas Importantes

- **NO dibujes manualmente**: El sistema dibuja automáticamente las notas como teclas cayendo
- **NO necesitas método `run()`**: `BaseSong` ya maneja todo automáticamente
- **El chart se convierte automáticamente**: Las notas se convierten a números de tecla automáticamente
- **Tiempo mínimo**: Usa al menos 0.2 segundos entre notas para que sean distinguibles

