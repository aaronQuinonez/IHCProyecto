#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de códigos de teclas para OpenCV en Windows
Usa este script para identificar los códigos correctos de las flechas
"""

import cv2
import numpy as np

def test_keys():
    """Muestra los códigos de las teclas presionadas"""
    print("="*60)
    print("TEST DE CÓDIGOS DE TECLAS")
    print("="*60)
    print("\nPresiona teclas para ver sus códigos.")
    print("Presiona 'q' para salir.\n")
    print("Códigos esperados:")
    print("  Flecha ARRIBA: 82 (0x52)")
    print("  Flecha ABAJO:  84 (0x54)")
    print("  Flecha IZQ:    81 (0x51)")
    print("  Flecha DER:    83 (0x53)")
    print("  ENTER:         13 (0x0D)")
    print("  ESC:           27 (0x1B)")
    print("\n" + "="*60 + "\n")
    
    # Crear ventana
    window_name = "Test de Teclas - Presiona Q para salir"
    cv2.namedWindow(window_name)
    
    # Frame negro simple
    frame = np.zeros((300, 600, 3), dtype=np.uint8)
    
    last_key = None
    last_key_name = ""
    
    while True:
        # Limpiar frame
        frame[:] = (30, 30, 30)
        
        # Título
        cv2.putText(frame, "Presiona cualquier tecla", (150, 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # Mostrar última tecla presionada
        if last_key is not None:
            info_text = f"Codigo: {last_key} (0x{last_key:02X})"
            cv2.putText(frame, info_text, (150, 120),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            if last_key_name:
                cv2.putText(frame, last_key_name, (150, 170),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (100, 255, 255), 2)
        
        # Instrucción
        cv2.putText(frame, "Q = Salir", (230, 250),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        
        cv2.imshow(window_name, frame)
        
        # Capturar tecla
        key = cv2.waitKey(100) & 0xFF
        
        if key != 255:  # Se presionó alguna tecla
            last_key = key
            
            # Identificar tecla
            if key == 82:
                last_key_name = "FLECHA ARRIBA"
            elif key == 84:
                last_key_name = "FLECHA ABAJO"
            elif key == 81:
                last_key_name = "FLECHA IZQUIERDA"
            elif key == 83:
                last_key_name = "FLECHA DERECHA"
            elif key == 13:
                last_key_name = "ENTER"
            elif key == 27:
                last_key_name = "ESC"
            elif 32 <= key <= 126:  # Caracteres imprimibles
                last_key_name = f"Tecla: '{chr(key)}'"
            else:
                last_key_name = "Tecla especial"
            
            print(f"Tecla presionada: {last_key} (0x{last_key:02X}) - {last_key_name}")
            
            if key == ord('q') or key == ord('Q'):
                print("\nSaliendo...")
                break
    
    cv2.destroyAllWindows()
    print("\n" + "="*60)
    print("Test finalizado.")
    print("="*60)

if __name__ == '__main__':
    test_keys()
