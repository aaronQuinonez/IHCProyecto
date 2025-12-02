# 🎹 Guía Rápida: Modo de Aprendizaje de Teoría Musical

## 🚀 Cómo iniciar el Modo de Aprendizaje

### Desde la Interfaz Principal

1. **Ejecuta el programa:**
   ```bat
   python c:\CodingWindows\IHC_Proyecto_Fork\IHCProyecto\src\main.py
   ```

2. **Verás la pantalla de bienvenida** con estas opciones:
   ```
   ╔════════════════════════════════════╗
   ║     PIANO VIRTUAL                  ║
   ║                                    ║
   ║  CONTROLES:                        ║
   ║  [G] Juego de ritmo               ║
   ║  [F] Modo libre                   ║
   ║  [L] Aprender teoria ⭐           ║
   ║  [D] Dashboard                    ║
   ║  [Q] Salir                        ║
   ╚════════════════════════════════════╝
   ```

3. **Presiona la tecla `L`** para entrar al modo teoría

4. **Verás el menú de lecciones** con navegación visual:
   ```
   ╔════════════════════════════════════════════════╗
   ║  MODO TEORIA - Selecciona una leccion         ║
   ║━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━║
   ║                                                ║
   ║  ► 1. Intervalos Musicales      [Básico]     ║
   ║    2. Escalas Musicales          [Básico]     ║
   ║    3. Acordes Basicos            [Intermedio] ║
   ║                                                ║
   ║  Descripcion:                                  ║
   ║  Aprende a identificar y tocar intervalos     ║
   ║  (distancia entre dos notas)                   ║
   ║                                                ║
   ║  W/S o Flechas: Navegar                       ║
   ║  1-9 o ENTER: Seleccionar                     ║
   ║  Q: Salir                                     ║
   ╚════════════════════════════════════════════════╝
   ```

5. **Navega entre lecciones usando:**
   - **Teclas W/S** (más confiable en Windows)
   - **Flechas ↑/↓** (pueden variar según el sistema)
   - **O presiona directamente 1, 2 o 3** para selección rápida

6. **Presiona `ENTER`** para iniciar la lección seleccionada

7. **Dentro de la lección:**
   - Sigue las instrucciones en pantalla
   - Usa los controles específicos de cada lección
   - Presiona `ESC` para volver al menú de lecciones
   - Presiona `Q` para salir del modo teoría

## 📋 Flujo completo de navegación

```
Pantalla Principal
       │
       ├─ [L] ──→ Menú de Lecciones ←──────┐
       │              │                      │
       │              ├─ [↑↓] Navegar       │
       │              │                      │
       │              ├─ [ENTER] ──→ Lección Activa
       │              │                      │
       │              │                      │
       │              └─ [Q] Salir          │
       │                                     │
       ├─ [F] Modo Libre                   │
       ├─ [G] Juego de Ritmo              [ESC]
       └─ [Q] Salir Programa               │
                                            │
                                  Volver al Menú ─┘
```

## 🎯 Atajos de teclado principales

| Tecla | Desde donde | Acción |
|-------|-------------|--------|
| `L` | Pantalla principal / Modo libre | Activar modo teoría |
| `W` / `S` | Menú de lecciones | Navegar (alternativa confiable) |
| `↑` / `↓` | Menú de lecciones | Navegar con flechas |
| `1` `2` `3` | Menú de lecciones | Selección directa de lección |
| `ENTER` | Menú de lecciones | Seleccionar lección resaltada |
| `ESC` | Dentro de lección | Volver al menú de lecciones |
| `Q` | Menú de lecciones | Salir del modo teoría |
| `Q` | Dentro de lección | Salir del modo teoría |
| `F` | Cualquier modo | Volver al modo libre |

## 💡 Tips

- **El menú siempre está disponible**: Puedes cambiar entre modos en cualquier momento presionando `L`, `F`, o `G`
- **Navegación intuitiva**: El menú muestra visualmente qué lección está seleccionada
- **Instrucciones en pantalla**: Cada lección muestra sus controles específicos
- **Progreso visible**: Barras de progreso y feedback visual en todas las lecciones

## 🎓 Lecciones disponibles

### 1. 🎵 Intervalos Musicales (Básico)
- **Qué aprendes**: Distancia entre dos notas
- **Controles principales**: `ESPACIO` para escuchar, `N/P` para navegar

### 2. 🎼 Escalas Musicales (Básico)
- **Qué aprendes**: Patrones de escalas mayores, menores y pentatónicas
- **Controles principales**: `ESPACIO` para tocar nota, `A/D` o flechas para navegar, `R` para auto-reproducir

### 3. 🎹 Acordes Básicos (Intermedio)
- **Qué aprendes**: Construcción de acordes mayores y menores
- **Controles principales**: `ESPACIO` arpegiado, `C` completo, `I` para construcción

## 🆘 Solución de problemas

**¿No veo el menú de teoría?**
- Asegúrate de presionar `L` (no `A`)
- Verifica que estés en modo libre o en la pantalla principal

**¿Cómo salgo de una lección?**
- Presiona `ESC` para volver al menú
- Presiona `Q` para salir completamente del modo teoría

**¿Las lecciones no cargan?**
- Verifica que la carpeta `src/theory/lessons/` exista
- Revisa la consola para mensajes de error

---

**¡Disfruta aprendiendo teoría musical de forma interactiva!** 🎶
