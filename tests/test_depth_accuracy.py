import cv2
import sys
import os
import time
import numpy as np

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.vision.depth_estimator import DepthEstimator
from src.vision.hand_detector import HandDetector
from src.config.app_config import AppConfig
from src.vision.stereo_config import StereoConfig

def main():
    print("=== TEST DE PRECISIÓN DE PROFUNDIDAD ===")
    print("Este script usa la calibración actual para medir la profundidad de tu dedo índice.")
    print("Presiona 'q' para salir.")

    # 1. Cargar Calibración
    calib_file = "camcalibration/calibration.json"
    if not os.path.exists(calib_file):
        print(f"ERROR: No se encontró {calib_file}")
        return

    try:
        depth_estimator = DepthEstimator(calib_file)
        print("Calibración cargada correctamente.")
    except Exception as e:
        print(f"Error cargando calibración: {e}")
        return

    # 2. Iniciar Cámaras usando configuración centralizada
    print(f"Abriendo cámaras: Izquierda={StereoConfig.LEFT_CAMERA_SOURCE}, Derecha={StereoConfig.RIGHT_CAMERA_SOURCE}")
    cap_left = cv2.VideoCapture(StereoConfig.LEFT_CAMERA_SOURCE, cv2.CAP_DSHOW)
    cap_right = cv2.VideoCapture(StereoConfig.RIGHT_CAMERA_SOURCE, cv2.CAP_DSHOW)

    if not cap_left.isOpened() or not cap_right.isOpened():
        print("Error abriendo cámaras.")
        return

    # Configurar resolución (importante que coincida con calibración)
    width = StereoConfig.PIXEL_WIDTH
    height = StereoConfig.PIXEL_HEIGHT
    
    cap_left.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap_left.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap_right.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap_right.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    # 3. Detectores de Manos
    detector_left = HandDetector()
    detector_right = HandDetector()

    while True:
        ret_l, frame_left = cap_left.read()
        ret_r, frame_right = cap_right.read()

        if not ret_l or not ret_r:
            print("Error leyendo frames.")
            break

        # Espejo (opcional, pero usual en UI)
        # frame_left = cv2.flip(frame_left, 1)
        # frame_right = cv2.flip(frame_right, 1) 
        # NOTA: Si hacemos flip, las coordenadas cambian. 
        # DepthEstimator espera coordenadas originales de la imagen o rectificadas.
        # Mantengamos sin flip para probar la precisión pura.

        # Detectar manos
        detector_left.findHands(frame_left)
        detector_right.findHands(frame_right)

        lm_left, tips_left = detector_left.getFingerTipsPos()
        lm_right, tips_right = detector_right.getFingerTipsPos()

        # Dibujar
        detector_left.drawHands(frame_left)
        detector_left.drawTips(frame_left)

        # Calcular profundidad si hay coincidencia
        if len(tips_left) > 0 and len(tips_right) > 0:
            # Buscar dedo índice (ID 8)
            idx_l = next((t for t in tips_left if t[1] == 8), None)
            idx_r = next((t for t in tips_right if t[1] == 8), None)

            if idx_l and idx_r:
                # idx_l = [hand_id, finger_id, x, y]
                pt_left = (idx_l[2], idx_l[3])
                pt_right = (idx_r[2], idx_r[3])

                # Estimar profundidad
                # 1. Rectificar puntos
                pt_left_rect = depth_estimator.rectify_point(pt_left, 'left')
                pt_right_rect = depth_estimator.rectify_point(pt_right, 'right')

                # 2. Triangular
                point_3d = depth_estimator.triangulate_point(pt_left_rect, pt_right_rect)
                    
                if point_3d is not None:
                    x, y, z = point_3d
                    cv2.putText(frame_left, f"Z: {z:.2f} cm", (50, 50), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.putText(frame_left, f"X: {x:.2f} Y: {y:.2f}", (50, 90), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)


        cv2.imshow("Test Depth - Left Camera", frame_left)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap_left.release()
    cap_right.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
