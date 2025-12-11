# Deduplicator

Módulo: `src/deduplicator.py`

## Descripción

Implementa deduplicación inteligente de observaciones mediante clustering espacio-temporal. Identifica observaciones que probablemente corresponden al mismo individuo fotografiado múltiples veces.

## Clases

### `ObservationDeduplicator`

```python
from src.deduplicator import ObservationDeduplicator

deduplicator = ObservationDeduplicator(
    spatial_threshold_m=100,
    temporal_threshold_days=1,
    min_samples=1,
    logger=None
)
```

#### Parámetros del Constructor

| Parámetro | Tipo | Descripción | Valor por defecto |
|-----------|------|-------------|-------------------|
| `spatial_threshold_m` | float | Distancia máxima en metros | `100` |
| `temporal_threshold_days` | int | Días máximos entre observaciones | `1` |
| `min_samples` | int | Mínimo de muestras para cluster | `1` |
| `logger` | Logger | Logger opcional | `None` |

### `UniqueIndividual`

Dataclass que representa un individuo único identificado.

```python
@dataclass
class UniqueIndividual:
    individual_id: str           # ID único del individuo
    species: str                 # Nombre de la especie
    species_id: int              # ID del taxón
    observations: List[Dict]     # Todas las observaciones del individuo
    best_observation: Dict       # Mejor observación seleccionada
    n_duplicates: int            # Número de duplicados encontrados
    date_range: Tuple[str, str]  # Rango de fechas (min, max)
    location_centroid: Tuple[float, float]  # Centroide geográfico
```

### `DeduplicationResult`

Dataclass con el resultado del proceso de deduplicación.

```python
@dataclass
class DeduplicationResult:
    unique_individuals: List[UniqueIndividual]  # Individuos únicos
    total_original: int          # Total de observaciones originales
    total_unique: int            # Total de individuos únicos
    duplicates_removed: int      # Duplicados eliminados
    dedup_rate: float            # Tasa de deduplicación (0-1)
    by_species: Dict             # Estadísticas por especie
```

## Métodos

### `deduplicate`

Procesa una lista de observaciones y agrupa duplicados.

```python
result = deduplicator.deduplicate(observations)
```

#### Parámetros

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `observations` | List[Dict] | Lista de observaciones de iNaturalist |

#### Retorno

`DeduplicationResult` con individuos únicos y estadísticas.

### `get_dedup_summary`

Genera un resumen legible del resultado.

```python
summary = deduplicator.get_dedup_summary(result)
print(summary)
```

## Algoritmo

### 1. Agrupación por Especie

Las observaciones se procesan separadamente por `taxon.id`:

```python
by_species = defaultdict(list)
for obs in observations:
    species_id = obs.get('taxon', {}).get('id')
    by_species[species_id].append(obs)
```

### 2. Extracción de Coordenadas

El módulo extrae coordenadas de múltiples formatos de iNaturalist:

```python
def _extract_coordinates(observation):
    # 1. Campos directos
    if observation.get('latitude') and observation.get('longitude'):
        return (latitude, longitude)
    
    # 2. GeoJSON
    if observation.get('geojson'):
        coords = observation['geojson']['coordinates']
        return (coords[1], coords[0])  # [lon, lat] -> (lat, lon)
    
    # 3. String location
    if observation.get('location'):
        parts = observation['location'].split(',')
        return (float(parts[0]), float(parts[1]))
```

### 3. Clustering DBSCAN

Se crea un espacio 3D normalizado:

```python
features = []
for obs in observations:
    lat, lon = extract_coordinates(obs)
    day_of_year = date_to_day_of_year(obs['observed_on'])
    features.append([lat, lon, day_of_year])

# Normalización
features[:, 0] *= 111000  # lat -> metros
features[:, 1] *= 111000 * cos(mean_lat)  # lon -> metros
features[:, 2] *= spatial_threshold / temporal_threshold  # días -> escala espacial

# DBSCAN
clustering = DBSCAN(eps=threshold, min_samples=1).fit(features)
```

### 4. Selección del Mejor

De cada cluster, se selecciona la mejor observación:

| Criterio | Peso | Cálculo |
|----------|------|---------|
| Resolución | 40% | Área de la imagen (width × height) |
| Calidad visual | 30% | Score de calidad si disponible |
| Engagement | 20% | likes + comentarios |
| Recencia | 10% | Fecha más reciente |

## Ejemplo Completo

```python
from src.deduplicator import ObservationDeduplicator
import json

# Cargar observaciones
with open('observations.json') as f:
    observations = json.load(f)

# Crear deduplicador
deduplicator = ObservationDeduplicator(
    spatial_threshold_m=100,
    temporal_threshold_days=1
)

# Ejecutar deduplicación
result = deduplicator.deduplicate(observations)

# Mostrar resumen
print(deduplicator.get_dedup_summary(result))

# Obtener observaciones únicas
unique_observations = [
    ind.best_observation 
    for ind in result.unique_individuals
]

print(f"Original: {result.total_original}")
print(f"Únicos: {result.total_unique}")
print(f"Tasa de dedup: {result.dedup_rate:.1%}")
```

## Consideraciones

### Observaciones sin Coordenadas

Las observaciones sin coordenadas válidas se omiten del proceso de deduplicación. El módulo registra un warning:

```
WARNING: No valid coordinates for species X, skipping
```

### Ajuste de Parámetros

| Especie | Espacial | Temporal | Notas |
|---------|----------|----------|-------|
| Mamíferos sedentarios | 50-100m | 1-3 días | Territorios pequeños |
| Aves | 100-200m | 1 día | Mayor movilidad |
| Reptiles | 20-50m | 1-7 días | Muy sedentarios |

### Rendimiento

El algoritmo DBSCAN tiene complejidad O(n²) en el peor caso. Para datasets muy grandes (>10,000 observaciones por especie), considerar:

- Procesar por lotes geográficos
- Usar índices espaciales (R-tree)

## Dependencias

- `numpy`: Operaciones numéricas
- `sklearn.cluster.DBSCAN`: Algoritmo de clustering
- [`geo_utils.py`](utils/geo_utils.md): Cálculos geográficos
