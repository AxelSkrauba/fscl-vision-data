# FSCL-Vision Data Pipeline

Pipeline de adquisición y preparación de datasets de fauna silvestre desde iNaturalist para el framework FSCL-Vision (Few-Shot Classification Learning).

## Descripción

Este repositorio proporciona herramientas para la conformación de datasets de alta calidad orientados a tareas de clasificación de imágenes con pocos ejemplos (few-shot learning). El pipeline completo incluye:

1. **Obtención de datos** desde iNaturalist API v1 con rate-limiting y caché local
2. **Descarga de imágenes** con metadatos asociados y manejo robusto de errores
3. **Deduplicación inteligente** mediante clustering espacio-temporal (DBSCAN)
4. **Evaluación de calidad** de imágenes (nitidez, exposición, contraste, composición)
5. **Selección de muestras representativas** con múltiples estrategias (clustering, calidad, estratificado)
6. **Organización estructurada** de datasets con manifests y metadatos completos

## Instalación

```bash
git clone https://github.com/AxelSkrauba/fscl-vision-data.git
cd fscl-vision-data
python -m venv env
source env/bin/activate  # En Windows: .\env\Scripts\activate
pip install -r requirements.txt
```

## Uso Rápido

### Opción 1: Pipeline completo automatizado

```bash
python scripts/helpers/run_full_pipeline.py --config config/paraense_fauna.yaml
```

### Opción 2: Ejecución por etapas

```bash
# 1. Configurar tu dataset
cp config/paraense_fauna.yaml config/my_dataset.yaml
# Editar según tu región y especies de interés

# 2. Ejecutar cada etapa del pipeline
python scripts/01_fetch_observations.py --config config/my_dataset.yaml
python scripts/02_download_images.py --config config/my_dataset.yaml
python scripts/03_deduplicate.py --config config/my_dataset.yaml
python scripts/04_assess_quality.py --config config/my_dataset.yaml
python scripts/05_select_samples.py --config config/my_dataset.yaml
python scripts/06_organize_dataset.py --config config/my_dataset.yaml

# 3. Validar dataset generado
python scripts/helpers/validate_dataset.py --dataset data/final_datasets/my_dataset/
```

### Prueba rápida

Para verificar que el pipeline funciona correctamente:

```bash
python scripts/helpers/run_full_pipeline.py --config config/test_config.yaml
```

## Estructura del Proyecto

```
fscl-vision-data/
├── config/                     # Archivos de configuración YAML
│   ├── default.yaml            # Configuración base
│   ├── paraense_fauna.yaml     # Fauna de la Selva Paranaense
│   └── test_config.yaml        # Configuración para pruebas rápidas
├── src/                        # Código fuente
│   ├── api_client.py           # Cliente iNaturalist API
│   ├── image_downloader.py     # Descarga paralela de imágenes
│   ├── deduplicator.py         # Deduplicación espacio-temporal
│   ├── quality_assessor.py     # Evaluación de calidad de imágenes
│   ├── sample_selector.py      # Selección de muestras representativas
│   ├── dataset_organizer.py    # Organización del dataset final
│   ├── local_cache.py          # Caché local para respuestas API
│   └── utils/                  # Utilidades (logger, rate_limiter, geo_utils, image_utils)
├── scripts/                    # Scripts del pipeline
│   ├── 01_fetch_observations.py
│   ├── 02_download_images.py
│   ├── 03_deduplicate.py
│   ├── 04_assess_quality.py
│   ├── 05_select_samples.py
│   ├── 06_organize_dataset.py
│   └── helpers/                # Scripts auxiliares
│       ├── run_full_pipeline.py
│       ├── validate_dataset.py
│       └── compute_statistics.py
├── docs/                       # Documentación detallada
│   ├── modules/                # Documentación por módulo
│   └── pipeline/               # Guía de cada etapa del pipeline
├── data/                       # Datos generados (gitignored)
│   ├── cache/                  # Caché de API y archivos intermedios
│   ├── raw/                    # Imágenes descargadas
│   └── final_datasets/         # Datasets organizados
└── tests/                      # Tests unitarios
```

## Documentación

Para información detallada sobre cada componente del pipeline, consultar:

- **[Guía de Configuración](docs/configuration.md)** - Parámetros y opciones de configuración
- **[Etapas del Pipeline](docs/pipeline/)** - Documentación de cada etapa
- **[Módulos](docs/modules/)** - Referencia técnica de cada módulo

## Configuración

Ver `config/paraense_fauna.yaml` para un ejemplo completo de configuración.

Parámetros principales:

| Sección | Descripción |
|---------|-------------|
| `geography` | Región geográfica (`place_id` de iNaturalist o bounding box) |
| `fauna.taxa` | Lista de especies con `taxon_id` verificados |
| `quality` | Umbrales de calidad de imagen (dimensiones mínimas, score) |
| `deduplication` | Parámetros de clustering espacio-temporal |
| `sampling` | Método de selección y cantidad de muestras por especie |

**Nota**: Los `taxon_id` y `place_id` deben verificarse en la API de iNaturalist antes de usar.

## Salida

El pipeline genera un dataset estructurado con:

```
final_datasets/my_dataset/
├── species_manifest.json       # Índice de todas las imágenes por especie
├── dataset_metadata.yaml       # Estadísticas y proveniencia de datos
├── statistics.json             # Métricas detalladas del dataset
├── README.md                   # Documentación del dataset generado
└── images/
    └── {species_name}/         # Imágenes organizadas por especie
        ├── {observation_id}.jpg
        └── {observation_id}.json  # Metadatos de cada imagen
```

## Tests

```bash
# Ejecutar todos los tests
python -m pytest tests/ -v

# Ejecutar tests de un módulo específico
python -m pytest tests/test_deduplicator.py -v
```

## Licencia

MIT License

## Citación

Si utilizas este pipeline en tu investigación, por favor citar:

- El proyecto [iNaturalist](https://www.inaturalist.org/)
- Los fotógrafos individuales (ver metadatos de cada imagen)
- Este repositorio
