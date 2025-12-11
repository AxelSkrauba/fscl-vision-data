# Referencia de Módulos

Documentación técnica de los módulos del código fuente de FSCL-Vision Data Pipeline.

## Módulos Principales

| Módulo | Archivo | Descripción |
|--------|---------|-------------|
| [API Client](api_client.md) | `src/api_client.py` | Cliente para iNaturalist API v1 |
| [Image Downloader](image_downloader.md) | `src/image_downloader.py` | Descarga paralela de imágenes |
| [Deduplicator](deduplicator.md) | `src/deduplicator.py` | Clustering espacio-temporal |
| [Quality Assessor](quality_assessor.md) | `src/quality_assessor.py` | Evaluación de calidad de imágenes |
| [Sample Selector](sample_selector.md) | `src/sample_selector.py` | Selección de muestras representativas |
| [Dataset Organizer](dataset_organizer.md) | `src/dataset_organizer.py` | Organización y generación de manifests |
| [Local Cache](local_cache.md) | `src/local_cache.py` | Caché local para respuestas API |

## Utilidades

| Módulo | Archivo | Descripción |
|--------|---------|-------------|
| [Logger](utils/logger.md) | `src/utils/logger.py` | Sistema de logging estructurado |
| [Rate Limiter](utils/rate_limiter.md) | `src/utils/rate_limiter.py` | Control de tasa de llamadas |
| [Geo Utils](utils/geo_utils.md) | `src/utils/geo_utils.py` | Utilidades geográficas |
| [Image Utils](utils/image_utils.md) | `src/utils/image_utils.py` | Procesamiento de imágenes |

## Arquitectura

```
src/
├── __init__.py
├── api_client.py          ◄── Interacción con iNaturalist
├── local_cache.py         ◄── Caché de respuestas
├── image_downloader.py    ◄── Descarga de imágenes
├── deduplicator.py        ◄── Identificación de duplicados
├── quality_assessor.py    ◄── Evaluación de calidad
├── sample_selector.py     ◄── Selección representativa
├── dataset_organizer.py   ◄── Organización final
└── utils/
    ├── __init__.py
    ├── logger.py          ◄── Logging estructurado
    ├── rate_limiter.py    ◄── Control de tasa
    ├── geo_utils.py       ◄── Cálculos geográficos
    └── image_utils.py     ◄── Procesamiento de imágenes
```

## Dependencias entre Módulos

```
api_client
    ├── local_cache
    └── utils/rate_limiter

image_downloader
    └── utils/image_utils

deduplicator
    └── utils/geo_utils

quality_assessor
    └── utils/image_utils

sample_selector
    └── (standalone)

dataset_organizer
    └── utils/image_utils
```

## Uso Programático

Los módulos pueden usarse de forma independiente:

```python
from src.api_client import iNaturalistAPIClient
from src.deduplicator import ObservationDeduplicator
from src.quality_assessor import ImageQualityAssessor
from src.sample_selector import RepresentativeSampleSelector
from src.dataset_organizer import DatasetOrganizer

# Ejemplo: obtener observaciones
client = iNaturalistAPIClient()
observations = client.search_observations(
    taxon_id=12738,
    place_id=10422,
    quality_grade="research"
)

# Ejemplo: deduplicar
deduplicator = ObservationDeduplicator(
    spatial_threshold_m=100,
    temporal_threshold_days=1
)
result = deduplicator.deduplicate(observations)
unique_obs = [ind.best_observation for ind in result.unique_individuals]
```

## Convenciones

### Logging

Todos los módulos aceptan un `logger` opcional:

```python
import logging
logger = logging.getLogger(__name__)

client = iNaturalistAPIClient(logger=logger)
```

### Configuración

Los módulos reciben parámetros directamente, no archivos de configuración. Los scripts del pipeline se encargan de leer la configuración YAML y pasar los parámetros apropiados.

### Tipos de Datos

- **Observaciones**: Diccionarios con estructura de respuesta de iNaturalist
- **Resultados**: Dataclasses tipadas para resultados estructurados
- **Coordenadas**: Tuplas (latitud, longitud) en grados decimales
