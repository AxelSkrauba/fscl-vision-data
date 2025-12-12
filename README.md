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

### Ejemplo: Dataset de Especies Amenazadas

El repositorio incluye un ejemplo completo de configuración para generar un dataset de especies amenazadas de la Selva Paranaense:

```bash
# Ejecutar pipeline completo con el ejemplo incluido
python scripts/helpers/run_full_pipeline.py --config config/datasets/especies_amenazadas_selva_paranaense.yaml
```

**Resultado esperado:**
- ~850 imágenes de ~29 especies amenazadas
- Dataset organizado en `data/final_datasets/especies_amenazadas_selva_paranaense/`
- Incluye manifests, metadatos y README generado automáticamente


### Crear tu Propio Dataset

```bash
# 1. Copiar configuración de ejemplo
cp config/datasets/especies_amenazadas_selva_paranaense.yaml config/datasets/mi_dataset.yaml

# 2. Editar según región y especies de interés
# - Cambiar place_id para la región de interés (buscar en iNaturalist)
# - Modificar lista de especies con taxon_id verificados
# - Ajustar parámetros de calidad y muestreo

# 3. Ejecutar pipeline
python scripts/helpers/run_full_pipeline.py --config config/datasets/mi_dataset.yaml
```

### Ejecución por Etapas

Para mayor control, ejecutar cada etapa individualmente:

```bash
python scripts/01_fetch_observations.py --config config/datasets/mi_dataset.yaml
python scripts/02_download_images.py --config config/datasets/mi_dataset.yaml
python scripts/03_deduplicate.py --config config/datasets/mi_dataset.yaml
python scripts/04_assess_quality.py --config config/datasets/mi_dataset.yaml
python scripts/05_select_samples.py --config config/datasets/mi_dataset.yaml
python scripts/06_organize_dataset.py --config config/datasets/mi_dataset.yaml
```

> **Nota**: El pipeline soporta continuación desde caché. Si una ejecución falla, al re-ejecutar continuará desde la última etapa completada.

## Estructura del Proyecto

```
fscl-vision-data/
├── config/                     # Archivos de configuración YAML
│   ├── default.yaml            # Configuración base
│   ├── paraense_fauna.yaml     # Fauna de la Selva Paranaense
│   ├── test_config.yaml        # Configuración para pruebas rápidas
│   └── datasets/               # Configuraciones de datasets específicos
│       ├── especies_amenazadas_selva_paranaense.yaml  # Ejemplo principal
│       └── ...
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

Ver [`config/datasets/especies_amenazadas_selva_paranaense.yaml`](config/datasets/especies_amenazadas_selva_paranaense.yaml) para un ejemplo completo y documentado.

### Estructura del Archivo YAML

```yaml
dataset:
  name: "mi_dataset"                    # Nombre del dataset (usado para directorio y manifests)
  version: "1.0"
  description: "Descripción del dataset"
  target_task: "multi-class classification"
  notes: "Notas adicionales"

geography:
  region_name: "Mi Región"
  place_id: 12345                        # ID de lugar en iNaturalist
  country: "País"

quality:
  minimum_width: 300
  minimum_height: 300
  quality_score_threshold: 30

sampling:
  method: "quality"                      # quality, clustering, stratified
  n_samples_per_species: 50
  min_samples_per_species: 3

fauna:
  taxa:
    - name: "Panthera onca"
      taxon_id: 41944                    # Verificar en iNaturalist
      common_names: ["Jaguar"]
      max_observations: 30
```

### Parámetros Principales

| Sección | Descripción |
|---------|-------------|
| `dataset` | Nombre, versión y descripción del dataset |
| `geography` | Región geográfica (`place_id` de iNaturalist) |
| `fauna.taxa` | Lista de especies con `taxon_id` verificados |
| `quality` | Umbrales de calidad de imagen (dimensiones mínimas, score) |
| `deduplication` | Parámetros de clustering espacio-temporal |
| `sampling` | Método de selección y cantidad de muestras por especie |

> **Importante**: Los `taxon_id` y `place_id` deben verificarse en [iNaturalist](https://www.inaturalist.org/) antes de usar.

## Salida

El pipeline genera un dataset estructurado con:

```
final_datasets/especies_amenazadas_selva_paranaense/
├── species_manifest.json       # Índice de todas las imágenes por especie
├── dataset_metadata.yaml       # Estadísticas y proveniencia de datos
├── statistics.json             # Métricas detalladas del dataset
├── README.md                   # Documentación del dataset generado
└── images/
    └── {taxon_id}/             # Imágenes organizadas por especie
        ├── {obs_id}_{photo_id}.jpg
        └── {obs_id}_{photo_id}.json  # Metadatos de cada imagen
```

### Ejemplo de README Generado

El README del dataset incluye automáticamente:
- Descripción y notas del YAML original
- Cobertura geográfica (región, país, provincia)
- Configuración del pipeline (calidad, muestreo)
- Lista de especies con cantidad de imágenes
- Instrucciones de uso y carga del dataset

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
