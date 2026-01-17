
import cv2
import cv2.aruco as aruco
import numpy as np
from PIL import Image, ImageOps
import os
import sys

# Añadir src al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

try:
    from src.vision.stereo_config import StereoConfig
    marker_id = StereoConfig.ARUCO_MARKER_ID
    dictionary_name = StereoConfig.ARUCO_DICTIONARY
    target_size_cm = StereoConfig.ARUCO_MARKER_SIZE_CM
except:
    marker_id = 0
    dictionary_name = "4X4_50"
    target_size_cm = 15.0

def create_aruco_pdf():
    print(f"Generando PDF para ArUco ID={marker_id} ({dictionary_name})...")
    
    # 1. Generar imagen ArUco con OpenCV
    dict_id = cv2.aruco.DICT_4X4_50 # Default safe
    if hasattr(cv2.aruco, f"DICT_{dictionary_name}"):
        dict_id = getattr(cv2.aruco, f"DICT_{dictionary_name}")
    
    aruco_dict = cv2.aruco.getPredefinedDictionary(dict_id)
    
    # Alta resolución para impresión (Ej. 2000x2000 px)
    # A4 a 300 DPI es ~2480 x 3508 px
    # 15cm a 300 DPI (118 px/cm) es ~1770 px
    marker_px = int(target_size_cm * 118) 
    
    marker_img = cv2.aruco.generateImageMarker(aruco_dict, marker_id, marker_px)
    
    # 2. Convertir a PIL
    # OpenCV genera grayscale 0-255.
    pil_img = Image.fromarray(marker_img)
    
    # 3. Crear canvas A4 (blanco)
    # A4 @ 300 DPI = 2480 x 3508 px
    a4_w, a4_h = 2480, 3508
    page = Image.new('RGB', (a4_w, a4_h), (255, 255, 255))
    
    # 4. Pegar marcador centrado
    pos_x = (a4_w - marker_px) // 2
    pos_y = (a4_h - marker_px) // 2
    
    page.paste(pil_img, (pos_x, pos_y))
    
    # 5. Añadir texto informativo (opcional, básico)
    # Sin fuentes externas es difícil centrar texto bonito con PIL puro sin cargar TTF.
    # Simplemente guardamos así.
    
    output_filename = "aruco_print_a4.pdf"
    page.save(output_filename, "PDF", resolution=300.0)
    
    print(f"LISTO: {os.path.abspath(output_filename)}")

if __name__ == "__main__":
    create_aruco_pdf()
