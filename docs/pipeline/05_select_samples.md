# Etapa 5: Selección de Muestras

Script: `scripts/05_select_samples.py`

## Descripción

Esta etapa selecciona un subconjunto representativo de las observaciones que pasaron el filtro de calidad, aplicando diferentes estrategias de muestreo para conformar el dataset final.

## Uso

```bash
python scripts/05_select_samples.py --config config/mi_config.yaml
```

### Argumentos

| Argumento | Descripción | Valor por defecto |
|-----------|-------------|-------------------|
| `--config` | Ruta al archivo de configuración YAML | `config/paraense_fauna.yaml` |
| `--method` | Override del método de selección | Valor en config |
| `--n-samples` | Override de muestras por especie | Valor en config |

## Métodos de Selección

### 1. Por Calidad (`quality`)

Selecciona las N imágenes con mayor score de calidad por especie.

```yaml
sampling:
  method: "quality"
  n_samples_per_species: 100
```

**Ventajas:**
- Garantiza imágenes de alta calidad
- Simple y predecible

**Desventajas:**
- Puede sesgar hacia ciertos tipos de fotos
- Menor diversidad visual

### 2. Por Clustering (`clustering`)

Maximiza la diversidad visual mediante K-Means en espacio de características.

```yaml
sampling:
  method: "clustering"
  n_samples_per_species: 100
```

**Funcionamiento:**
1. Extrae características visuales de cada imagen
2. Aplica K-Means con K = n_samples
3. Selecciona la imagen más cercana a cada centroide

**Ventajas:**
- Maximiza diversidad visual
- Cubre diferentes poses, fondos, iluminación

**Desventajas:**
- Más costoso computacionalmente
- Puede incluir imágenes de menor calidad

### 3. Estratificado (`stratified`)

Estratifica por ubicación geográfica y temporal.

```yaml
sampling:
  method: "stratified"
  n_samples_per_species: 100
```

**Funcionamiento:**
1. Divide observaciones en estratos geográficos (cuadrantes)
2. Subdivide por período temporal (meses/estaciones)
3. Muestrea proporcionalmente de cada estrato

**Ventajas:**
- Representación geográfica balanceada
- Captura variación estacional

**Desventajas:**
- Puede tener estratos vacíos
- Requiere buena distribución de datos

### 4. Aleatorio (`random`)

Selección aleatoria con semilla fija para reproducibilidad.

```yaml
sampling:
  method: "random"
  n_samples_per_species: 100
  random_seed: 42
```

**Ventajas:**
- Simple y rápido
- Reproducible con semilla fija

**Desventajas:**
- No optimiza ningún criterio
- Resultados variables

## Parámetros de Configuración

```yaml
sampling:
  method: "quality"              # Método de selección
  n_samples_per_species: 100     # Muestras objetivo por especie
  min_samples_per_species: 20    # Mínimo para incluir especie
  balance_dataset: true          # Igualar muestras entre especies
  random_seed: 42                # Semilla para reproducibilidad
```

### Balanceo de Dataset

Cuando `balance_dataset: true`:
- Se calcula el mínimo de muestras disponibles entre especies
- Todas las especies se limitan a ese número
- Útil para evitar sesgo hacia especies más fotografiadas

## Salida

### Archivo principal

`data/{dataset}/cache/observations_selected.json`

Observaciones seleccionadas para el dataset final.

### Estadísticas

`data/{dataset}/cache/selection_stats.json`

```json
{
  "method": "quality",
  "total_candidates": 320,
  "total_selected": 200,
  "species_included": 2,
  "species_excluded": 1,
  "by_species": {
    "Turdus rufiventris": {
      "candidates": 155,
      "selected": 100,
      "mean_quality": 72.5
    },
    "Ramphastos toco": {
      "candidates": 140,
      "selected": 100,
      "mean_quality": 68.3
    }
  },
  "excluded_species": {
    "Nasua nasua": {
      "reason": "insufficient_samples",
      "available": 15,
      "required": 20
    }
  }
}
```

## Filtro de Mínimo de Muestras

Las especies con menos de `min_samples_per_species` observaciones se excluyen del dataset final. Esto evita:

- Clases con muy pocos ejemplos
- Sesgo en entrenamiento de modelos
- Evaluaciones poco confiables

```yaml
sampling:
  min_samples_per_species: 20  # Excluir especies con < 20 muestras
```

## Consideraciones

### Tamaño del Dataset

| Objetivo | Muestras/especie | Total (10 especies) |
|----------|------------------|---------------------|
| Prototipo | 20-50 | 200-500 |
| Desarrollo | 50-100 | 500-1000 |
| Producción | 100-500 | 1000-5000 |

### Few-Shot Learning

Para tareas de few-shot learning, considera:
- **Support set**: 5-20 imágenes por clase
- **Query set**: Resto de imágenes para evaluación
- Usar `balance_dataset: true` para clases equilibradas

### Reproducibilidad

El selector utiliza `np.random.RandomState` aislado para garantizar reproducibilidad:

```python
selector = RepresentativeSampleSelector(
    method="random",
    random_state=42  # Misma semilla = mismos resultados
)
```

## Módulos Utilizados

- [`sample_selector.py`](../modules/sample_selector.md) - Lógica de selección

## Siguiente Etapa

Una vez seleccionadas las muestras, proceder a [Etapa 6: Organización del Dataset](06_organize_dataset.md).
