# mc-preview

Una CLI *standalone* para generar previews 3D locales, versionadas y comparables de texturas de bloques de Minecraft.

Esta herramienta está pensada para ser infraestructura: simple, predecible y automatizable, siendo el compañero perfecto para pipelines de Resource Packs (y de IA como Claude Code) donde se requiere revisión visual rápida sin orquestación pesada.

## Características

- **Sin dependencias nativas pesadas**: Renderizado isométrico por software utilizando `Pillow`. No requiere Three.js, OpenGL, ni Blender.
- **Determinista**: Genera exactamente 2 vistas clave (`upper`, `lower`) con misma iluminación y FOV, asegurando que las versiones sean 100% comparables.
- **Mapeo explícito de caras**: Requiere proveer explícitamente texturas separadas para `--top`, `--bottom` y `--sides` a fin de evitar mapeos repetitivos.
- **Versionado automático**: Cada vez que se renderiza, se crea una nueva versión en una carpeta `vXXXX` sin sobreescribir la historia, junto con una carpeta `current/` que contiene una copia de la última versión activa.
- **Comparación visual**: Genera un collage side-by-side entre dos versiones para facilitar la evaluación de QA.
- **Auditable**: Genera metadatos JSON completos (dimensiones, hashes, motor, timestamp) junto con la textura original en cada versión.

## Instalación

Requiere **Python 3** y `Pillow`.

1. Clona el repositorio
2. Ejecuta:
```bash
pip install -e .
```

## Configuración

Ejecuta el comando `init` para crear un archivo `preview.config.json` con valores por defecto.

```bash
preview init
```

Por defecto, esto configurará un `workspace/` relativo al archivo de configuración.

## Uso

### Renderizar texturas
Genera una nueva versión a partir de las texturas provistas:
```bash
preview render --block stone --top ./ruta/top.png --bottom ./ruta/bottom.png --sides ./ruta/sides.png
```
*Salida: Crea la versión `v0001` (o la siguiente disponible) con 2 renders (upper/lower), copia las 3 texturas de entrada, y actualiza `current/`.*

### Estado
Muestra un resumen rápido de las versiones y la versión actual:
```bash
preview status --block stone
```

### Comparar versiones
Genera una imagen side-by-side comparando dos versiones existentes.
```bash
preview compare --block stone --from v0001 --to v0002
```

### Limpiar
Limpia archivos temporales y comparaciones, **sin** borrar tu historial de versiones ni `current/`.
```bash
preview clean --block stone
```

### Abrir
Abre el directorio del workspace del bloque en el explorador de archivos de tu sistema operativo.
```bash
preview open --block stone
```

## Estructura de Directorios

```text
workspace/
  stone/
    current/
      top.png
      bottom.png
      sides.png
      metadata.json
      preview/
        upper.png
        lower.png
    v0001/
      ...
    v0002/
      ...
    comparisons/
      v0001_vs_v0002.png
```

## Arquitectura

- `preview/cli.py`: Frontend de CLI con argparse.
- `preview/config.py`: Gestión del archivo de configuración json y resolución de rutas relativas.
- `preview/workspace.py`: Lógica del sistema de archivos, manejo de la versión actual y metadatos con soporte multiface.
- `preview/render.py`: Motor isométrico propio que aplica textura a 3 caras visibles (distinguiendo entre top/bottom/sides) de un cubo sin aceleración de hardware.
- `preview/compare.py`: Lógica para generar collages de imágenes de las 2 vistas de evaluación.
