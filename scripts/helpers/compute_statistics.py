#!/usr/bin/env python3
"""
Computa estadisticas detalladas del dataset.

Uso:
    python scripts/helpers/compute_statistics.py --dataset data/final_datasets/my_dataset/
"""

import argparse
import json
import sys
from pathlib import Path
from collections import defaultdict

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.logger import setup_logger


def main(dataset_path: str, output_file: str = None):
    """
    Computa estadisticas detalladas del dataset.
    
    Args:
        dataset_path: Ruta al directorio del dataset
        output_file: Archivo de salida para estadisticas (opcional)
    """
    logger = setup_logger('compute_statistics')
    
    dataset_path = Path(dataset_path)
    
    manifest_path = dataset_path / 'species_manifest.json'
    if not manifest_path.exists():
        logger.error(f"Manifest not found: {manifest_path}")
        return
    
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    logger.info(f"Computing statistics for: {manifest['dataset_name']}")
    
    stats = {
        'dataset_name': manifest['dataset_name'],
        'total_images': manifest['total_images'],
        'total_species': manifest['total_species'],
        'species': [],
        'quality': {},
        'temporal': {},
        'geographic': {}
    }
    
    all_quality_scores = []
    all_dates = []
    all_lats = []
    all_lons = []
    images_per_species = []
    
    for species_id, cls_data in manifest['classes'].items():
        species_stats = {
            'id': species_id,
            'name': cls_data['name'],
            'common_name': cls_data.get('common_name', ''),
            'count': cls_data['count']
        }
        
        quality_scores = []
        dates = []
        lats = []
        lons = []
        
        for img in cls_data['images']:
            if 'quality_score' in img:
                quality_scores.append(img['quality_score'])
                all_quality_scores.append(img['quality_score'])
            
            if img.get('observed_date'):
                dates.append(img['observed_date'])
                all_dates.append(img['observed_date'])
            
            loc = img.get('location', {})
            if loc.get('latitude') is not None:
                lats.append(loc['latitude'])
                all_lats.append(loc['latitude'])
            if loc.get('longitude') is not None:
                lons.append(loc['longitude'])
                all_lons.append(loc['longitude'])
        
        if quality_scores:
            species_stats['quality_mean'] = float(np.mean(quality_scores))
            species_stats['quality_std'] = float(np.std(quality_scores))
        
        stats['species'].append(species_stats)
        images_per_species.append(cls_data['count'])
    
    if all_quality_scores:
        stats['quality'] = {
            'mean': float(np.mean(all_quality_scores)),
            'std': float(np.std(all_quality_scores)),
            'min': float(np.min(all_quality_scores)),
            'max': float(np.max(all_quality_scores)),
            'median': float(np.median(all_quality_scores))
        }
    
    if all_dates:
        sorted_dates = sorted(all_dates)
        stats['temporal'] = {
            'earliest': sorted_dates[0],
            'latest': sorted_dates[-1],
            'total_observations': len(all_dates)
        }
        
        months = defaultdict(int)
        for d in all_dates:
            try:
                month = d.split('-')[1] if '-' in d else '00'
                months[month] += 1
            except:
                pass
        stats['temporal']['by_month'] = dict(months)
    
    if all_lats and all_lons:
        stats['geographic'] = {
            'north': float(np.max(all_lats)),
            'south': float(np.min(all_lats)),
            'east': float(np.max(all_lons)),
            'west': float(np.min(all_lons)),
            'centroid_lat': float(np.mean(all_lats)),
            'centroid_lon': float(np.mean(all_lons))
        }
    
    stats['distribution'] = {
        'images_per_species_mean': float(np.mean(images_per_species)),
        'images_per_species_std': float(np.std(images_per_species)),
        'images_per_species_min': int(np.min(images_per_species)),
        'images_per_species_max': int(np.max(images_per_species))
    }
    
    print("\n" + "=" * 60)
    print("DATASET STATISTICS")
    print("=" * 60)
    print(f"\nDataset: {stats['dataset_name']}")
    print(f"Total images: {stats['total_images']}")
    print(f"Total species: {stats['total_species']}")
    
    print("\n--- Distribution ---")
    print(f"  Images per species (mean): {stats['distribution']['images_per_species_mean']:.1f}")
    print(f"  Images per species (std): {stats['distribution']['images_per_species_std']:.1f}")
    print(f"  Images per species (min): {stats['distribution']['images_per_species_min']}")
    print(f"  Images per species (max): {stats['distribution']['images_per_species_max']}")
    
    if stats['quality']:
        print("\n--- Quality ---")
        print(f"  Mean: {stats['quality']['mean']:.1f}")
        print(f"  Std: {stats['quality']['std']:.1f}")
        print(f"  Range: [{stats['quality']['min']:.1f}, {stats['quality']['max']:.1f}]")
    
    if stats['temporal']:
        print("\n--- Temporal Coverage ---")
        print(f"  Earliest: {stats['temporal']['earliest']}")
        print(f"  Latest: {stats['temporal']['latest']}")
    
    if stats['geographic']:
        print("\n--- Geographic Coverage ---")
        print(f"  North: {stats['geographic']['north']:.4f}")
        print(f"  South: {stats['geographic']['south']:.4f}")
        print(f"  East: {stats['geographic']['east']:.4f}")
        print(f"  West: {stats['geographic']['west']:.4f}")
    
    print("\n--- Species ---")
    for sp in sorted(stats['species'], key=lambda x: -x['count']):
        quality_str = f" (q={sp['quality_mean']:.1f})" if 'quality_mean' in sp else ""
        print(f"  {sp['name']}: {sp['count']}{quality_str}")
    
    print("\n" + "=" * 60)
    
    if output_file:
        output_path = Path(output_file)
        with open(output_path, 'w') as f:
            json.dump(stats, f, indent=2)
        logger.info(f"Statistics saved to {output_path}")
    
    return stats


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Compute detailed dataset statistics'
    )
    parser.add_argument(
        '--dataset',
        required=True,
        help='Path to dataset directory'
    )
    parser.add_argument(
        '--output', '-o',
        default=None,
        help='Output file for statistics JSON'
    )
    
    args = parser.parse_args()
    main(args.dataset, args.output)
