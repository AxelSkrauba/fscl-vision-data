# Etapa 3: Deduplicación

Script: `scripts/03_deduplicate.py`

## Descripción

Esta etapa identifica y agrupa observaciones que probablemente corresponden al mismo individuo, evitando que el dataset contenga múltiples fotos del mismo animal tomadas en momentos cercanos.

## Uso

```bash
python scripts/03_deduplicate.py --config config/mi_config.yaml
```

### Argumentos

| Argumento | Descripción | Valor por defecto |
|-----------|-------------|-------------------|
| `--config` | Ruta al archivo de configuración YAML | `config/paraense_fauna.yaml` |
| `--spatial-threshold` | Override del umbral espacial (metros) | Valor en config |
| `--temporal-threshold` | Override del umbral temporal (días) | Valor en config |

## Funcionamiento

### Algoritmo

1. **Agrupación por especie**: Las observaciones se procesan separadamente por taxón
2. **Extracción de coordenadas**: Se obtienen latitud/longitud de cada observación
3. **Normalización espacio-temporal**: Se crea un espacio 3D (lat, lon, día_del_año)
4. **Clustering DBSCAN**: Agrupa observaciones cercanas en espacio y tiempo
5. **Selección del mejor**: De cada cluster, se elige la mejor observación

### Criterios de "Mejor Observación"

Cuando hay múltiples observaciones del mismo individuo, se selecciona según:

| Criterio | Peso | Descripción |
|----------|------|-------------|
| Resolución | 40% | Mayor tamaño de imagen |
| Calidad visual | 30% | Score de calidad si está disponible |
| Engagement | 20% | Likes + comentarios |
| Recencia | 10% | Observaciones más recientes |

## Parámetros de Configuración

```yaml
deduplication:
  spatial_threshold_m: 100    # Metros de distancia máxima
  temporal_threshold_days: 1  # Días entre observaciones
  min_samples: 1              # Mínimo para formar cluster
```

### Interpretación de Parámetros

- **spatial_threshold_m = 100**: Observaciones a menos de 100m se consideran del mismo lugar
- **temporal_threshold_days = 1**: Observaciones el mismo día o días consecutivos se agrupan
- **min_samples = 1**: Incluso observaciones aisladas forman su propio "cluster"

### Ajuste de Parámetros

| Escenario | Espacial | Temporal | Resultado |
|-----------|----------|----------|-----------|
| Animales sedentarios | 50-100m | 1-3 días | Deduplicación agresiva |
| Animales móviles | 200-500m | 1 día | Deduplicación moderada |
| Aves migratorias | 100m | 1 día | Solo duplicados obvios |

## Salida

### Archivo principal

`data/{dataset}/cache/observations_deduplicated.json`

Contiene solo las "mejores" observaciones de cada individuo único identificado.

### Estadísticas

`data/{dataset}/cache/deduplication_stats.json`

```json
{
  "total_original": 500,
  "total_unique": 380,
  "duplicates_removed": 120,
  "dedup_rate": 0.24,
  "by_species": {
    "12738": {
      "name": "Turdus rufiventris",
      "original": 250,
      "unique": 180,
      "removed": 70,
      "dedup_rate": 0.28
    }
  },
  "parameters": {
    "spatial_threshold_m": 100,
    "temporal_threshold_days": 1
  }
}
```

## Ejemplo Visual

```
Observaciones originales:
  A: (-25.680, -54.450) @ 2024-01-15  ─┐
  B: (-25.681, -54.451) @ 2024-01-15  ─┼─► Cluster 1 → Selecciona A (mejor calidad)
  C: (-25.680, -54.449) @ 2024-01-16  ─┘
  
  D: (-26.100, -54.800) @ 2024-01-20  ─── Cluster 2 → Mantiene D
  
  E: (-25.500, -54.200) @ 2024-02-01  ─┐
  F: (-25.501, -54.201) @ 2024-02-01  ─┴─► Cluster 3 → Selecciona E

Resultado: 3 individuos únicos de 6 observaciones (50% dedup)
```

## Manejo de Coordenadas

El deduplicador extrae coordenadas de múltiples formatos de iNaturalist:

1. **Campos directos**: `latitude`, `longitude`
2. **GeoJSON**: `geojson.coordinates` [lon, lat]
3. **String location**: `location` "lat,lon"

Las observaciones sin coordenadas válidas se omiten del proceso.

## Consideraciones

### Falsos Positivos

Dos individuos diferentes en el mismo lugar pueden agruparse incorrectamente. Esto es aceptable porque:
- Es mejor tener menos duplicados que más
- La diversidad se mantiene en la selección posterior

### Falsos Negativos

El mismo individuo fotografiado en lugares distantes no se agrupa. Esto es intencional:
- No hay forma confiable de identificar individuos sin marcas
- Diferentes ubicaciones aportan diversidad al dataset

### Especies Coloniales

Para especies que viven en colonias (ej: pingüinos, murciélagos), considerar:
- Reducir `spatial_threshold_m` a 10-20m
- O desactivar deduplicación para esas especies

## Módulos Utilizados

- [`deduplicator.py`](../modules/deduplicator.md) - Lógica de clustering
- [`geo_utils.py`](../modules/utils/geo_utils.md) - Cálculos geográficos

## Siguiente Etapa

Una vez deduplicadas las observaciones, proceder a [Etapa 4: Evaluación de Calidad](04_assess_quality.md).
