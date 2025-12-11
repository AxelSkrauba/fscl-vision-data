# Etapas del Pipeline

El pipeline de FSCL-Vision Data se ejecuta en 6 etapas secuenciales. Cada etapa procesa la salida de la anterior.

## Resumen de Etapas

| Etapa | Script | Entrada | Salida |
|-------|--------|---------|--------|
| 1 | `01_fetch_observations.py` | Configuración YAML | `observations.json` |
| 2 | `02_download_images.py` | `observations.json` | Imágenes + metadatos |
| 3 | `03_deduplicate.py` | `observations.json` | `observations_deduplicated.json` |
| 4 | `04_assess_quality.py` | Imágenes descargadas | `observations_quality.json` |
| 5 | `05_select_samples.py` | `observations_quality.json` | `observations_selected.json` |
| 6 | `06_organize_dataset.py` | `observations_selected.json` | Dataset final |

## Documentación por Etapa

1. **[Obtención de Observaciones](01_fetch_observations.md)** - Consulta a iNaturalist API
2. **[Descarga de Imágenes](02_download_images.md)** - Descarga paralela con metadatos
3. **[Deduplicación](03_deduplicate.md)** - Clustering espacio-temporal
4. **[Evaluación de Calidad](04_assess_quality.md)** - Métricas de calidad de imagen
5. **[Selección de Muestras](05_select_samples.md)** - Muestreo representativo
6. **[Organización del Dataset](06_organize_dataset.md)** - Estructura final y manifests

## Ejecución

### Pipeline Completo

```bash
python scripts/helpers/run_full_pipeline.py --config config/mi_config.yaml
```

### Por Etapas

```bash
python scripts/01_fetch_observations.py --config config/mi_config.yaml
python scripts/02_download_images.py --config config/mi_config.yaml
python scripts/03_deduplicate.py --config config/mi_config.yaml
python scripts/04_assess_quality.py --config config/mi_config.yaml
python scripts/05_select_samples.py --config config/mi_config.yaml
python scripts/06_organize_dataset.py --config config/mi_config.yaml
```

### Saltar Etapas

El script `run_full_pipeline.py` permite saltar etapas:

```bash
# Saltar fetch (usar observaciones existentes)
python scripts/helpers/run_full_pipeline.py --config config/mi_config.yaml --skip-fetch

# Saltar descarga (usar imágenes existentes)
python scripts/helpers/run_full_pipeline.py --config config/mi_config.yaml --skip-download
```

## Flujo de Datos

```
config.yaml
    │
    ▼
┌───────────────────┐
│ 01_fetch          │──► observations.json
└───────────────────┘
    │
    ▼
┌───────────────────┐
│ 02_download       │──► raw/{species}/*.jpg
└───────────────────┘
    │
    ▼
┌───────────────────┐
│ 03_deduplicate    │──► observations_deduplicated.json
└───────────────────┘
    │
    ▼
┌───────────────────┐
│ 04_assess_quality │──► observations_quality.json
└───────────────────┘
    │
    ▼
┌───────────────────┐
│ 05_select_samples │──► observations_selected.json
└───────────────────┘
    │
    ▼
┌───────────────────┐
│ 06_organize       │──► final_datasets/{name}/
└───────────────────┘
```

## Archivos Intermedios

Todos los archivos intermedios se guardan en `data/{dataset}/cache/`:

| Archivo | Etapa | Descripción |
|---------|-------|-------------|
| `observations.json` | 1 | Observaciones crudas de iNaturalist |
| `fetch_stats.json` | 1 | Estadísticas de obtención |
| `download_stats.json` | 2 | Estadísticas de descarga |
| `observations_deduplicated.json` | 3 | Observaciones únicas |
| `deduplication_stats.json` | 3 | Estadísticas de deduplicación |
| `observations_quality.json` | 4 | Observaciones con métricas |
| `quality_stats.json` | 4 | Estadísticas de calidad |
| `observations_selected.json` | 5 | Observaciones seleccionadas |
| `selection_stats.json` | 5 | Estadísticas de selección |

## Reanudación

Si el pipeline se interrumpe, se puede reanudar desde cualquier etapa. Los archivos intermedios permiten continuar sin repetir trabajo (**MUY IMPORTANTE** en nuestra zona, sopla una brisa y nos quedamos sin energía eléctrica...).

## Logs

Cada etapa genera logs en `data/{dataset}/logs/`:

```
logs/
├── fetch_observations.log
├── download_images.log
├── deduplicate.log
├── assess_quality.log
├── select_samples.log
└── organize_dataset.log
```
