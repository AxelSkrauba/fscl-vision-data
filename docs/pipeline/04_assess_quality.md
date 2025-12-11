# Etapa 4: Evaluación de Calidad

Script: `scripts/04_assess_quality.py`

## Descripción

Esta etapa evalúa la calidad visual de cada imagen descargada, calculando métricas objetivas que permiten filtrar imágenes de baja calidad antes de incluirlas en el dataset final.

## Uso

```bash
python scripts/04_assess_quality.py --config config/mi_config.yaml
```

### Argumentos

| Argumento | Descripción | Valor por defecto |
|-----------|-------------|-------------------|
| `--config` | Ruta al archivo de configuración YAML | `config/paraense_fauna.yaml` |
| `--threshold` | Override del umbral de calidad | Valor en config |

## Funcionamiento

Para cada imagen, se calculan las siguientes métricas:

### Métricas de Calidad

| Métrica | Rango | Descripción |
|---------|-------|-------------|
| **Nitidez (Sharpness)** | 0-100 | Varianza del Laplaciano normalizada |
| **Exposición** | 0-100 | Análisis del histograma de luminosidad |
| **Contraste** | 0-100 | Desviación estándar de la luminosidad |
| **Composición** | 0-100 | Proximidad del sujeto a puntos de interés |
| **Blur** | 0-100 | Detección de desenfoque (menor es mejor) |

### Score Compuesto

El score final se calcula como promedio ponderado:

```
score = (sharpness * 0.30) + 
        (exposure * 0.20) + 
        (contrast * 0.20) + 
        (composition * 0.15) + 
        ((100 - blur) * 0.15)
```

## Parámetros de Configuración

```yaml
quality:
  minimum_width: 400           # Ancho mínimo en píxeles
  minimum_height: 400          # Alto mínimo en píxeles
  quality_score_threshold: 40  # Score mínimo (0-100)
  max_blur_detected: 30        # Máximo blur permitido
  
  # Pesos personalizados (opcional)
  weights:
    sharpness: 0.30
    exposure: 0.20
    contrast: 0.20
    composition: 0.15
    blur: 0.15
```

## Salida

### Archivo principal

`data/{dataset}/cache/observations_quality.json`

Observaciones que pasaron el filtro de calidad, con métricas añadidas:

```json
[
  {
    "id": 123456789,
    "taxon": {...},
    "quality_metrics": {
      "sharpness": 75.3,
      "exposure": 82.1,
      "contrast": 68.5,
      "composition": 55.0,
      "blur": 12.3,
      "overall_score": 71.2
    }
  }
]
```

### Estadísticas

`data/{dataset}/cache/quality_stats.json`

```json
{
  "total_assessed": 380,
  "passed": 320,
  "rejected": 60,
  "pass_rate": 0.84,
  "metrics": {
    "mean_score": 65.4,
    "std_score": 15.2,
    "min_score": 25.1,
    "max_score": 92.3
  },
  "by_species": {
    "Turdus rufiventris": {
      "assessed": 180,
      "passed": 155,
      "mean_score": 68.2
    }
  },
  "rejection_reasons": {
    "low_score": 45,
    "high_blur": 10,
    "small_dimensions": 5
  }
}
```

## Detalles de las Métricas

### Nitidez (Sharpness)

Utiliza la varianza del operador Laplaciano:

```python
laplacian = cv2.Laplacian(gray_image, cv2.CV_64F)
sharpness = laplacian.var()
```

- **Alto**: Bordes bien definidos, imagen enfocada
- **Bajo**: Imagen borrosa o desenfocada

### Exposición

Analiza el histograma de luminosidad:

```python
hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
# Penaliza extremos (muy oscuro o muy claro)
```

- **Alto**: Buena distribución de tonos
- **Bajo**: Subexposición o sobreexposición

### Contraste

Desviación estándar de la luminosidad:

```python
contrast = np.std(gray_image)
```

- **Alto**: Buen rango dinámico
- **Bajo**: Imagen plana o lavada

### Composición

Evalúa la posición del sujeto respecto a la regla de tercios:

```python
# Detecta región de interés
# Calcula distancia a puntos de tercios
```

- **Alto**: Sujeto bien posicionado
- **Bajo**: Sujeto centrado o en bordes

### Blur

Detección de desenfoque mediante análisis de frecuencias:

```python
fft = np.fft.fft2(gray_image)
# Analiza componentes de alta frecuencia
```

- **Alto**: Imagen muy borrosa
- **Bajo**: Imagen nítida

## Consideraciones

### Umbrales Recomendados

| Caso de uso | Score mínimo | Blur máximo |
|-------------|--------------|-------------|
| Dataset de alta calidad | 50-60 | 20 |
| Dataset balanceado | 35-45 | 35 |
| Maximizar cantidad | 25-30 | 50 |

### Imágenes de Fauna

Las fotos de fauna silvestre suelen tener:
- Fondos complejos (vegetación)
- Sujetos en movimiento
- Condiciones de luz variables

Por eso, umbrales moderados (35-45) suelen ser apropiados.

### Validación Visual

Se recomienda revisar manualmente una muestra de:
- Imágenes rechazadas cerca del umbral
- Imágenes aceptadas con scores bajos

Esto permite ajustar los umbrales según el caso específico.

## Módulos Utilizados

- [`quality_assessor.py`](../modules/quality_assessor.md) - Evaluación de calidad
- [`image_utils.py`](../modules/utils/image_utils.md) - Carga de imágenes

## Siguiente Etapa

Una vez evaluada la calidad, proceder a [Etapa 5: Selección de Muestras](05_select_samples.md).
