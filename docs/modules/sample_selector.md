# Sample Selector

Módulo: `src/sample_selector.py`

## Descripción

Selecciona muestras representativas de observaciones utilizando diferentes estrategias: por calidad, clustering, estratificado o aleatorio.

## Clase Principal

### `RepresentativeSampleSelector`

```python
from src.sample_selector import RepresentativeSampleSelector

selector = RepresentativeSampleSelector(
    method="clustering",
    random_state=42,
    logger=None
)
```

#### Parámetros del Constructor

| Parámetro | Tipo | Descripción | Valor por defecto |
|-----------|------|-------------|-------------------|
| `method` | str | Método de selección | `"clustering"` |
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
    total_candidates: int          # Total de observaciones recibidas
    total_selected: int            # Total seleccionado
    by_species: Dict[int, int]     # Cantidad seleccionada por especie (taxon_id -> n)
    selection_method: str          # Método usado
```

## Métodos

### `select_samples`

Selecciona muestras de una lista de observaciones.

```python
result = selector.select_samples(
    observations,
    n_samples_per_species=50,
    min_samples_per_species=10,
    diversity_weight=0.7,
    quality_weight=0.3
)
```

#### Parámetros

| Parámetro | Tipo | Descripción | Default |
|-----------|------|-------------|---------|
| `observations` | List[Dict] | Lista de observaciones (con `quality_score` si disponible) | — |
| `n_samples_per_species` | int | Muestras objetivo por especie | `50` |
| `min_samples_per_species` | int | Mínimo para incluir especie | `10` |
| `diversity_weight` | float | Peso de diversidad en selección (0-1) | `0.7` |
| `quality_weight` | float | Peso de calidad en selección (0-1) | `0.3` |

#### Retorno

`SampleSelectionResult` con observaciones seleccionadas y conteos por especie.

### `balance_dataset`

Balancea el número de muestras entre especies.

```python
balanced = selector.balance_dataset(
    observations,
    target_per_species,        # obligatorio (int)
    allow_undersampling=True
)
```

| Parámetro | Tipo | Descripción | Default |
|-----------|------|-------------|---------|
| `observations` | List[Dict] | Lista de observaciones | — |
| `target_per_species` | int | Número objetivo por especie (obligatorio) | — |
| `allow_undersampling` | bool | Si reducir (por calidad) las especies con más muestras | `True` |

#### Retorno

Lista de observaciones balanceada.

## Estrategias de Selección

### Por Calidad (`quality`)

Ordena por `quality_score` (escrito por la etapa 4) y selecciona los mejores:

```python
def _select_by_quality(self, observations, n_samples):
    sorted_obs = sorted(
        observations,
        key=lambda o: self._get_quality_score(o),
        reverse=True
    )
    return sorted_obs[:n_samples]

def _get_quality_score(self, obs):
    score = obs.get('quality_score', 50)
    if score is None:
        return 50.0
    try:
        return float(score)
    except (TypeError, ValueError):
        return 50.0
```

**Ventajas:**
- Garantiza imágenes de alta calidad
- Predecible y determinístico

**Desventajas:**
- Puede sesgar hacia ciertos tipos de fotos
- Menor diversidad visual

### Por Clustering (`clustering`)

Maximiza diversidad visual mediante K-Means en un espacio de características (ubicación, fecha, calidad) escalado con `StandardScaler`. De cada cluster se selecciona la observación con mejor balance diversidad-calidad:

```python
def _select_by_clustering(self, observations, n_samples, diversity_weight, quality_weight):
    if len(observations) <= n_samples:
        return observations

    features = self._extract_features(observations)  # lat, lon, día del año, quality_score
    if features is None or len(features) < n_samples:
        return self._select_by_quality(observations, n_samples)

    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)

    kmeans = KMeans(n_clusters=min(n_samples, len(observations)),
                    random_state=self.random_state, n_init=10)
    labels = kmeans.fit_predict(features_scaled)

    selected = []
    for cluster_id in range(n_clusters):
        cluster_obs = [observations[i] for i in np.where(labels == cluster_id)[0]]
        if not cluster_obs:
            continue
        selected.append(self._select_best_from_cluster(cluster_obs, quality_weight))

    # Completar hasta n_samples con los de mayor calidad restantes
    if len(selected) < n_samples:
        remaining = [o for o in observations if o not in selected]
        remaining.sort(key=lambda o: self._get_quality_score(o), reverse=True)
        selected.extend(remaining[:n_samples - len(selected)])

    return selected[:n_samples]
```

Si el clustering falla, cae automáticamente al método `quality`.

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
    n_samples_per_species=100,
    min_samples_per_species=20
)

print(f"Seleccionadas: {len(result.selected)}")
print(f"Especies incluidas: {len(result.by_species)}")

# by_species es Dict[int, int]: taxon_id -> cantidad seleccionada
for species_id, count in result.by_species.items():
    print(f"  {species_id}: {count} muestras")

# Balancear dataset (target_per_species es obligatorio)
balanced = selector.balance_dataset(result.selected, target_per_species=20)
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

result1 = selector1.select_samples(observations, n_samples_per_species=50)
result2 = selector2.select_samples(observations, n_samples_per_species=50)

assert result1.selected == result2.selected  # Siempre True
```

## Consideraciones

### Mínimo de Muestras

Las especies con menos de `min_samples_per_species` observaciones se excluyen (se loguea un `warning` y no se incluyen en `selected`):

```python
result = selector.select_samples(
    observations,
    n_samples_per_species=100,
    min_samples_per_species=20  # Especies con < 20 se excluyen
)

# Las especies excluidas no aparecen en result.by_species;
# el total se refleja en result.total_candidates vs result.total_selected.
```

### Few-Shot Learning

Para tareas de few-shot learning:

```python
# Support set pequeño
selector = RepresentativeSampleSelector(method="clustering")
result = selector.select_samples(
    observations, n_samples_per_species=5, min_samples_per_species=5
)

# Maximiza diversidad en pocas muestras
```

## Dependencias

- `numpy`: Operaciones numéricas
- `sklearn.cluster.KMeans`: Para método clustering
