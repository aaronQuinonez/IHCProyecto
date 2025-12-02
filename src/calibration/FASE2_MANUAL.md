# 🎯 FASE 2: Calibración Estéreo

## 📋 Objetivo

Determinar la **posición y orientación relativa** entre ambas cámaras. Esto permite:
- Calcular la distancia entre las cámaras (**baseline**)
- Conocer la rotación relativa entre ellas
- Obtener la matriz fundamental (F) y esencial (E)
- Generar mapas de rectificación para triangulación 3D

---

## 🔄 Diferencia entre Fase 1 y Fase 2

### Fase 1 (Calibración Individual)
- ✅ **Ya completada**: Calibraste ambas cámaras por separado
- 📸 **25 fotos cada una** moviendo el tablero en diferentes posiciones
- 🎯 **Resultado**: Parámetros intrínsecos (K, D) de cada cámara
- 📊 **Errores obtenidos**: 
  - Cámara izquierda: 0.0667 px
  - Cámara derecha: 0.0878 px

### Fase 2 (Calibración Estéreo)
- 🎬 **Ahora**: Captura **simultánea** con ambas cámaras
- 📸 **8 a 15 pares** mostrando el mismo tablero desde ambas cámaras
- 🎯 **Resultado**: Parámetros extrínsecos (R, T, E, F)
- 📏 **Baseline**: Distancia real entre las cámaras en centímetros

---

## 📸 ¿Cómo capturar en Fase 2?

### Setup físico
```
        [Cámara Izq]    [Cámara Der]
              ↓              ↓
         ╔═════════════════════════╗
         ║                         ║
         ║      📋 Tablero 8x8     ║
         ║                         ║
         ╚═════════════════════════╝
```

### Instrucciones paso a paso

1. **Posiciona el tablero** frente a ambas cámaras
   - Debe ser visible en **AMBAS** pantallas simultáneamente
   - Mantén distancia: 40-80 cm aproximadamente

2. **Verifica la detección**
   - El sistema mostrará ambas vistas lado a lado
   - Espera a que aparezcan las esquinas verdes en **AMBAS**
   - Mensaje: "LISTO PARA CAPTURAR" cuando esté estable

3. **Captura el par**
   - Presiona **ESPACIO**
   - Se guardará el par simultáneo

4. **Varía la posición**
   - Mueve el tablero a otra posición/ángulo
   - Captura otro par
   - Repite hasta tener 8-15 pares

5. **Finaliza**
   - Presiona **ESC** cuando tengas suficientes pares (mínimo 8)

---

## 📏 Variaciones recomendadas

Para obtener buena calibración estéreo, captura el tablero en:

### Posiciones (4-5 capturas)
- Centro del campo de visión
- Cerca del borde izquierdo
- Cerca del borde derecho
- Parte superior
- Parte inferior

### Distancias (3-4 capturas)
- Cerca (40 cm)
- Medio (60 cm)
- Lejos (80 cm)

### Ángulos (3-4 capturas)
- Frontal (perpendicular)
- Rotado 30° hacia izquierda
- Rotado 30° hacia derecha
- Inclinado hacia arriba/abajo

---

## 🔬 ¿Qué calcula `cv2.stereoCalibrate()`?

### Matriz de Rotación (R) - 3x3
Describe cómo está rotada la cámara derecha respecto a la izquierda.
```
R = [[r11, r12, r13],
     [r21, r22, r23],
     [r31, r32, r33]]
```

### Vector de Traslación (T) - 3x1
Describe la posición de la cámara derecha respecto a la izquierda.
```
T = [[tx],   ← Separación horizontal (baseline)
     [ty],   ← Desplazamiento vertical
     [tz]]   ← Profundidad
```

**Baseline** = `sqrt(tx² + ty² + tz²)` ≈ distancia entre cámaras

### Matriz Esencial (E) - 3x3
Relaciona puntos correspondientes en coordenadas normalizadas:
```
E = [T]× · R
```
Donde `[T]×` es la matriz antisimétrica de T.

### Matriz Fundamental (F) - 3x3
Similar a E, pero trabaja en píxeles (no normalizado):
```
p_right^T · F · p_left = 0
```
Para cualquier punto correspondiente en ambas imágenes.

---

## 📊 Interpretación de resultados

### Error RMS estéreo
- **< 0.5**: Excelente
- **0.5 - 1.0**: Bueno
- **1.0 - 2.0**: Aceptable
- **> 2.0**: Revisar setup

### Baseline típico
- **5-10 cm**: Setup estándar de escritorio
- **10-15 cm**: Comparable a separación entre ojos humanos
- **15-25 cm**: Para mayor precisión en profundidad

---

## 🎮 Parámetros de Rectificación

Después de `stereoCalibrate()`, se calculan con `stereoRectify()`:

### R1, R2 (Matrices 3x3)
Rotaciones para enderezar cada imagen.

### P1, P2 (Matrices 3x4)
Nuevas matrices de proyección después de rectificación.

### Q (Matriz 4x4)
**Matriz de reproyección**: Convierte disparidad en profundidad 3D.

```python
[X]       [x_left]
[Y] = Q · [y_left]
[Z]       [disparity]
[W]       [1]
```

Luego: `X/W, Y/W, Z/W` = coordenadas 3D reales

---

## 🛠️ Uso después de calibración

Una vez completada la Fase 2, puedes:

1. **Cargar calibración**:
```python
from calibration import CalibrationManager
data = CalibrationManager.load_calibration()

# Parámetros intrínsecos (Fase 1)
K_left = np.array(data['left_camera']['camera_matrix'])
D_left = np.array(data['left_camera']['distortion_coeffs'])
K_right = np.array(data['right_camera']['camera_matrix'])
D_right = np.array(data['right_camera']['distortion_coeffs'])

# Parámetros extrínsecos (Fase 2)
R = np.array(data['stereo']['rotation_matrix'])
T = np.array(data['stereo']['translation_vector'])
Q = np.array(data['stereo']['rectification']['Q'])
```

2. **Rectificar imágenes**:
```python
# Crear mapas de rectificación (una vez)
map1_left, map2_left = cv2.initUndistortRectifyMap(
    K_left, D_left, R1, P1, image_size, cv2.CV_32FC1
)
map1_right, map2_right = cv2.initUndistortRectifyMap(
    K_right, D_right, R2, P2, image_size, cv2.CV_32FC1
)

# Aplicar rectificación (cada frame)
left_rect = cv2.remap(left_frame, map1_left, map2_left, cv2.INTER_LINEAR)
right_rect = cv2.remap(right_frame, map1_right, map2_right, cv2.INTER_LINEAR)
```

3. **Calcular disparidad**:
```python
stereo = cv2.StereoSGBM_create(
    minDisparity=0,
    numDisparities=64,
    blockSize=5
)
disparity = stereo.compute(left_rect_gray, right_rect_gray)
```

4. **Obtener nube de puntos 3D**:
```python
points_3D = cv2.reprojectImageTo3D(disparity, Q)
```

---

## 🚨 Troubleshooting

### "✗ Error al abrir las cámaras"
- Verifica que ambas cámaras estén conectadas
- Cierra otras aplicaciones que usen las cámaras
- Revisa los IDs en `stereo_config.py`

### "Buscando tablero en ambas cámaras..."
- Asegúrate de que el tablero esté **completamente visible** en ambas
- Mejora la iluminación
- Aleja/acerca el tablero
- Evita reflejos en el tablero

### "✗ Cancelado. Se necesitan al menos 8 pares"
- No puedes finalizar con menos de 8 pares
- Captura más posiciones antes de presionar ESC

### Error RMS alto (> 2.0)
- Recaptura con más variación de posiciones
- Verifica que la Fase 1 esté bien calibrada
- Asegúrate de que las cámaras estén fijas durante captura

---

## 📚 Referencias teóricas

- [OpenCV Stereo Calibration](https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html#ga246253dcc6de2e0376c599e7d692303a)
- [Stereo Vision Tutorial](https://docs.opencv.org/4.x/dd/d53/tutorial_py_depthmap.html)
- [Multiple View Geometry (Hartley & Zisserman)](http://www.robots.ox.ac.uk/~vgg/hzbook/)

---

## ✅ Checklist Fase 2

- [ ] Fase 1 completada con errores < 0.1 px en ambas cámaras
- [ ] Tablero 8x8 disponible y medido
- [ ] Ambas cámaras conectadas y funcionando
- [ ] Iluminación uniforme configurada
- [ ] Capturados 8-15 pares simultáneos con variación
- [ ] Error RMS estéreo < 1.0
- [ ] Baseline coherente con tu setup físico
- [ ] Datos guardados en `calibration.json`
- [ ] Parámetros de rectificación calculados

---

**¡Listo para usar visión estéreo en tu proyecto!** 🎉
