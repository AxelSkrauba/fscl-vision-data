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
| `--min-quality` | Override del umbral de calidad (score overall mínimo 0-100) | Valor en config (`quality.quality_score_threshold`) |

## Funcionamiento

Para cada imagen, se calculan las siguientes métricas:

### Métricas de Calidad

| Métrica | Rango | Descripción |
|---------|-------|-------------|
| **Nitidez (Sharpness)** | 0-100 | Varianza del Laplaciano normalizada |
| **Exposición** | 0-100 | Análisis del histograma de luminosidad |
| **Contraste** | 0-100 | Desviación estándar de la luminosidad normalizada |
| **Composición** | 0-100 | Entropía de Shannon (complejidad visual) |
| **Blur** | 0-100 | Score anti-blur: **alto = nítido** (varianza del Laplaciano) |

> **Composición:** se estima mediante entropía de Shannon. El framework apunta a few-shot sobre cámaras trampa, donde el encuadre es irrelevante. Ver [`quality_assessor.md`](../modules/quality_assessor.md).

### Score Compuesto

El score final se calcula como promedio ponderado. Nótese que `blur` entra **directamente** (alto = nítido = bueno):

```
score = (sharpness * 0.30) +
        (exposure * 0.20) +
        (contrast * 0.20) +
        (composition * 0.15) +
        (blur * 0.15)
```

## Parámetros de Configuración

```yaml
quality:
  minimum_width: 400           # Ancho mínimo en píxeles (filtrado)
  minimum_height: 400          # Alto mínimo en píxeles (filtrado)
  quality_score_threshold: 40  # Score overall mínimo (0-100)
  max_blur_detected: 30        # Blurriness máxima permitida (0-100, menor = más estricto)

  # Pesos personalizados (opcional). Si se omite, se usan los defaults del código.
  weights:
    sharpness: 0.30
    exposure: 0.20
    contrast: 0.20
    composition: 0.15
    blur: 0.15
```

### Filtros aplicados

1. **Dimensiones mínimas:** las imágenes con `width < minimum_width` o `height < minimum_height` se descartan antes de evaluar calidad (no se evalúan).
2. **Blur:** si `max_blur_detected` está definido, se rechazan las imágenes cuyo "blurriness" `(100 - blur_score)` supere ese valor. Es decir, se exige `blur_score >= (100 - max_blur_detected)`.
3. **Score overall:** se rechazan las imágenes con `quality_score < quality_score_threshold` (o `--min-quality` si se pasa).

## Salida

### Archivo principal

`data/{dataset}/cache/observations_quality.json`

Observaciones que pasaron el filtro de calidad, con métricas añadidas como claves planas:

```json
[
  {
    "id": 123456789,
    "taxon": {...},
    "quality_score": 71.2,
    "quality_details": {
      "sharpness": 75.3,
      "exposure": 82.1,
      "contrast": 68.5,
      "composition": 55.0,
      "blur": 12.3,
      "overall": 71.2
    }
  }
]
```

> `quality_score` es el score overall; `quality_details` es el dict completo producido por `QualityScores.to_dict()`.

### Estadísticas

`data/{dataset}/cache/quality_stats.json`

Estadísticas por métrica (no incluye conteos de pasan/no-pasan):

```json
{
  "sharpness":  {"mean": 60.1, "std": 18.2, "min": 5.0,  "max": 100.0, "median": 61.0},
  "exposure":   {"mean": 70.5, "std": 12.3, "min": 20.0, "max": 95.0,  "median": 72.0},
  "contrast":   {"mean": 55.0, "std": 14.1, "min": 10.0, "max": 90.0,  "median": 55.0},
  "composition":{"mean": 50.2, "std": 16.8, "min": 0.0,   "max": 100.0, "median": 50.0},
  "blur":       {"mean": 45.3, "std": 20.0, "min": 0.0,   "max": 100.0, "median": 47.0},
  "overall":    {"mean": 65.4, "std": 15.2, "min": 25.1,  "max": 92.3,  "median": 66.0}
}
```

## Detalles de las Métricas

### Nitidez (Sharpness)

Varianza del operador Laplaciano, normalizada al rango 0-100 (umbrales 100-2000):

```python
laplacian = cv2.Laplacian(gray, cv2.CV_64F)
variance = laplacian.var()
sharpness = normalize(variance, min_val=100, max_val=2000)
```

- **Alto**: Bordes bien definidos, imagen enfocada
- **Bajo**: Imagen borrosa o desenfocada

### Exposición

Analiza el histograma de luminosidad y penaliza desvíos respecto a una distribución ideal (~15% oscuro, ~10% brillante). Resta 20 si los tonos medios (`mid_ratio`) son menos del 50%.

- **Alto**: Buena distribución de tonos
- **Bajo**: Subexposición o sobreexposición

### Contraste

Desviación estándar de la luminosidad, normalizada (rango 20-80 → 0-100):

- **Alto**: Buen rango dinámico
- **Bajo**: Imagen plana o lavada

### Composición (Entropía de Shannon)

Entropía de Shannon del histograma en escala de grises, normalizada (rango 4.0-7.5 bits → 0-100):

```python
entropy = -sum(p * log2(p) for p in hist if p > 0)
composition = normalize(entropy, min_val=4.0, max_val=7.5)
```

- **Alto**: Imagen visualmente compleja/rica
- **Bajo**: Imagen uniforme/poco variada

### Blur (Anti-blur)

Varianza del Laplaciano con umbral 100. **Score alto = nítido**:

```python
if variance < 100:
    blur_score = (variance / 100) * 50        # 0-50: borrosa
else:
    blur_score = 50 + (variance - 100) / 40   # 50-100: nítida
```

- **Alto (> 50)**: Imagen nítida
- **Bajo (< 50)**: Imagen borrosa

## Consideraciones

### Umbrales Recomendados

| Caso de uso | Score mínimo | max_blur_detected |
|-------------|--------------|-------------------|
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
- [`image_utils.py`](../modules/utils/image_utils.md) - Carga y dimensiones de imágenes

## Siguiente Etapa

Una vez evaluada la calidad, proceder a [Etapa 5: Selección de Muestras](05_select_samples.md).
