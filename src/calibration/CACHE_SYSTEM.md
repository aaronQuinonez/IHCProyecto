# 💾 Sistema de Caché de Calibración

## 🎯 Problema Resuelto

**Antes**: Cada vez que ejecutabas el programa, tenías que recalibrar las cámaras (50+ fotos, 10+ minutos).

**Ahora**: El sistema detecta automáticamente si ya existe una calibración válida y te permite:
- ✅ **Usarla directamente** → Empiezas a jugar de inmediato
- 🔄 **Re-calibrar completamente** → Borra todo y empieza desde cero
- 📸 **Completar solo Fase 2** → Si solo falta calibración estéreo

---

## 📁 Archivo de Caché

**Ubicación**: `camcalibration/calibration.json`

**Contenido**:
```json
{
  "version": "2.0",
  "board_config": {
    "cols": 7,
    "rows": 7,
    "square_size_mm": 30.0
  },
  "left_camera": {
    "camera_matrix": [[fx, 0, cx], [0, fy, cy], [0, 0, 1]],
    "distortion_coeffs": [k1, k2, p1, p2, k3],
    "reprojection_error": 0.0667,
    "num_images": 25,
    "image_width": 1280,
    "image_height": 720
  },
  "right_camera": {
    "camera_matrix": [[fx, 0, cx], [0, fy, cy], [0, 0, 1]],
    "distortion_coeffs": [k1, k2, p1, p2, k3],
    "reprojection_error": 0.0878,
    "num_images": 25,
    "image_width": 1280,
    "image_height": 720
  },
  "stereo": {
    "rotation_matrix": [[r11, r12, r13], ...],
    "translation_vector": [[tx], [ty], [tz]],
    "essential_matrix": [...],
    "fundamental_matrix": [...],
    "rms_error": 0.45,
    "baseline_cm": 12.34,
    "num_pairs": 10,
    "rectification": {
      "R1": [...],
      "R2": [...],
      "P1": [...],
      "P2": [...],
      "Q": [...]
    }
  },
  "camera_ids": {
    "left": 1,
    "right": 2
  },
  "resolution": {
    "width": 1280,
    "height": 720
  }
}
```

---

## 🔄 Flujo de Decisión

```
┌─────────────────────────────────┐
│  Usuario inicia programa         │
└────────────┬────────────────────┘
             │
             ▼
    ┌────────────────────┐
    │ Selecciona opción   │
    │ "Calibrar cámaras"  │
    └────────┬───────────┘
             │
             ▼
    ┌────────────────────────────┐
    │ ¿Existe calibration.json?   │
    └─────┬──────────────────┬───┘
          │ NO               │ SÍ
          │                  │
          ▼                  ▼
    ┌─────────────┐    ┌──────────────────────┐
    │ CALIBRACIÓN │    │ Mostrar pantalla:     │
    │ COMPLETA    │    │ "CALIBRACIÓN ENCONTRADA" │
    │             │    │                       │
    │ Fase 1:     │    │ Opciones:             │
    │ - Izq (25)  │    │ [ENTER] Usar existente│
    │ - Der (25)  │    │ [R] Re-calibrar todo  │
    │             │    │ [S] Solo Fase 2       │
    │ Fase 2:     │    │ [ESC] Volver          │
    │ - Pares(8+) │    └─────┬────────────────┘
    │             │          │
    │ → Guarda    │          │
    │   JSON      │          ▼
    └─────────────┘    Usuario presiona tecla
                             │
                 ┌───────────┼───────────┬──────────┐
                 │           │           │          │
              ENTER          R           S        ESC
                 │           │           │          │
                 ▼           ▼           ▼          ▼
          ┌──────────┐ ┌─────────┐ ┌────────┐ ┌────────┐
          │ Continuar│ │Re-calibr│ │ Solo   │ │ Volver │
          │   con    │ │completo │ │ Fase 2 │ │   al   │
          │existente │ │Fase 1+2 │ │(estéreo│ │  menú  │
          └──────────┘ └─────────┘ └────────┘ └────────┘
```

---

## 🖥️ Pantalla "CALIBRACIÓN ENCONTRADA"

Cuando existe calibración, verás:

```
╔═══════════════════════════════════════════════════════╗
║        CALIBRACIÓN ENCONTRADA                         ║
╠═══════════════════════════════════════════════════════╣
║                                                       ║
║  Fecha: 2025-12-02 14:35:22                          ║
║  Version: 2.0                                         ║
║                                                       ║
║  Tablero: 8x8 (30.0 mm)                              ║
║                                                       ║
║  Cámara Izquierda:                                   ║
║    Error: 0.0667 px                                  ║
║    Imágenes: 25                                      ║
║                                                       ║
║  Cámara Derecha:                                     ║
║    Error: 0.0878 px                                  ║
║    Imágenes: 25                                      ║
║                                                       ║
║  Calibración Estéreo: SÍ                             ║
║    Baseline: 12.34 cm                                ║
║    Error RMS: 0.4532                                 ║
║    Pares: 10                                         ║
║                                                       ║
║  ─────────────────────────────────────────────       ║
║  OPCIONES:                                           ║
║                                                       ║
║  [ENTER] - Usar calibración existente y continuar   ║
║  [R] - RE-CALIBRAR desde cero (Fase 1 + Fase 2)     ║
║  [S] - Completar SOLO Fase 2 (calibración estéreo)  ║
║  [ESC] - Volver al menú                              ║
║                                                       ║
╚═══════════════════════════════════════════════════════╝
```

**Nota**: Si solo completaste Fase 1, la opción `[S]` estará disponible para completar Fase 2.

---

## 🔍 Validación Automática

El sistema verifica que la calibración sea válida:

```python
CalibrationConfig.calibration_exists()
```

**Verifica**:
- ✅ Archivo `calibration.json` existe
- ✅ Estructura JSON válida
- ✅ Contiene `left_camera`, `right_camera`, `board_config`
- ✅ Cada cámara tiene `camera_matrix` y `distortion_coeffs`

**Si falta algo** → Sistema asume que NO existe calibración válida.

---

## 📊 Función `get_calibration_summary()`

Extrae información resumida sin cargar toda la calibración:

```python
from calibration.calibration_config import CalibrationConfig

summary = CalibrationConfig.get_calibration_summary()
# {
#   'fecha': '2025-12-02 14:35:22',
#   'version': '2.0',
#   'tablero': '8x8',
#   'square_size': 30.0,
#   'error_left': 0.0667,
#   'error_right': 0.0878,
#   'imagenes_left': 25,
#   'imagenes_right': 25,
#   'tiene_estereo': True,
#   'baseline_cm': 12.34,
#   'error_stereo': 0.4532,
#   'pares_stereo': 10
# }
```

---

## ⚡ Opción [S] - Completar Solo Fase 2

Si ya tienes Fase 1 completa pero falta Fase 2:

1. Carga calibración de Fase 1 desde JSON
2. Recrea `CameraCalibrator` con matrices K y D cargadas
3. Crea `StereoCalibrator` con calibradores cargados
4. Ejecuta **solo** captura de pares estéreo (8-15)
5. Ejecuta `stereoCalibrate()` y `stereoRectify()`
6. **Actualiza** JSON con sección `stereo`

**Ventaja**: No necesitas recapturar 50 fotos individuales, solo 8-15 pares.

---

## 🗑️ ¿Cuándo Re-calibrar? (Opción [R])

Deberías re-calibrar si:

- ❌ Moviste las cámaras de posición
- ❌ Cambiaste la resolución de captura
- ❌ Cambiaste el enfoque de las cámaras
- ❌ Los errores en el JSON son altos (> 1.0 px)
- ❌ El sistema no detecta manos correctamente
- ❌ La profundidad 3D es imprecisa

**NO necesitas re-calibrar si**:
- ✅ Solo cambias de PC (copia `camcalibration/`)
- ✅ Solo cambias software
- ✅ Las cámaras están en la misma posición física

---

## 💡 Uso Programático

### Verificar si existe calibración:
```python
from calibration.calibration_config import CalibrationConfig

if CalibrationConfig.calibration_exists():
    print("✓ Calibración encontrada")
else:
    print("✗ No hay calibración, ejecutar proceso")
```

### Cargar calibración:
```python
from calibration import CalibrationManager
import numpy as np

data = CalibrationManager.load_calibration()

if data:
    K_left = np.array(data['left_camera']['camera_matrix'])
    D_left = np.array(data['left_camera']['distortion_coeffs'])
    
    # Usar en tu aplicación
    undistorted = cv2.undistort(frame, K_left, D_left)
```

### Obtener resumen:
```python
summary = CalibrationConfig.get_calibration_summary()

if summary:
    print(f"Fecha: {summary['fecha']}")
    print(f"Error izq: {summary['error_left']:.4f} px")
    print(f"Tiene estéreo: {summary['tiene_estereo']}")
```

---

## 🔒 Seguridad del Caché

### Persistencia:
- ✅ Se guarda en disco (`calibration.json`)
- ✅ Sobrevive a reinicios del programa
- ✅ Sobrevive a reinicios del sistema
- ✅ Puede copiarse entre computadoras (si las cámaras son las mismas)

### Invalidación:
- ❌ Si borras `calibration.json` → Sistema pide re-calibrar
- ❌ Si el JSON está corrupto → Sistema pide re-calibrar
- ❌ Si falta algún campo requerido → Sistema pide re-calibrar

### Backup:
```bash
# Hacer backup de calibración
cp camcalibration/calibration.json camcalibration/calibration_backup.json

# Restaurar backup
cp camcalibration/calibration_backup.json camcalibration/calibration.json
```

---

## 📝 Logs de Consola

### Primera vez (sin caché):
```
INICIANDO CALIBRACIÓN COMPLETA
======================================================================
FASE 1: CALIBRACIÓN INDIVIDUAL - CÁMARA IZQUIERDA
...
FASE 2: CALIBRACIÓN ESTÉREO
...
✓ Calibración completa guardada en: camcalibration/calibration.json
```

### Con caché existente (presiona ENTER):
```
✓ Calibración encontrada
✓ Usando calibración existente
[Inicia el juego directamente]
```

### Re-calibración (presiona R):
```
⚠ Iniciando RE-CALIBRACIÓN completa...
INICIANDO CALIBRACIÓN COMPLETA
...
```

### Solo Fase 2 (presiona S):
```
⚠ Completando Fase 2 (calibración estéreo)...
FASE 2: CALIBRACIÓN ESTÉREO
...
✓ Calibración estéreo completada y guardada
```

---

## 🎮 Flujo Recomendado

### Primera instalación:
1. Ejecutar programa
2. Seleccionar "Calibrar cámaras"
3. Sistema detecta que NO existe caché
4. Ejecuta calibración completa (Fase 1 + Fase 2)
5. Guarda en `calibration.json`
6. Listo para jugar

### Usos posteriores:
1. Ejecutar programa
2. Seleccionar "Calibrar cámaras"
3. Sistema detecta caché existente
4. **Presionar ENTER**
5. Listo para jugar (inmediato)

### Si moviste las cámaras:
1. Ejecutar programa
2. Seleccionar "Calibrar cámaras"
3. Sistema detecta caché existente
4. **Presionar R**
5. Re-calibra todo desde cero
6. Listo para jugar

---

## ✅ Ventajas del Sistema

1. **Ahorro de tiempo**: De 10+ minutos a <5 segundos
2. **Experiencia de usuario**: No repites trabajo innecesario
3. **Flexibilidad**: 3 opciones según necesidad
4. **Transparencia**: Ves fecha y calidad de calibración existente
5. **Robustez**: Validación automática de integridad
6. **Portabilidad**: Puedes copiar `camcalibration/` entre PCs

---

**¡Sistema de caché implementado! Ya no necesitas recalibrar cada vez.** 🎉
