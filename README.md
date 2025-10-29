## Requisitos

- **Python 3.10.11**

## Archivos necesarios

- `fluid.rar` → contiene el archivo **FluidR3_GM.sf2**  
- `fluidsynth.rar` → contiene la carpeta **bin** con las DLL necesarias  

Descomprime ambos antes de continuar.

---

## Configuración de rutas

### 1. Banco de sonido (.sf2)

1. Abrir el archivo `virtualpianokb.py`  
2. Buscar la línea:
   sfid = fs.sfload(r"C:\Users\MI PC\OneDrive\Desktop\fluid\FluidR3_GM.sf2")
Cambiar la ruta según la ubicación del archivo .sf2 en tu equipo.
Ejemplo:


sfid = fs.sfload(r"D:\Proyectos\fluid\FluidR3_GM.sf2")

### 2. Librerías FluidSynth (DLL)
Ir a la carpeta del entorno virtual:

  venv/Lib/site-packages/
Abrir el archivo fluidsynth.py

Buscar la línea:
  os.add_dll_directory(r"...")
Cambiar la ruta para que apunte a la carpeta bin descomprimida desde fluidsynth.rar.

Ejemplo:
  os.add_dll_directory(r"D:\Proyectos\fluidsynth\bin")

### Ejecución
Ejecutar el archivo principal desde la terminal:
  python virtualpianokb.py
