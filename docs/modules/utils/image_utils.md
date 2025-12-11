# Image Utils

Módulo: `src/utils/image_utils.py`

## Descripción

Proporciona utilidades para procesamiento y validación de imágenes, incluyendo carga, redimensionamiento y verificación de integridad.

## Clase Principal

### `ImageUtils`

```python
from src.utils.image_utils import ImageUtils
```

#### Métodos Estáticos

##### `load_image`

Carga una imagen desde disco.

```python
image = ImageUtils.load_image(
    path="image.jpg",
    mode="RGB"
)
```

**Parámetros:**

| Parámetro | Tipo | Descripción | Valor por defecto |
|-----------|------|-------------|-------------------|
| `path` | str/Path | Ruta a la imagen | Requerido |
| `mode` | str | Modo de color (RGB, L, RGBA) | `"RGB"` |

**Retorno:** Objeto PIL.Image o None si falla.

##### `load_image_cv2`

Carga una imagen usando OpenCV.

```python
image = ImageUtils.load_image_cv2(
    path="image.jpg",
    grayscale=False
)
```

**Retorno:** Array numpy (BGR o grayscale) o None si falla.

##### `validate_image`

Verifica que un archivo sea una imagen válida.

```python
is_valid = ImageUtils.validate_image(path="image.jpg")
```

**Verificaciones:**
- El archivo existe
- PIL puede abrirlo
- La imagen no está corrupta (verify)

##### `get_image_info`

Obtiene información de una imagen.

```python
info = ImageUtils.get_image_info(path="image.jpg")
```

**Retorno:**

```python
{
    'width': int,
    'height': int,
    'format': str,      # JPEG, PNG, etc.
    'mode': str,        # RGB, L, RGBA
    'size_bytes': int
}
```

##### `resize_image`

Redimensiona una imagen manteniendo la proporción.

```python
resized = ImageUtils.resize_image(
    image,
    max_size=1024,
    resample=Image.LANCZOS
)
```

**Parámetros:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `image` | PIL.Image | Imagen a redimensionar |
| `max_size` | int | Tamaño máximo del lado mayor |
| `resample` | int | Método de resampling |

##### `save_image`

Guarda una imagen a disco.

```python
ImageUtils.save_image(
    image,
    path="output.jpg",
    quality=85
)
```

##### `convert_to_grayscale`

Convierte una imagen a escala de grises.

```python
gray = ImageUtils.convert_to_grayscale(image)
```

## Ejemplo Completo

```python
from src.utils.image_utils import ImageUtils
from pathlib import Path

# Validar imagen
image_path = Path("data/raw/species/123456.jpg")
if not ImageUtils.validate_image(image_path):
    print("Imagen inválida o corrupta")
    exit()

# Obtener información
info = ImageUtils.get_image_info(image_path)
print(f"Dimensiones: {info['width']}x{info['height']}")
print(f"Formato: {info['format']}")
print(f"Tamaño: {info['size_bytes'] / 1024:.1f} KB")

# Cargar imagen
image = ImageUtils.load_image(image_path)

# Redimensionar si es muy grande
if info['width'] > 1024 or info['height'] > 1024:
    image = ImageUtils.resize_image(image, max_size=1024)
    print(f"Redimensionada a: {image.size}")

# Guardar
ImageUtils.save_image(image, "output.jpg", quality=90)

# Cargar para OpenCV (análisis de calidad)
cv_image = ImageUtils.load_image_cv2(image_path, grayscale=True)
if cv_image is not None:
    print(f"Shape: {cv_image.shape}")
```

## Formatos Soportados

| Formato | Extensiones | Notas |
|---------|-------------|-------|
| JPEG | .jpg, .jpeg | Más común para fotos |
| PNG | .png | Soporta transparencia |
| GIF | .gif | Animaciones |
| BMP | .bmp | Sin compresión |
| TIFF | .tif, .tiff | Alta calidad |
| WebP | .webp | Moderno, buena compresión |

## Manejo de Errores

```python
from src.utils.image_utils import ImageUtils

try:
    image = ImageUtils.load_image("image.jpg")
    if image is None:
        print("No se pudo cargar la imagen")
except Exception as e:
    print(f"Error: {e}")
```

## Consideraciones

### Memoria

Las imágenes grandes pueden consumir mucha memoria:
- Imagen 4000x3000 RGB: ~36 MB en memoria
- Considerar redimensionar antes de procesar

### Formatos de Color

| Modo | Descripción | Uso |
|------|-------------|-----|
| `RGB` | Color 24-bit | Procesamiento general |
| `L` | Escala de grises 8-bit | Análisis de calidad |
| `RGBA` | Color con alpha | Imágenes con transparencia |

### OpenCV vs PIL

- **PIL**: Mejor para carga/guardado, manipulación básica
- **OpenCV**: Mejor para análisis, procesamiento avanzado

```python
# PIL para cargar
pil_image = ImageUtils.load_image(path)

# OpenCV para análisis
cv_image = ImageUtils.load_image_cv2(path, grayscale=True)
laplacian_var = cv2.Laplacian(cv_image, cv2.CV_64F).var()
```

## Dependencias

- `Pillow`: Carga y manipulación de imágenes
- `opencv-python`: Procesamiento avanzado
- `numpy`: Operaciones con arrays
