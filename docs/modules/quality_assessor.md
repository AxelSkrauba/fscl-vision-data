# Quality Assessor

Módulo: `src/quality_assessor.py`

## Descripción

Evalúa la calidad visual de imágenes calculando métricas objetivas: nitidez (sharpness), exposición, contraste, composición (entropía de Shannon) y detección de blur. Cada métrica retorna un score normalizado a 0-100, y se combinan en un score compuesto ponderado.

## Dataclass

### `QualityScores`

```python
from src.quality_assessor import QualityScores

scores = QualityScores(
    sharpness=75.3,
    exposure=82.1,
    contrast=68.5,
    composition=55.0,
    blur=12.3,
    overall=71.2
)

scores.to_dict()
# {'sharpness': 75.3, 'exposure': 82.1, 'contrast': 68.5,
#  'composition': 55.0, 'blur': 12.3, 'overall': 71.2}
```

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `sharpness` | float | Nitidez (0-100) |
| `exposure` | float | Exposición (0-100) |
| `contrast` | float | Contraste (0-100) |
| `composition` | float | Complejidad visual por entropía (0-100) |
| `blur` | float | Score anti-blur: **alto = nítido** (0-100) |
| `overall` | float | Score compuesto ponderado (0-100) |

> **Nota sobre `blur`:** a diferencia de lo que su nombre sugiere, el score de blur es **alto cuando la imagen NO está borrosa**. Es decir, funciona como un "anti-blur / nitidez". Esto se refleja en la fórmula del score compuesto, donde `blur` se suma directamente (sin invertir).

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
| `weights` | Dict[str, float] | Pesos personalizados para cada métrica | `None` (usa defaults) |
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
scores = assessor.assess_quality(image_path)
```

#### Parámetros

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `image_path` | str/Path | Ruta a la imagen |

#### Retorno

Instancia de `QualityScores` (o `None` si hay error). Si OpenCV no está disponible, retorna un `QualityScores` con todos los scores en 50.

### `assess_batch`

Evalúa múltiples imágenes de forma **secuencial**.

```python
results = assessor.assess_batch(
    image_paths,
    progress_callback=None
)
```

#### Parámetros

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `image_paths` | List[Path] | Lista de rutas a imágenes |
| `progress_callback` | callable | Callback `(current, total)` invocado cada 100 imágenes |

#### Retorno

Diccionario `{str(path): QualityScores}` para cada imagen evaluada con éxito.

> **Nota:** No hay paralelización; la evaluación es secuencial. El callback de progreso se llama cada 100 imágenes y se loguea cada 500.

### `filter_by_quality`

Filtra imágenes por umbrales de calidad a partir de los scores calculados.

```python
passed = assessor.filter_by_quality(
    scores,
    min_overall=40.0,
    min_sharpness=None,
    max_blur=None
)
```

#### Parámetros

| Parámetro | Tipo | Descripción | Default |
|-----------|------|-------------|---------|
| `scores` | Dict[str, QualityScores] | Scores por imagen (de `assess_batch`) | — |
| `min_overall` | float | Score overall mínimo | `40.0` |
| `min_sharpness` | float \| None | Sharpness mínimo (opcional) | `None` |
| `max_blur` | float \| None | Blurriness máxima permitida (opcional) | `None` |

#### Retorno

Lista de paths que pasan los filtros.

> **Semántica de `max_blur`:** se rechaza si `score.blur < (100 - max_blur)`, es decir, si el "blurriness" `(100 - blur)` supera el máximo. Coherente con que `blur` alto = nítido.

### `get_statistics`

Calcula estadísticas de los scores de calidad.

```python
stats = assessor.get_statistics(scores)
```

#### Parámetros

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `scores` | Dict[str, QualityScores] | Scores por imagen |

#### Retorno

Diccionario por métrica (`sharpness`, `exposure`, `contrast`, `composition`, `blur`, `overall`), cada una con `mean`, `std`, `min`, `max`, `median`. Devuelve `{}` si `scores` está vacío.

```python
{
    'overall': {'mean': 65.4, 'std': 15.2, 'min': 25.1, 'max': 92.3, 'median': 66.0},
    'sharpness': {...},
    ...
}
```

## Métricas Detalladas

### Nitidez (Sharpness)

Varianza del operador Laplaciano, normalizada al rango 0-100:

```python
def _assess_sharpness(self, gray):
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    variance = laplacian.var()
    return self._normalize_score(variance, min_val=100, max_val=2000)
```

Mayor varianza = imagen más nítida. La normalización mapea el rango `[100, 2000]` a `[0, 100]`.

### Exposición

Analiza el histograma de luminosidad y penaliza desvíos respecto a una distribución ideal:

```python
def _assess_exposure(self, gray):
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    hist_norm = hist.flatten() / hist.sum()

    dark_ratio = np.sum(hist_norm[:64])      # px < 64
    bright_ratio = np.sum(hist_norm[192:])   # px > 192
    mid_ratio = np.sum(hist_norm[64:192])

    # Ideales: ~15% oscuro, ~10% brillante
    dark_penalty = abs(dark_ratio - 0.15) * 100
    bright_penalty = abs(bright_ratio - 0.10) * 100

    score = 100 - (dark_penalty + bright_penalty)
    if mid_ratio < 0.5:
        score -= 20

    return max(0, min(100, score))
```

### Contraste

Desviación estándar de la luminosidad, normalizada:

```python
def _assess_contrast(self, gray):
    std = gray.std()
    return self._normalize_score(std, min_val=20, max_val=80)
```

El rango `[20, 80]` se mapea a `[0, 100]`.

### Composición (Entropía de Shannon)

> **Decisión de diseño:** la "composición" se estima mediante **entropía de Shannon** de la imagen en escala de grises, no mediante regla de tercios ni detección de ROI. El framework apunta a tareas de few-shot learning sobre cámaras trampa, donde el encuadre fotográfico es irrelevante (el animal aparece en cualquier parte de la toma). Lo que importa es la diversidad y riqueza visual de los ejemplares, no su posición en el frame. A mayor entropía, la imagen se interpreta como más compleja/interesante visualmente.

```python
def _assess_composition(self, gray):
    entropy = self._calculate_entropy(gray)
    return self._normalize_score(entropy, min_val=4.0, max_val=7.5)

@staticmethod
def _calculate_entropy(image):
    hist = cv2.calcHist([image], [0], None, [256], [0, 256])
    hist = hist.flatten()
    hist = hist / hist.sum()
    hist = hist[hist > 0]
    return -np.sum(hist * np.log2(hist))
```

La entropía (en bits) se normaliza del rango `[4.0, 7.5]` a `[0, 100]`.

### Blur (Anti-blur)

Detección de desenfoque mediante **varianza del Laplaciano** (no FFT):

```python
def _assess_blur(self, gray):
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    variance = laplacian.var()
    blur_threshold = 100

    if variance < blur_threshold:
        return max(0, (variance / blur_threshold) * 50)        # 0-50: borrosa
    else:
        return min(100, 50 + (variance - blur_threshold) / 40)  # 50-100: nítida
```

**Interpretación (alto = nítido):**
- **> 50**: Imagen nítida
- **< 50**: Imagen con blur significativo

> El score es **alto cuando la imagen NO está borrosa**. Por eso entra directamente (sin invertir) en el score compuesto.

## Score Compuesto

El score final combina todas las métricas con sus pesos. Nótese que `blur` se suma directamente (alto = bueno), a diferencia de un esquema donde se invertiría:

```python
overall = (
    sharpness * self.weights['sharpness'] +
    exposure * self.weights['exposure'] +
    contrast * self.weights['contrast'] +
    composition * self.weights['composition'] +
    blur * self.weights['blur']
)
```

## Normalización

`_normalize_score(value, min_val, max_val)` mapea linealmente `value` del rango `[min_val, max_val]` a `[0, 100]`, acotando al rango. Si `max_val <= min_val`, retorna 50.

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
scores = assessor.assess_quality("image.jpg")
print(f"Score: {scores.overall:.1f}")
print(f"Nitidez: {scores.sharpness:.1f}")
print(f"Blur (alto=nítido): {scores.blur:.1f}")

# Evaluar batch
image_dir = Path("data/raw/species")
image_paths = list(image_dir.glob("*.jpg"))
all_scores = assessor.assess_batch(image_paths)

# Estadísticas
stats = assessor.get_statistics(all_scores)
print(f"Media overall: {stats['overall']['mean']:.1f}")
print(f"Std overall: {stats['overall']['std']:.1f}")

# Filtrar por calidad
passed = assessor.filter_by_quality(all_scores, min_overall=40, max_blur=30)
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

La evaluación de calidad es CPU-intensiva y **secuencial**. Para datasets grandes:
- Considerar reducir resolución antes del análisis
- Cachear resultados (el pipeline ya cachea `observations_quality.json`)

## Dependencias

- `opencv-python`: Procesamiento de imágenes
- `numpy`: Operaciones numéricas
- [`image_utils.py`](utils/image_utils.md): Carga de imágenes
