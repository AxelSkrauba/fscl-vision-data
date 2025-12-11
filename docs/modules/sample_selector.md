# Sample Selector

Módulo: `src/sample_selector.py`

## Descripción

Selecciona muestras representativas de observaciones utilizando diferentes estrategias: por calidad, clustering, estratificado o aleatorio.

## Clase Principal

### `RepresentativeSampleSelector`

```python
from src.sample_selector import RepresentativeSampleSelector

selector = RepresentativeSampleSelector(
    method="quality",
    random_state=42,
    logger=None
)
```

#### Parámetros del Constructor

| Parámetro | Tipo | Descripción | Valor por defecto |
|-----------|------|-------------|-------------------|
| `method` | str | Método de selección | `"quality"` |
| `random_state` | int | Semilla para reproducibilidad | `42` |
| `logger` | Logger | Logger opcional | `None` |

#### Métodos Disponibles

| Método | Descripción |
|--------|-------------|
| `"quality"` | Selecciona por mayor score de calidad |
| `"clustering"` | Maximiza diversidad visual con K-Means |
| `"stratified"` | Estratifica por ubicación y tiempo |
| `"random"` | Selección aleatoria reproducible |

## Dataclasses

### `SampleSelectionResult`

```python
@dataclass
class SampleSelectionResult:
    selected: List[Dict]           # Observaciones seleccionadas
    excluded: List[Dict]           # Observaciones excluidas
    by_species: Dict[int, List]    # Selección por especie
    stats: Dict                    # Estadísticas del proceso
```

## Métodos

### `select_samples`

Selecciona muestras de una lista de observaciones.

```python
result = selector.select_samples(
    observations,
    n_samples=100,
    min_samples=20
)
```

#### Parámetros

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `observations` | List[Dict] | Lista de observaciones |
| `n_samples` | int | Muestras objetivo por especie |
| `min_samples` | int | Mínimo para incluir especie |

#### Retorno

`SampleSelectionResult` con observaciones seleccionadas y estadísticas.

### `balance_dataset`

Balancea el número de muestras entre especies.

```python
balanced = selector.balance_dataset(
    observations,
    target_per_species=None  # None = mínimo disponible
)
```

## Estrategias de Selección

### Por Calidad (`quality`)

Ordena por `quality_metrics.overall_score` y selecciona los mejores:

```python
def _select_by_quality(self, observations, n_samples):
    sorted_obs = sorted(
        observations,
        key=lambda x: x.get('quality_metrics', {}).get('overall_score', 0),
        reverse=True
    )
    return sorted_obs[:n_samples]
```

**Ventajas:**
- Garantiza imágenes de alta calidad
- Predecible y determinístico

**Desventajas:**
- Puede sesgar hacia ciertos tipos de fotos
- Menor diversidad visual

### Por Clustering (`clustering`)

Maximiza diversidad visual mediante K-Means:

```python
def _select_by_clustering(self, observations, n_samples):
    # Extraer características (ubicación, fecha, calidad)
    features = extract_features(observations)
    
    # K-Means con K = n_samples
    kmeans = KMeans(n_clusters=n_samples, random_state=self.random_state)
    kmeans.fit(features)
    
    # Seleccionar observación más cercana a cada centroide
    selected = []
    for i in range(n_samples):
        cluster_obs = [obs for obs, label in zip(observations, kmeans.labels_) if label == i]
        best = min(cluster_obs, key=lambda x: distance_to_centroid(x, kmeans.cluster_centers_[i]))
        selected.append(best)
    
    return selected
```

**Ventajas:**
- Maximiza diversidad
- Cubre diferentes poses, fondos, iluminación

**Desventajas:**
- Más costoso computacionalmente
- Puede incluir imágenes de menor calidad

### Estratificado (`stratified`)

Estratifica por ubicación geográfica y temporal:

```python
def _select_stratified(self, observations, n_samples):
    # Dividir en cuadrantes geográficos
    geo_strata = divide_by_location(observations, n_strata=4)
    
    # Subdividir por período temporal
    for stratum in geo_strata:
        temporal_strata = divide_by_month(stratum)
    
    # Muestrear proporcionalmente de cada estrato
    samples_per_stratum = n_samples // total_strata
    selected = []
    for stratum in all_strata:
        selected.extend(sample(stratum, samples_per_stratum))
    
    return selected
```

**Ventajas:**
- Representación geográfica balanceada
- Captura variación estacional

**Desventajas:**
- Puede tener estratos vacíos
- Requiere buena distribución de datos

### Aleatorio (`random`)

Selección aleatoria con semilla fija:

```python
def _select_random(self, observations, n_samples):
    indices = self._rng.choice(
        len(observations),
        size=min(n_samples, len(observations)),
        replace=False
    )
    return [observations[i] for i in indices]
```

**Nota**: Usa `np.random.RandomState` aislado para garantizar reproducibilidad.

## Ejemplo Completo

```python
from src.sample_selector import RepresentativeSampleSelector
import json

# Cargar observaciones con métricas de calidad
with open('observations_quality.json') as f:
    observations = json.load(f)

# Crear selector
selector = RepresentativeSampleSelector(
    method="quality",
    random_state=42
)

# Seleccionar muestras
result = selector.select_samples(
    observations,
    n_samples=100,
    min_samples=20
)

print(f"Seleccionadas: {len(result.selected)}")
print(f"Especies incluidas: {len(result.by_species)}")

# Ver estadísticas por especie
for species_id, obs_list in result.by_species.items():
    species_name = obs_list[0].get('taxon', {}).get('name', 'Unknown')
    print(f"  {species_name}: {len(obs_list)} muestras")

# Balancear dataset
balanced = selector.balance_dataset(result.selected)
print(f"Balanceado: {len(balanced)} observaciones")
```

## Reproducibilidad

El selector garantiza reproducibilidad mediante:

1. **RandomState aislado**: Cada instancia tiene su propio generador de números aleatorios
2. **Semilla configurable**: El parámetro `random_state` controla la semilla

```python
# Misma semilla = mismos resultados
selector1 = RepresentativeSampleSelector(method="random", random_state=42)
selector2 = RepresentativeSampleSelector(method="random", random_state=42)

result1 = selector1.select_samples(observations, n_samples=50)
result2 = selector2.select_samples(observations, n_samples=50)

assert result1.selected == result2.selected  # Siempre True
```

## Consideraciones

### Mínimo de Muestras

Las especies con menos de `min_samples` observaciones se excluyen:

```python
result = selector.select_samples(
    observations,
    n_samples=100,
    min_samples=20  # Especies con < 20 se excluyen
)

# Ver especies excluidas
for species_id, reason in result.stats['excluded_species'].items():
    print(f"Excluida: {species_id} - {reason}")
```

### Few-Shot Learning

Para tareas de few-shot learning:

```python
# Support set pequeño
selector = RepresentativeSampleSelector(method="clustering")
result = selector.select_samples(observations, n_samples=5, min_samples=5)

# Maximiza diversidad en pocas muestras
```

## Dependencias

- `numpy`: Operaciones numéricas
- `sklearn.cluster.KMeans`: Para método clustering
