"""
Organizador de dataset final para FSCL-Vision.

Organiza imagenes seleccionadas en estructura estandar con
manifests y metadata para reproducibilidad.
"""

import json
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass, asdict

import yaml
import numpy as np


@dataclass
class DatasetMetadata:
    """Metadata del dataset generado."""
    name: str
    description: str
    created_at: str
    total_images: int
    total_species: int
    source: str
    pipeline_version: str
    
    images_per_species: Dict[str, float] = None
    geographic_coverage: Dict[str, float] = None
    temporal_coverage: Dict[str, str] = None
    quality_metrics: Dict[str, float] = None
    data_provenance: Dict[str, Any] = None


class DatasetOrganizer:
    """
    Organiza imagenes seleccionadas en estructura final para FSCL-Vision.
    
    Estructura de salida:
    ```
    {dataset_name}/
    ├── images/
    │   ├── {species_id}/
    │   │   ├── {obs_id}_{photo_id}.jpg
    │   │   └── {obs_id}_{photo_id}.json
    │   └── ...
    ├── species_manifest.json
    ├── dataset_metadata.yaml
    ├── statistics.json
    └── README.md
    ```
    """
    
    PIPELINE_VERSION = "1.0.0"
    
    def __init__(
        self,
        source_dir: Optional[Path] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Inicializa el organizador.
        
        Args:
            source_dir: Directorio con imagenes descargadas (raw/)
            logger: Logger opcional
        """
        self.source_dir = Path(source_dir) if source_dir else None
        self.logger = logger or logging.getLogger(__name__)
    
    def _safe_float(self, value, default: float = 50.0) -> float:
        """Convierte un valor a float de forma segura."""
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def organize_dataset(
        self,
        observations: List[Dict[str, Any]],
        output_dir: Path,
        dataset_name: str,
        description: str = "",
        copy_images: bool = True,
        n_classes: Optional[int] = None,
        min_images_per_class: int = 10
    ) -> Path:
        """
        Organiza el dataset final.
        
        Args:
            observations: Lista de observaciones seleccionadas
            output_dir: Directorio base de salida
            dataset_name: Nombre del dataset
            description: Descripcion del dataset
            copy_images: Si copiar imagenes (False = solo crear manifest)
            n_classes: Limitar a N clases con mas imagenes
            min_images_per_class: Minimo de imagenes para incluir clase
        
        Returns:
            Path al directorio del dataset creado
        """
        output_dir = Path(output_dir)
        dataset_path = output_dir / dataset_name
        images_path = dataset_path / 'images'
        
        dataset_path.mkdir(parents=True, exist_ok=True)
        images_path.mkdir(parents=True, exist_ok=True)
        
        by_species = defaultdict(list)
        for obs in observations:
            taxon = obs.get('taxon', {})
            species_id = taxon.get('id')
            if species_id is not None:
                by_species[species_id].append(obs)
        
        by_species = {
            k: v for k, v in by_species.items()
            if len(v) >= min_images_per_class
        }
        
        if n_classes and len(by_species) > n_classes:
            sorted_species = sorted(
                by_species.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )
            by_species = dict(sorted_species[:n_classes])
        
        manifest = {
            'dataset_name': dataset_name,
            'created_at': datetime.now().isoformat(),
            'total_images': 0,
            'total_species': len(by_species),
            'classes': {}
        }
        
        all_quality_scores = []
        all_dates = []
        all_lats = []
        all_lons = []
        
        for species_id, species_obs in by_species.items():
            species_name = species_obs[0].get('taxon', {}).get('name', 'Unknown')
            common_name = species_obs[0].get('taxon', {}).get('preferred_common_name', '')
            
            species_dir = images_path / str(species_id)
            species_dir.mkdir(parents=True, exist_ok=True)
            
            manifest['classes'][str(species_id)] = {
                'name': species_name,
                'common_name': common_name,
                'count': len(species_obs),
                'images': []
            }
            
            for obs in species_obs:
                photos = obs.get('photos', [])
                if not photos:
                    continue
                
                photo = photos[0]
                obs_id = obs.get('id', 'unknown')
                photo_id = photo.get('id', 0)
                quality_score = self._safe_float(obs.get('quality_score', 50))
                
                filename = f"{obs_id}_{photo_id}.jpg"
                
                if copy_images and self.source_dir:
                    source_image = self.source_dir / str(species_id) / filename
                    dest_image = species_dir / filename
                    
                    if source_image.exists() and not dest_image.exists():
                        shutil.copy2(source_image, dest_image)
                    
                    source_meta = source_image.with_suffix('.json')
                    if source_meta.exists():
                        dest_meta = dest_image.with_suffix('.json')
                        if not dest_meta.exists():
                            shutil.copy2(source_meta, dest_meta)
                
                image_entry = {
                    'filename': filename,
                    'observation_id': obs_id,
                    'photo_id': photo_id,
                    'quality_score': round(quality_score, 2),
                    'observed_date': obs.get('observed_on', ''),
                    'location': {
                        'latitude': obs.get('latitude'),
                        'longitude': obs.get('longitude'),
                        'accuracy_m': obs.get('positional_accuracy')
                    },
                    'license': photo.get('license_code', ''),
                    'attribution': photo.get('attribution', '')
                }
                
                manifest['classes'][str(species_id)]['images'].append(image_entry)
                manifest['total_images'] += 1
                
                all_quality_scores.append(quality_score)
                if obs.get('observed_on'):
                    all_dates.append(obs['observed_on'])
                if obs.get('latitude') is not None:
                    all_lats.append(self._safe_float(obs['latitude'], 0))
                if obs.get('longitude') is not None:
                    all_lons.append(self._safe_float(obs['longitude'], 0))
            
            self.logger.info(
                f"Organized {species_name}: {len(species_obs)} images"
            )
        
        manifest_path = dataset_path / 'species_manifest.json'
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        metadata = self._create_metadata(
            dataset_name=dataset_name,
            description=description,
            manifest=manifest,
            quality_scores=all_quality_scores,
            dates=all_dates,
            lats=all_lats,
            lons=all_lons,
            observations=observations
        )
        
        metadata_path = dataset_path / 'dataset_metadata.yaml'
        with open(metadata_path, 'w', encoding='utf-8') as f:
            yaml.dump(asdict(metadata), f, default_flow_style=False, allow_unicode=True)
        
        statistics = self._compute_statistics(manifest, all_quality_scores)
        stats_path = dataset_path / 'statistics.json'
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(statistics, f, indent=2)
        
        readme = self._generate_readme(dataset_name, description, manifest, metadata)
        readme_path = dataset_path / 'README.md'
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme)
        
        self.logger.info(
            f"Dataset '{dataset_name}' organized: "
            f"{manifest['total_images']} images, "
            f"{manifest['total_species']} species"
        )
        
        return dataset_path
    
    def _create_metadata(
        self,
        dataset_name: str,
        description: str,
        manifest: Dict,
        quality_scores: List[float],
        dates: List[str],
        lats: List[float],
        lons: List[float],
        observations: List[Dict]
    ) -> DatasetMetadata:
        """Crea metadata del dataset."""
        images_counts = [
            len(cls['images']) for cls in manifest['classes'].values()
        ]
        
        images_per_species = {
            'mean': float(np.mean(images_counts)) if images_counts else 0,
            'min': int(np.min(images_counts)) if images_counts else 0,
            'max': int(np.max(images_counts)) if images_counts else 0,
            'std': float(np.std(images_counts)) if images_counts else 0
        }
        
        geographic_coverage = {}
        if lats and lons:
            geographic_coverage = {
                'north': float(np.max(lats)),
                'south': float(np.min(lats)),
                'east': float(np.max(lons)),
                'west': float(np.min(lons))
            }
        
        temporal_coverage = {}
        if dates:
            sorted_dates = sorted([d for d in dates if d])
            if sorted_dates:
                temporal_coverage = {
                    'earliest': sorted_dates[0],
                    'latest': sorted_dates[-1]
                }
        
        quality_metrics = {}
        if quality_scores:
            quality_metrics = {
                'mean': float(np.mean(quality_scores)),
                'min': float(np.min(quality_scores)),
                'max': float(np.max(quality_scores)),
                'std': float(np.std(quality_scores))
            }
        
        data_provenance = {
            'source': 'iNaturalist',
            'total_observations_processed': len(observations),
            'pipeline_stages': [
                'fetch_observations',
                'download_images',
                'deduplicate',
                'assess_quality',
                'select_samples',
                'organize_dataset'
            ]
        }
        
        return DatasetMetadata(
            name=dataset_name,
            description=description or f"Wildlife dataset: {dataset_name}",
            created_at=datetime.now().isoformat(),
            total_images=manifest['total_images'],
            total_species=manifest['total_species'],
            source='iNaturalist',
            pipeline_version=self.PIPELINE_VERSION,
            images_per_species=images_per_species,
            geographic_coverage=geographic_coverage,
            temporal_coverage=temporal_coverage,
            quality_metrics=quality_metrics,
            data_provenance=data_provenance
        )
    
    def _compute_statistics(
        self,
        manifest: Dict,
        quality_scores: List[float]
    ) -> Dict[str, Any]:
        """Computa estadisticas detalladas del dataset."""
        species_stats = []
        
        for species_id, cls_data in manifest['classes'].items():
            cls_quality = [
                img['quality_score'] for img in cls_data['images']
                if 'quality_score' in img
            ]
            
            species_stats.append({
                'species_id': species_id,
                'name': cls_data['name'],
                'common_name': cls_data.get('common_name', ''),
                'count': cls_data['count'],
                'quality_mean': float(np.mean(cls_quality)) if cls_quality else 0,
                'quality_std': float(np.std(cls_quality)) if cls_quality else 0
            })
        
        return {
            'summary': {
                'total_images': manifest['total_images'],
                'total_species': manifest['total_species'],
                'images_per_species_mean': float(np.mean([s['count'] for s in species_stats])),
                'quality_overall_mean': float(np.mean(quality_scores)) if quality_scores else 0
            },
            'by_species': species_stats,
            'distribution': {
                'images_histogram': self._compute_histogram(
                    [s['count'] for s in species_stats]
                ),
                'quality_histogram': self._compute_histogram(quality_scores)
            }
        }
    
    def _compute_histogram(
        self,
        values: List[float],
        n_bins: int = 10
    ) -> Dict[str, List]:
        """Computa histograma de valores."""
        if not values:
            return {'bins': [], 'counts': []}
        
        counts, bin_edges = np.histogram(values, bins=n_bins)
        
        return {
            'bins': [float(b) for b in bin_edges],
            'counts': [int(c) for c in counts]
        }
    
    def _generate_readme(
        self,
        dataset_name: str,
        description: str,
        manifest: Dict,
        metadata: DatasetMetadata
    ) -> str:
        """Genera README.md para el dataset."""
        species_list = "\n".join([
            f"- **{cls['name']}** ({cls.get('common_name', '')}): {cls['count']} images"
            for cls in manifest['classes'].values()
        ])
        
        readme = f"""# {dataset_name}

{description or 'Wildlife image dataset for few-shot classification.'}

## Overview

- **Total Images**: {manifest['total_images']}
- **Total Species**: {manifest['total_species']}
- **Source**: iNaturalist
- **Created**: {metadata.created_at}
- **Pipeline Version**: {metadata.pipeline_version}

## Species Included

{species_list}

## Directory Structure

```
{dataset_name}/
├── images/
│   ├── {{species_id}}/
│   │   ├── {{obs_id}}_{{photo_id}}.jpg
│   │   └── {{obs_id}}_{{photo_id}}.json
│   └── ...
├── species_manifest.json
├── dataset_metadata.yaml
├── statistics.json
└── README.md
```

## Usage

### Loading the Dataset

```python
import json
from pathlib import Path

dataset_path = Path("{dataset_name}")

# Load manifest
with open(dataset_path / "species_manifest.json") as f:
    manifest = json.load(f)

# Iterate over species
for species_id, species_data in manifest["classes"].items():
    print(f"{{species_data['name']}}: {{species_data['count']}} images")
    
    for img in species_data["images"]:
        img_path = dataset_path / "images" / species_id / img["filename"]
        # Load and process image...
```

## License & Attribution

Images are sourced from iNaturalist and retain their original licenses.
Each image's metadata JSON file contains license and attribution information.

**Important**: Check individual image licenses before commercial use.

## Citation

If you use this dataset, please cite:
- iNaturalist (https://www.inaturalist.org)
- Individual photographers (see image metadata)
- FSCL-Vision project
"""
        return readme
    
    def validate_dataset(self, dataset_path: Path) -> Dict[str, Any]:
        """
        Valida integridad del dataset.
        
        Args:
            dataset_path: Ruta al dataset
        
        Returns:
            Dict con resultados de validacion
        """
        dataset_path = Path(dataset_path)
        
        validation = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'stats': {}
        }
        
        manifest_path = dataset_path / 'species_manifest.json'
        if not manifest_path.exists():
            validation['valid'] = False
            validation['errors'].append("Missing species_manifest.json")
            return validation
        
        try:
            with open(manifest_path, encoding='utf-8') as f:
                manifest = json.load(f)
        except json.JSONDecodeError as e:
            validation['valid'] = False
            validation['errors'].append(f"Invalid manifest JSON: {e}")
            return validation
        
        images_path = dataset_path / 'images'
        if not images_path.exists():
            validation['valid'] = False
            validation['errors'].append("Missing images/ directory")
            return validation
        
        missing_images = 0
        total_images = 0
        
        for species_id, cls_data in manifest['classes'].items():
            species_dir = images_path / str(species_id)
            
            if not species_dir.exists():
                validation['warnings'].append(
                    f"Missing directory for species {species_id}"
                )
                continue
            
            for img in cls_data['images']:
                total_images += 1
                img_path = species_dir / img['filename']
                
                if not img_path.exists():
                    missing_images += 1
        
        if missing_images > 0:
            validation['warnings'].append(
                f"{missing_images}/{total_images} images missing"
            )
        
        validation['stats'] = {
            'total_species': len(manifest['classes']),
            'total_images_manifest': manifest['total_images'],
            'total_images_checked': total_images,
            'missing_images': missing_images
        }
        
        self.logger.info(
            f"Validation complete: {validation['stats']}"
        )
        
        return validation
