# Dataset Organizer

Módulo: `src/dataset_organizer.py`

## Descripción

Organiza las observaciones seleccionadas en una estructura de directorios estándar, genera manifests, metadatos y documentación del dataset resultante.

## Clase Principal

### `DatasetOrganizer`

```python
from src.dataset_organizer import DatasetOrganizer

organizer = DatasetOrganizer(
    output_dir="./data/final_datasets",
    logger=None
)
```

#### Parámetros del Constructor

| Parámetro | Tipo | Descripción | Valor por defecto |
|-----------|------|-------------|-------------------|
| `output_dir` | str/Path | Directorio de salida | `"./data/final_datasets"` |
| `logger` | Logger | Logger opcional | `None` |

## Métodos

### `organize`

Organiza un conjunto de observaciones en un dataset estructurado.

```python
result = organizer.organize(
    observations,
    dataset_name="mi_dataset",
    source_image_dir="./data/raw",
    config=None
)
```

#### Parámetros

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `observations` | List[Dict] | Observaciones seleccionadas |
| `dataset_name` | str | Nombre del dataset |
| `source_image_dir` | str/Path | Directorio con imágenes originales |
| `config` | Dict | Configuración del pipeline (opcional) |

#### Retorno

Diccionario con información del dataset generado:

```python
{
    'dataset_path': Path,
    'total_species': int,
    'total_images': int,
    'validation': Dict
}
```

### `validate`

Valida la integridad de un dataset existente.

```python
validation = organizer.validate(dataset_path)
```

#### Retorno

```python
{
    'status': 'PASSED' | 'FAILED',
    'total_species': int,
    'total_images_manifest': int,
    'total_images_checked': int,
    'missing_images': int,
    'invalid_images': int,
    'errors': List[str]
}
```

### `generate_manifest`

Genera el archivo `species_manifest.json`.

```python
manifest = organizer.generate_manifest(
    observations,
    dataset_name
)
```

### `generate_metadata`

Genera el archivo `dataset_metadata.yaml`.

```python
metadata = organizer.generate_metadata(
    observations,
    dataset_name,
    config
)
```

### `generate_statistics`

Calcula estadísticas detalladas del dataset.

```python
stats = organizer.generate_statistics(observations)
```

### `generate_readme`

Genera documentación README del dataset.

```python
readme = organizer.generate_readme(
    dataset_name,
    manifest,
    metadata,
    stats
)
```

## Estructura Generada

```
final_datasets/{dataset_name}/
├── species_manifest.json       # Índice principal
├── dataset_metadata.yaml       # Metadatos y proveniencia
├── statistics.json             # Estadísticas detalladas
├── README.md                   # Documentación del dataset
└── images/
    ├── turdus_rufiventris/
    │   ├── 123456789.jpg
    │   ├── 123456789.json
    │   └── ...
    └── ramphastos_toco/
        ├── 987654321.jpg
        ├── 987654321.json
        └── ...
```

## Archivos Generados

### species_manifest.json

```json
{
  "dataset_name": "mi_dataset",
  "created_at": "2024-12-11T10:30:00",
  "total_species": 2,
  "total_images": 200,
  "species": {
    "turdus_rufiventris": {
      "taxon_id": 12738,
      "scientific_name": "Turdus rufiventris",
      "common_names": ["Zorzal colorado"],
      "image_count": 100,
      "images": [
        {
          "filename": "123456789.jpg",
          "observation_id": 123456789,
          "quality_score": 75.3,
          "location": {"lat": -25.68, "lon": -54.45},
          "observed_on": "2024-01-15"
        }
      ]
    }
  }
}
```

### dataset_metadata.yaml

```yaml
name: mi_dataset
version: "1.0"
created_at: "2024-12-11T10:30:00"
description: "Dataset generado por FSCL-Vision Data Pipeline"

source:
  platform: iNaturalist
  api_version: v1
  quality_grade: research

pipeline:
  deduplication:
    spatial_threshold_m: 100
    temporal_threshold_days: 1
  quality:
    score_threshold: 40
  sampling:
    method: quality
    n_per_species: 100

statistics:
  total_species: 2
  total_images: 200
  mean_quality_score: 68.5

license:
  dataset: MIT
  images: "Ver metadatos individuales"
```

### statistics.json

```json
{
  "overview": {
    "total_species": 2,
    "total_images": 200,
    "total_size_mb": 45.2
  },
  "quality": {
    "mean_score": 68.5,
    "std_score": 12.3,
    "min_score": 42.1,
    "max_score": 92.5
  },
  "geographic": {
    "bounding_box": {...},
    "unique_locations": 185
  },
  "temporal": {
    "date_range": ["2020-01-15", "2024-11-30"],
    "observations_by_year": {...}
  },
  "by_species": {...}
}
```

## Ejemplo Completo

```python
from src.dataset_organizer import DatasetOrganizer
import json
import yaml

# Cargar observaciones seleccionadas
with open('observations_selected.json') as f:
    observations = json.load(f)

# Cargar configuración
with open('config/mi_config.yaml') as f:
    config = yaml.safe_load(f)

# Crear organizador
organizer = DatasetOrganizer(output_dir="./data/final_datasets")

# Organizar dataset
result = organizer.organize(
    observations=observations,
    dataset_name="selva_paranaense_v1",
    source_image_dir="./data/raw",
    config=config
)

print(f"Dataset creado: {result['dataset_path']}")
print(f"Especies: {result['total_species']}")
print(f"Imágenes: {result['total_images']}")
print(f"Validación: {result['validation']['status']}")

# Validar dataset existente
validation = organizer.validate(result['dataset_path'])
if validation['status'] == 'PASSED':
    print("Dataset válido")
else:
    print(f"Errores: {validation['errors']}")
```

## Normalización de Nombres

Los nombres de especies se normalizan para usar como nombres de directorio:

```python
def _normalize_species_name(self, name):
    # "Turdus rufiventris" -> "turdus_rufiventris"
    normalized = name.lower()
    normalized = normalized.replace(' ', '_')
    normalized = re.sub(r'[^a-z0-9_]', '', normalized)
    return normalized
```

## Validaciones

El organizador ejecuta validaciones automáticas:

| Verificación | Descripción |
|--------------|-------------|
| Existencia de archivos | Todas las imágenes del manifest existen |
| Formato de imágenes | Archivos son imágenes válidas (PIL puede abrirlas) |
| Metadatos | Cada imagen tiene su JSON asociado |
| Consistencia | Conteos en manifest coinciden con archivos |

## Consideraciones

### Copia vs Enlace

Por defecto, las imágenes se copian al directorio final. Para datasets grandes, considerar usar enlaces simbólicos (no implementado actualmente).

### Metadatos por Imagen

Cada imagen incluye un archivo JSON con:
- ID de observación original
- Información del fotógrafo
- Licencia de uso
- Coordenadas geográficas
- Fecha de observación
- Métricas de calidad

### Reproducibilidad

El dataset incluye toda la información necesaria para:
- Rastrear la proveniencia de cada imagen
- Reproducir el proceso de generación
- Citar correctamente las fuentes

## Dependencias

- `pathlib`: Manejo de rutas
- `shutil`: Copia de archivos
- `yaml`: Generación de metadatos
- [`image_utils.py`](utils/image_utils.md): Validación de imágenes
