
import cv2
import sys
import os

# Añadir src al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

try:
    from src.vision.aruco_detector import generate_aruco_marker
    from src.vision.stereo_config import StereoConfig
    
    marker_id = StereoConfig.ARUCO_MARKER_ID
    dictionary = StereoConfig.ARUCO_DICTIONARY
    
    print(f"Generando marcador ArUco ID={marker_id} ({dictionary})...")
    
    output_file = f"aruco_marker_id{marker_id}.png"
    generate_aruco_marker(
        marker_id=marker_id,
        dictionary_name=dictionary,
        size_pixels=1000,
        output_path=output_file
    )
    
    print(f"¡Éxito! Imagen guardada en: {os.path.abspath(output_file)}")

except ImportError as e:
    print(f"Error importando módulos: {e}")
    # Fallback si falla el import
    import cv2.aruco as aruco
    import numpy as np
    
    id_fallback = 0
    dict_fallback = cv2.aruco.DICT_4X4_50
    print(f"Usando fallback: ID={id_fallback}, Dict=4X4_50")
    
    aruco_dict = cv2.aruco.getPredefinedDictionary(dict_fallback)
    img = cv2.aruco.generateImageMarker(aruco_dict, id_fallback, 1000)
    
    # Border
    img = cv2.copyMakeBorder(img, 50, 50, 50, 50, cv2.BORDER_CONSTANT, value=255)
    cv2.imwrite("aruco_marker_id0_fallback.png", img)
    print("Guardado aruco_marker_id0_fallback.png")
