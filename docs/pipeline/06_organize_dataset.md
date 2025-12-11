# Etapa 6: Organización del Dataset

Script: `scripts/06_organize_dataset.py`

## Descripción

Esta etapa final organiza las imágenes seleccionadas en una estructura de directorios estándar, genera manifests, metadatos y documentación del dataset resultante.

## Uso

```bash
python scripts/06_organize_dataset.py --config config/mi_config.yaml
```

### Argumentos

| Argumento | Descripción | Valor por defecto |
|-----------|-------------|-------------------|
| `--config` | Ruta al archivo de configuración YAML | `config/paraense_fauna.yaml` |
| `--output-dir` | Directorio de salida | `data/final_datasets` |
| `--dataset-name` | Nombre del dataset | Derivado de config |

## Funcionamiento

1. **Creación de estructura**: Genera directorios organizados por especie
2. **Copia de imágenes**: Mueve imágenes seleccionadas a la estructura final
3. **Generación de manifests**: Crea índices JSON de todas las imágenes
4. **Metadatos**: Genera archivo YAML con información del dataset
5. **Estadísticas**: Calcula métricas detalladas
6. **Documentación**: Genera README específico del dataset
7. **Validación**: Verifica integridad del dataset generado

## Salida

### Estructura del Dataset

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
    │   ├── 123456790.jpg
    │   └── 123456790.json
    └── ramphastos_toco/
        ├── 987654321.jpg
        └── 987654321.json
```

### species_manifest.json

Índice de todas las imágenes organizadas por especie:

```json
{
  "dataset_name": "selva_paranaense_dataset",
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

Metadatos completos del dataset:

```yaml
name: selva_paranaense_dataset
version: "1.0"
created_at: "2024-12-11T10:30:00"
description: "Dataset de fauna de la Selva Paranaense"

source:
  platform: iNaturalist
  api_version: v1
  quality_grade: research
  geographic_region: "Misiones, Argentina"
  place_id: 10422

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
  
citation: |
  Si utilizas este dataset, por favor cita:
  - iNaturalist (https://www.inaturalist.org)
  - Los fotógrafos individuales
```

### statistics.json

Estadísticas detalladas:

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
    "bounding_box": {
      "north": -25.0,
      "south": -28.0,
      "east": -53.5,
      "west": -56.0
    },
    "unique_locations": 185
  },
  "temporal": {
    "date_range": ["2020-01-15", "2024-11-30"],
    "observations_by_year": {
      "2020": 25,
      "2021": 45,
      "2022": 55,
      "2023": 50,
      "2024": 25
    }
  },
  "by_species": {
    "turdus_rufiventris": {
      "count": 100,
      "mean_quality": 72.1
    }
  }
}
```

### README.md del Dataset

Se genera automáticamente un README específico para el dataset:

```markdown
# Dataset: Selva Paranaense

## Descripción
Dataset de fauna silvestre de la Selva Paranaense...

## Contenido
- 2 especies
- 200 imágenes

## Especies incluidas
| Especie | Imágenes |
|---------|----------|
| Turdus rufiventris | 100 |
| Ramphastos toco | 100 |

## Uso
...

## Licencia
...
```

## Validación

El organizador ejecuta validaciones automáticas:

| Verificación | Descripción |
|--------------|-------------|
| Integridad de archivos | Todas las imágenes del manifest existen |
| Formato de imágenes | Archivos son imágenes válidas |
| Metadatos completos | Cada imagen tiene su JSON asociado |
| Consistencia de conteos | Números en manifest coinciden con archivos |

### Resultado de validación

```json
{
  "status": "PASSED",
  "total_species": 2,
  "total_images_manifest": 200,
  "total_images_checked": 200,
  "missing_images": 0,
  "invalid_images": 0
}
```

## Consideraciones

### Nombres de Directorios

Los nombres de especies se normalizan:
- Espacios → guiones bajos
- Minúsculas
- Caracteres especiales removidos

Ejemplo: "Turdus rufiventris" → `turdus_rufiventris`

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

## Scripts Auxiliares

### Validación manual

```bash
python scripts/helpers/validate_dataset.py \
    --dataset data/final_datasets/mi_dataset/
```

### Estadísticas adicionales

```bash
python scripts/helpers/compute_statistics.py \
    --dataset data/final_datasets/mi_dataset/
```

## Módulos Utilizados

- [`dataset_organizer.py`](../modules/dataset_organizer.md) - Organización y manifests

## Resultado Final

Al completar esta etapa, se tiene un dataset listo para:
- Entrenamiento de modelos de clasificación
- Evaluación de backbones de visión
- Tareas de few-shot learning
- Benchmarking de algoritmos

El dataset está completamente documentado y es reproducible.
