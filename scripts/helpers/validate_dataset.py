#!/usr/bin/env python3
"""
Validacion de integridad del dataset generado.

Uso:
    python scripts/helpers/validate_dataset.py --dataset data/final_datasets/my_dataset/
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.dataset_organizer import DatasetOrganizer
from src.utils.logger import setup_logger


def main(dataset_path: str, verbose: bool = False):
    """
    Valida integridad del dataset.
    
    Args:
        dataset_path: Ruta al directorio del dataset
        verbose: Mostrar detalles adicionales
    """
    logger = setup_logger('validate_dataset')
    
    dataset_path = Path(dataset_path)
    
    if not dataset_path.exists():
        logger.error(f"Dataset path not found: {dataset_path}")
        return False
    
    logger.info(f"Validating dataset: {dataset_path}")
    
    organizer = DatasetOrganizer(logger=logger)
    validation = organizer.validate_dataset(dataset_path)
    
    print("\n" + "=" * 60)
    print("DATASET VALIDATION REPORT")
    print("=" * 60)
    print(f"\nDataset: {dataset_path}")
    print(f"Status: {'VALID' if validation['valid'] else 'INVALID'}")
    
    print("\n--- Statistics ---")
    for key, value in validation['stats'].items():
        print(f"  {key}: {value}")
    
    if validation['warnings']:
        print("\n--- Warnings ---")
        for w in validation['warnings']:
            print(f"  [WARN] {w}")
    
    if validation['errors']:
        print("\n--- Errors ---")
        for e in validation['errors']:
            print(f"  [ERROR] {e}")
    
    if verbose:
        manifest_path = dataset_path / 'species_manifest.json'
        if manifest_path.exists():
            with open(manifest_path) as f:
                manifest = json.load(f)
            
            print("\n--- Species Details ---")
            for species_id, cls_data in manifest['classes'].items():
                print(f"  {cls_data['name']}: {cls_data['count']} images")
    
    print("\n" + "=" * 60)
    
    if validation['valid']:
        print("Dataset validation PASSED")
    else:
        print("Dataset validation FAILED")
    
    print("=" * 60 + "\n")
    
    return validation['valid']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Validate dataset integrity'
    )
    parser.add_argument(
        '--dataset',
        required=True,
        help='Path to dataset directory'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed information'
    )
    
    args = parser.parse_args()
    success = main(args.dataset, args.verbose)
    sys.exit(0 if success else 1)
