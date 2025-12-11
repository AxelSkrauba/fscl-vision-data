# Quality Assessor

Módulo: `src/quality_assessor.py`

## Descripción

Evalúa la calidad visual de imágenes calculando métricas objetivas como nitidez, exposición, contraste, composición y detección de blur.

## Clase Principal

### `ImageQualityAssessor`

```python
from src.quality_assessor import ImageQualityAssessor

assessor = ImageQualityAssessor(
    weights=None,
    logger=None
)
```

#### Parámetros del Constructor

| Parámetro | Tipo | Descripción | Valor por defecto |
|-----------|------|-------------|-------------------|
| `weights` | Dict | Pesos personalizados para métricas | `None` (usa defaults) |
| `logger` | Logger | Logger opcional | `None` |

#### Pesos por Defecto

```python
DEFAULT_WEIGHTS = {
    'sharpness': 0.30,
    'exposure': 0.20,
    'contrast': 0.20,
    'composition': 0.15,
    'blur': 0.15
}
```

## Métodos

### `assess_quality`

Evalúa la calidad de una imagen.

```python
metrics = assessor.assess_quality(image_path)
```

#### Parámetros

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `image_path` | str/Path | Ruta a la imagen |

#### Retorno

Diccionario con métricas de calidad:

```python
{
    'sharpness': 75.3,      # 0-100
    'exposure': 82.1,       # 0-100
    'contrast': 68.5,       # 0-100
    'composition': 55.0,    # 0-100
    'blur': 12.3,           # 0-100 (menor es mejor)
    'overall_score': 71.2   # 0-100
}
```

### `assess_batch`

Evalúa múltiples imágenes.

```python
results = assessor.assess_batch(
    image_paths,
    n_workers=4
)
```

#### Parámetros

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `image_paths` | List[str] | Lista de rutas a imágenes |
| `n_workers` | int | Workers paralelos | 

#### Retorno

Diccionario `{path: metrics}` para cada imagen.

### `filter_by_quality`

Filtra observaciones por umbral de calidad.

```python
passed, rejected = assessor.filter_by_quality(
    observations,
    image_dir,
    min_score=40,
    max_blur=30
)
```

### `get_statistics`

Calcula estadísticas de un conjunto de métricas.

```python
stats = assessor.get_statistics(all_metrics)
```

## Métricas Detalladas

### Nitidez (Sharpness)

Utiliza la varianza del operador Laplaciano para detectar bordes:

```python
def _calculate_sharpness(self, gray_image):
    laplacian = cv2.Laplacian(gray_image, cv2.CV_64F)
    variance = laplacian.var()
    # Normalizar a 0-100
    return min(100, variance / 10)
```

**Interpretación:**
- **> 70**: Imagen muy nítida
- **40-70**: Nitidez aceptable
- **< 40**: Imagen borrosa

### Exposición

Analiza el histograma de luminosidad:

```python
def _calculate_exposure(self, gray_image):
    hist = cv2.calcHist([gray_image], [0], None, [256], [0, 256])
    hist = hist.flatten() / hist.sum()
    
    # Penalizar extremos
    dark_ratio = hist[:50].sum()
    bright_ratio = hist[200:].sum()
    
    # Score óptimo cuando la distribución es balanceada
    score = 100 - (dark_ratio + bright_ratio) * 100
    return max(0, score)
```

**Interpretación:**
- **> 70**: Buena exposición
- **40-70**: Exposición aceptable
- **< 40**: Sub/sobreexposición

### Contraste

Desviación estándar de la luminosidad:

```python
def _calculate_contrast(self, gray_image):
    std = np.std(gray_image)
    # Normalizar (std típico 40-80)
    return min(100, std * 1.5)
```

**Interpretación:**
- **> 60**: Buen contraste
- **30-60**: Contraste moderado
- **< 30**: Imagen plana

### Composición

Evalúa la posición del sujeto respecto a la regla de tercios:

```python
def _calculate_composition(self, image):
    # Detectar región de interés (área más contrastada)
    roi_center = detect_roi(image)
    
    # Puntos de tercios
    thirds_points = [
        (w/3, h/3), (2*w/3, h/3),
        (w/3, 2*h/3), (2*w/3, 2*h/3)
    ]
    
    # Distancia mínima a un punto de tercios
    min_distance = min(distance(roi_center, p) for p in thirds_points)
    
    # Menor distancia = mejor composición
    return 100 - min(100, min_distance / diagonal * 200)
```

### Blur

Detección de desenfoque mediante análisis de frecuencias:

```python
def _calculate_blur(self, gray_image):
    # FFT para analizar frecuencias
    fft = np.fft.fft2(gray_image)
    fft_shift = np.fft.fftshift(fft)
    magnitude = np.abs(fft_shift)
    
    # Ratio de altas frecuencias
    high_freq_ratio = high_freq_energy / total_energy
    
    # Menor ratio = más blur
    blur_score = 100 - high_freq_ratio * 100
    return blur_score
```

**Interpretación:**
- **< 20**: Imagen nítida
- **20-40**: Blur leve
- **> 40**: Blur significativo

## Score Compuesto

El score final combina todas las métricas:

```python
def _calculate_overall_score(self, metrics):
    score = (
        metrics['sharpness'] * self.weights['sharpness'] +
        metrics['exposure'] * self.weights['exposure'] +
        metrics['contrast'] * self.weights['contrast'] +
        metrics['composition'] * self.weights['composition'] +
        (100 - metrics['blur']) * self.weights['blur']
    )
    return score
```

## Ejemplo Completo

```python
from src.quality_assessor import ImageQualityAssessor
from pathlib import Path

# Crear assessor con pesos personalizados
assessor = ImageQualityAssessor(
    weights={
        'sharpness': 0.40,  # Priorizar nitidez
        'exposure': 0.20,
        'contrast': 0.20,
        'composition': 0.10,
        'blur': 0.10
    }
)

# Evaluar una imagen
metrics = assessor.assess_quality("image.jpg")
print(f"Score: {metrics['overall_score']:.1f}")
print(f"Nitidez: {metrics['sharpness']:.1f}")
print(f"Blur: {metrics['blur']:.1f}")

# Evaluar batch
image_dir = Path("data/raw/species")
image_paths = list(image_dir.glob("*.jpg"))
all_metrics = assessor.assess_batch(image_paths, n_workers=4)

# Estadísticas
stats = assessor.get_statistics(list(all_metrics.values()))
print(f"Media: {stats['mean']:.1f}")
print(f"Std: {stats['std']:.1f}")
```

## Consideraciones

### Imágenes de Fauna

Las fotos de fauna silvestre tienen características particulares:
- Fondos complejos (vegetación)
- Sujetos en movimiento
- Condiciones de luz variables
- Distancias focales largas

Por eso, umbrales moderados (35-45) suelen ser apropiados.

### Rendimiento

La evaluación de calidad es CPU-intensiva. Para datasets grandes:
- Usar `assess_batch` con múltiples workers
- Considerar reducir resolución para análisis
- Cachear resultados

## Dependencias

- `opencv-python`: Procesamiento de imágenes
- `numpy`: Operaciones numéricas
- [`image_utils.py`](utils/image_utils.md): Carga de imágenes
