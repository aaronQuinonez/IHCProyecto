import cv2

print("\n============== BUSCANDO CAMARAS ==============\n")

for i in range(10):
    cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
    
    if not cap.isOpened():
        print(f"[{i}] No disponible")
        continue

    ret, frame = cap.read()

    # Obtener nombre REAL de la cámara
    backend = cap.getBackendName()
    w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

    print(f"[{i}] Disponible | Backend: {backend} | {int(w)}x{int(h)} | frame={ret}")

    cap.release()

print("\n================================================\n")
