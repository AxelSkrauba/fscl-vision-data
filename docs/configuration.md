# Guía de Configuración

Esta guía describe todos los parámetros disponibles en los archivos de configuración YAML del pipeline.

## Estructura General

Los archivos de configuración se encuentran en el directorio `config/` y siguen una estructura jerárquica:

```yaml
geography:
  # Configuración geográfica
fauna:
  # Especies a obtener
quality:
  # Umbrales de calidad de imagen
deduplication:
  # Parámetros de deduplicación
sampling:
  # Configuración de selección de muestras
api:
  # Configuración del cliente API
data_dir:
  # Directorio base de datos
logging:
  # Configuración de logs
```

## Secciones de Configuración

### geography

Define la región geográfica de donde se obtendrán las observaciones.

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `region_name` | string | Nombre descriptivo de la región |
| `place_id` | integer | ID del lugar en iNaturalist (recomendado) |
| `bounds.north` | float | Latitud norte del bounding box |
| `bounds.south` | float | Latitud sur del bounding box |
| `bounds.east` | float | Longitud este del bounding box |
| `bounds.west` | float | Longitud oeste del bounding box |

**Ejemplo:**

```yaml
geography:
  region_name: "Selva Paranaense"
  place_id: 10422  # Misiones, Argentina
  bounds:
    north: -25.0
    south: -28.0
    east: -53.5
    west: -56.0
```

**Nota**: Para obtener el `place_id` correcto, utilizar la API de iNaturalist:
```
https://api.inaturalist.org/v1/places/autocomplete?q=NombreDelLugar
```

### fauna.taxa

Lista de especies a obtener del repositorio de iNaturalist.

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `name` | string | Nombre científico de la especie |
| `taxon_id` | integer | ID del taxón en iNaturalist |
| `common_names` | list | Nombres comunes (opcional) |
| `max_observations` | integer | Máximo de observaciones a obtener |

**Ejemplo:**

```yaml
fauna:
  taxa:
    - name: "Turdus rufiventris"
      taxon_id: 12738
      common_names: ["Zorzal colorado", "Rufous-bellied Thrush"]
      max_observations: 500

    - name: "Ramphastos toco"
      taxon_id: 18793
      common_names: ["Tucán grande", "Toco Toucan"]
      max_observations: 500
```

**Nota**: Para verificar el `taxon_id` correcto:
```
https://api.inaturalist.org/v1/taxa?q=NombreCientifico&rank=species
```

### quality

Umbrales para la evaluación de calidad de imágenes.

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `minimum_width` | integer | Ancho mínimo en píxeles |
| `minimum_height` | integer | Alto mínimo en píxeles |
| `quality_score_threshold` | float | Score mínimo de calidad (0-100) |
| `max_blur_detected` | float | Máximo nivel de blur permitido |

**Ejemplo:**

```yaml
quality:
  minimum_width: 400
  minimum_height: 400
  quality_score_threshold: 40
  max_blur_detected: 30
```

**Métricas de calidad evaluadas:**

- **Nitidez (sharpness)**: Varianza del Laplaciano
- **Exposición**: Análisis del histograma de luminosidad
- **Contraste**: Desviación estándar de la luminosidad
- **Composición**: Posición del sujeto respecto a la regla de tercios
- **Blur**: Detección de desenfoque mediante análisis de frecuencias

### deduplication

Parámetros para el clustering espacio-temporal que identifica observaciones del mismo individuo.

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `spatial_threshold_m` | float | Distancia máxima en metros |
| `temporal_threshold_days` | integer | Días máximos entre observaciones |
| `min_samples` | integer | Mínimo de muestras para formar cluster |

**Ejemplo:**

```yaml
deduplication:
  spatial_threshold_m: 100
  temporal_threshold_days: 1
  min_samples: 1
```

**Funcionamiento:**

El algoritmo DBSCAN agrupa observaciones que:
1. Están dentro del umbral espacial (misma ubicación aproximada)
2. Ocurrieron dentro del umbral temporal (mismo día o días cercanos)
3. Pertenecen a la misma especie

De cada cluster, se selecciona la "mejor" observación según:
- Resolución de la imagen
- Calidad visual (si está disponible)
- Engagement (likes, comentarios)
- Recencia

### sampling

Configuración para la selección de muestras representativas.

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `method` | string | Método de selección: `quality`, `clustering`, `stratified`, `random` |
| `n_samples_per_species` | integer | Número de muestras por especie |
| `min_samples_per_species` | integer | Mínimo requerido para incluir especie |
| `balance_dataset` | boolean | Balancear número de muestras entre especies |

**Ejemplo:**

```yaml
sampling:
  method: "quality"
  n_samples_per_species: 100
  min_samples_per_species: 20
  balance_dataset: true
```

**Métodos de selección:**

| Método | Descripción |
|--------|-------------|
| `quality` | Selecciona las imágenes con mayor score de calidad |
| `clustering` | Maximiza diversidad visual mediante K-Means en espacio de características |
| `stratified` | Estratifica por ubicación geográfica y temporal |
| `random` | Selección aleatoria (reproducible con seed) |

### api

Configuración del cliente de la API de iNaturalist.

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `quality_grade` | string | Grado de calidad: `research`, `needs_id`, `casual` |
| `rate_limit_calls` | integer | Llamadas máximas por período |
| `rate_limit_period` | integer | Período en segundos |
| `max_retries` | integer | Reintentos en caso de error |
| `timeout` | integer | Timeout de conexión en segundos |

**Ejemplo:**

```yaml
api:
  quality_grade: "research"
  rate_limit_calls: 60
  rate_limit_period: 60
  max_retries: 3
  timeout: 30
```

### download

Configuración para la descarga de imágenes.

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `max_workers` | integer | Número de workers paralelos |
| `image_size` | string | Tamaño de imagen: `original`, `large`, `medium`, `small` |
| `save_metadata` | boolean | Guardar metadatos JSON por imagen |

**Ejemplo:**

```yaml
download:
  max_workers: 4
  image_size: "large"
  save_metadata: true
```

### Otras opciones

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `data_dir` | string | Directorio base para datos |
| `logging.level` | string | Nivel de log: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `random_seed` | integer | Semilla para reproducibilidad |

**Ejemplo:**

```yaml
data_dir: "./data"
logging:
  level: "INFO"
random_seed: 42
```

## Archivos de Configuración Incluidos

### default.yaml

Configuración base con valores por defecto. Otros archivos pueden heredar de este.

### paraense_fauna.yaml

Configuración completa para la fauna de la Selva Paranaense (Misiones, Argentina). Incluye especies emblemáticas de la región.

### test_config.yaml

Configuración mínima para pruebas rápidas del pipeline. Utiliza pocas especies y observaciones para validar el funcionamiento.

## Creación de Configuración Personalizada

1. Copiar un archivo existente como base:
   ```bash
   cp config/paraense_fauna.yaml config/mi_dataset.yaml
   ```

2. Modificar los parámetros según el caso de uso

3. Verificar los IDs en la API de iNaturalist:
   - `place_id`: `/v1/places/autocomplete?q=...`
   - `taxon_id`: `/v1/taxa?q=...&rank=species`

4. Ejecutar una prueba con pocas observaciones primero:
   ```yaml
   fauna:
     taxa:
       - name: "Mi especie"
         taxon_id: 12345
         max_observations: 10  # Empezar con pocos
   ```

5. Una vez validado, incrementar `max_observations` según necesidad.
