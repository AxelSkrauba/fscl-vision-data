# Documentación de FSCL-Vision Data Pipeline

Bienvenido a la documentación detallada del pipeline de datos para FSCL-Vision.

## Contenido

### Guías Generales

- **[Configuración](configuration.md)** - Guía completa de parámetros de configuración YAML

### Etapas del Pipeline

El pipeline se ejecuta en 6 etapas secuenciales:

| Etapa | Script | Descripción |
|-------|--------|-------------|
| 1 | [01_fetch_observations](pipeline/01_fetch_observations.md) | Obtención de observaciones desde iNaturalist |
| 2 | [02_download_images](pipeline/02_download_images.md) | Descarga paralela de imágenes |
| 3 | [03_deduplicate](pipeline/03_deduplicate.md) | Deduplicación espacio-temporal |
| 4 | [04_assess_quality](pipeline/04_assess_quality.md) | Evaluación de calidad de imágenes |
| 5 | [05_select_samples](pipeline/05_select_samples.md) | Selección de muestras representativas |
| 6 | [06_organize_dataset](pipeline/06_organize_dataset.md) | Organización del dataset final |

### Referencia de Módulos

Documentación técnica de cada módulo del código fuente:

| Módulo | Descripción |
|--------|-------------|
| [api_client](modules/api_client.md) | Cliente para iNaturalist API v1 |
| [image_downloader](modules/image_downloader.md) | Descarga paralela de imágenes |
| [deduplicator](modules/deduplicator.md) | Clustering espacio-temporal |
| [quality_assessor](modules/quality_assessor.md) | Evaluación de calidad de imágenes |
| [sample_selector](modules/sample_selector.md) | Selección de muestras representativas |
| [dataset_organizer](modules/dataset_organizer.md) | Organización y generación de manifests |

### Utilidades

| Módulo | Descripción |
|--------|-------------|
| [logger](modules/utils/logger.md) | Sistema de logging estructurado |
| [rate_limiter](modules/utils/rate_limiter.md) | Control de tasa de llamadas API |
| [geo_utils](modules/utils/geo_utils.md) | Utilidades geográficas |
| [image_utils](modules/utils/image_utils.md) | Procesamiento de imágenes |
| [local_cache](modules/local_cache.md) | Caché local para respuestas API |

## Flujo del Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FSCL-Vision Data Pipeline                    │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  1. FETCH OBSERVATIONS                                              │
│     - Consulta iNaturalist API                                      │
│     - Aplica filtros geográficos y taxonómicos                      │
│     - Respeta rate-limiting                                         │
│     - Cachea respuestas localmente                                  │
│     Salida: observations.json                                       │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  2. DOWNLOAD IMAGES                                                 │
│     - Descarga imágenes en paralelo                                 │
│     - Valida integridad de archivos                                 │
│     - Guarda metadatos por imagen                                   │
│     Salida: raw/{species}/*.jpg + *.json                            │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  3. DEDUPLICATE                                                     │
│     - Agrupa por especie                                            │
│     - Clustering DBSCAN espacio-temporal                            │
│     - Selecciona mejor observación por cluster                      │
│     Salida: observations_deduplicated.json                          │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  4. ASSESS QUALITY                                                  │
│     - Evalúa nitidez, exposición, contraste                         │
│     - Calcula score compuesto                                       │
│     - Filtra por umbrales de calidad                                │
│     Salida: observations_quality.json                               │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  5. SELECT SAMPLES                                                  │
│     - Aplica método de selección (quality/clustering/stratified)    │
│     - Balancea entre especies si está configurado                   │
│     - Filtra especies con mínimo insuficiente                       │
│     Salida: observations_selected.json                              │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  6. ORGANIZE DATASET                                                │
│     - Crea estructura de directorios                                │
│     - Copia imágenes seleccionadas                                  │
│     - Genera manifests y metadatos                                  │
│     - Valida integridad del dataset                                 │
│     Salida: final_datasets/{dataset_name}/                          │
└─────────────────────────────────────────────────────────────────────┘
```

## Inicio Rápido

1. **Configurar**: Crear o modificar un archivo YAML en `config/`
2. **Ejecutar**: `python scripts/helpers/run_full_pipeline.py --config config/mi_config.yaml`
3. **Validar**: `python scripts/helpers/validate_dataset.py --dataset data/final_datasets/mi_dataset/`

Para más detalles, consultar la [Guía de Configuración](configuration.md).
