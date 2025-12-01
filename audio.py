#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de diagnóstico para audio - Detecta dónde falla el sonido
"""

import sys
import numpy as np

print("\n" + "="*70)
print("DIAGNÓSTICO DE AUDIO - PASO A PASO")
print("="*70 + "\n")

# PASO 1: Verificar FluidSynth
print("PASO 1: Verificando FluidSynth...")
try:
    import fluidsynth
    print("✓ FluidSynth importado correctamente")
except ImportError as e:
    print(f"✗ ERROR: FluidSynth no instalado: {e}")
    print("  Instala con: pip install pyfluidsynth")
    sys.exit(1)

# PASO 2: Verificar configuración
print("\nPASO 2: Verificando configuración...")
try:
    from src.vision.stereo_config import StereoConfig
    config = StereoConfig()
    print(f"✓ Config cargada")
    print(f"  - Soundfont: {config.SOUNDFONT_PATH}")
    
    import os
    if os.path.exists(config.SOUNDFONT_PATH):
        print(f"✓ Archivo de soundfont existe")
    else:
        print(f"✗ ERROR: Soundfont NO existe en: {config.SOUNDFONT_PATH}")
        sys.exit(1)
except Exception as e:
    print(f"✗ ERROR en config: {e}")
    sys.exit(1)

# PASO 3: Inicializar Synth
print("\nPASO 3: Inicializando Synth...")
try:
    fs = fluidsynth.Synth()
    print("✓ Synth creado")
except Exception as e:
    print(f"✗ ERROR al crear Synth: {e}")
    sys.exit(1)

# PASO 4: Iniciar driver
print("\nPASO 4: Iniciando driver de audio...")
try:
    fs.start(driver='dsound')  # Windows
    print("✓ Driver dsound iniciado")
except Exception as e:
    print(f"⚠ Error con dsound, intentando con otros drivers...")
    try:
        fs.start()
        print("✓ Driver automático iniciado")
    except Exception as e2:
        print(f"✗ ERROR al iniciar driver: {e2}")
        sys.exit(1)

# PASO 5: Cargar soundfont
print("\nPASO 5: Cargando soundfont...")
try:
    sfid = fs.sfload(config.SOUNDFONT_PATH)
    print(f"✓ Soundfont cargado (ID: {sfid})")
except Exception as e:
    print(f"✗ ERROR al cargar soundfont: {e}")
    fs.delete()
    sys.exit(1)

# PASO 6: Seleccionar instrumento
print("\nPASO 6: Seleccionando instrumento...")
try:
    fs.program_select(chan=0, sfid=sfid, bank=0, preset=0)
    print("✓ Instrumento Piano seleccionado (bank=0, preset=0)")
except Exception as e:
    print(f"✗ ERROR al seleccionar instrumento: {e}")
    fs.delete()
    sys.exit(1)

# PASO 7: Probar notas individuales
print("\nPASO 7: Probando notas MIDI...")
import time

notas_test = [
    (60, "Do"),
    (62, "Re"),
    (64, "Mi"),
    (65, "Fa"),
    (67, "Sol"),
]

for midi_note, nombre in notas_test:
    try:
        print(f"  Tocando {nombre} (MIDI {midi_note})...", end=" ", flush=True)
        fs.noteon(chan=0, key=midi_note, vel=100)
        time.sleep(0.5)
        fs.noteoff(chan=0, key=midi_note)
        print("✓")
    except Exception as e:
        print(f"✗ Error: {e}")

# PASO 8: Verificar VirtualKeyboard
print("\nPASO 8: Verificando VirtualKeyboard...")
try:
    from src.piano.virtual_keyboard import VirtualKeyboard
    vk = VirtualKeyboard(640, 480)
    print("✓ VirtualKeyboard creado")
    
    # Probar note_from_key
    for key_pos in [0, 7, 14, 21]:
        nota = vk.note_from_key(key_pos)
        print(f"  - Tecla {key_pos} → MIDI {nota}")
except Exception as e:
    print(f"✗ ERROR: {e}")
    import traceback
    traceback.print_exc()

# PASO 9: Verificar KeyboardMap
print("\nPASO 9: Verificando KeyboardMap...")
try:
    from src.vision.keyboard_mapper import KeyboardMap
    km = KeyboardMap(depth_threshold=2.5)
    
    # Crear array de prueba
    fingertips = [[0, 8, 100, 200]]  # Hand 0, tip 8, pos (100, 200)
    finger_depths = {(0, 8): 2.0}  # Profundidad 2.0 cm (debe presionar)
    
    on_map, off_map = km.get_kayboard_map(
        virtual_keyboard=vk,
        fingertips_pos=fingertips,
        finger_depths=finger_depths,
        keyboard_n_key=38
    )
    
    print("✓ KeyboardMap funcionando")
    print(f"  - on_map shape: {on_map.shape}, dtype: {on_map.dtype}")
    print(f"  - off_map shape: {off_map.shape}, dtype: {off_map.dtype}")
    print(f"  - on_map contiene True: {np.any(on_map)}")
    print(f"  - Teclas presionadas: {np.where(on_map)[0].tolist()}")
except Exception as e:
    print(f"✗ ERROR: {e}")
    import traceback
    traceback.print_exc()

# PASO 10: Simular envío de notas (como en main.py)
print("\nPASO 10: Simulando envío de notas (como en main.py)...")
try:
    print("Simulando on_map con teclas 5 y 10 presionadas...")
    
    on_map_test = np.full(38, False, dtype=bool)
    on_map_test[5] = True
    on_map_test[10] = True
    
    octave_base = 0
    
    print(f"np.any(on_map_test) = {np.any(on_map_test)}")
    
    if np.any(on_map_test):
        print("✓ Condición np.any(on_map) es TRUE")
        for k_pos, on_key in enumerate(on_map_test):
            if on_key:
                note = vk.note_from_key(k_pos) + octave_base
                print(f"  Enviando noteon: tecla {k_pos} → MIDI {note}...", end=" ", flush=True)
                fs.noteon(chan=0, key=note, vel=127*2//3)
                time.sleep(0.3)
                fs.noteoff(chan=0, key=note)
                print("✓")
    else:
        print("✗ Condición np.any(on_map) es FALSE")
        
except Exception as e:
    print(f"✗ ERROR: {e}")
    import traceback
    traceback.print_exc()

# Cleanup
print("\nLimpiando recursos...")
try:
    fs.delete()
    print("✓ Synth eliminado")
except:
    pass

print("\n" + "="*70)
print("DIAGNÓSTICO COMPLETADO")
print("="*70 + "\n")

print("Si NO escuchaste sonido en PASO 7 o PASO 10:")
print("  1. Verifica que el volumen del PC está alto")
print("  2. Verifica que los altavoces están conectados")
print("  3. Verifica que FluidSynth tiene permisos de audio")
print("\nSi escuchaste en PASO 7 pero NO en PASO 10:")
print("  El problema está en la detección de dedos/profundidad")
print("\n")