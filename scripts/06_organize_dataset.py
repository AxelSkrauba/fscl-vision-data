#!/usr/bin/env python3
"""
ETAPA 6: Organizacion del dataset final para FSCL-Vision.

Uso:
    python scripts/06_organize_dataset.py --config config/paraense_fauna.yaml
    python scripts/06_organize_dataset.py --config config/paraense_fauna.yaml --name my_dataset
"""

import argparse
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.dataset_organizer import DatasetOrganizer
from src.utils.logger import setup_logger


def main(
    config_path: str,
    dataset_name: str = None,
    n_classes: int = None
):
    """
    Organiza el dataset final.
    
    Args:
        config_path: Ruta al archivo de configuracion YAML
        dataset_name: Override del nombre del dataset
        n_classes: Limitar a N clases
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    data_dir = Path(config.get('data_dir', './data'))
    log_dir = data_dir / 'logs'
    cache_dir = data_dir / 'cache'
    raw_dir = data_dir / 'raw'
    output_dir = Path(config.get('output_dir', data_dir / 'final_datasets'))
    
    logger = setup_logger(
        'organize_dataset',
        log_dir=log_dir,
        level=config.get('logging', {}).get('level', 'INFO')
    )
    
    logger.info(f"Configuration loaded from {config_path}")
    
    selected_file = cache_dir / 'observations_selected.json'
    if not selected_file.exists():
        logger.warning(f"Selected file not found: {selected_file}")
        logger.warning("Falling back to quality-filtered observations")
        selected_file = cache_dir / 'observations_quality.json'
    
    if not selected_file.exists():
        selected_file = cache_dir / 'observations_deduplicated.json'
    
    if not selected_file.exists():
        selected_file = cache_dir / 'observations.json'
    
    if not selected_file.exists():
        logger.error("No observations file found")
        logger.error("Run previous pipeline stages first")
        return
    
    with open(selected_file, 'r', encoding='utf-8') as f:
        observations = json.load(f)
    
    logger.info(f"Loaded {len(observations)} observations from {selected_file}")
    
    # Usar dataset.name si está disponible, sino region_name como fallback
    dataset_config = config.get('dataset', {})
    geography_config = config.get('geography', {})
    
    name = dataset_name or dataset_config.get('name') or \
           f"{geography_config.get('region_name', 'wildlife').lower().replace(' ', '_')}_dataset"
    
    # Usar dataset.description si está disponible
    description = dataset_config.get('description') or (
        f"Wildlife image dataset from {geography_config.get('region_name', 'unknown region')}. "
        f"Prepared for few-shot classification with FSCL-Vision framework."
    )
    
    organizer = DatasetOrganizer(
        source_dir=raw_dir,
        logger=logger
    )
    
    logger.info(f"Organizing dataset: {name}")
    logger.info(f"Output directory: {output_dir}")
    
    dataset_path = organizer.organize_dataset(
        observations=observations,
        output_dir=output_dir,
        dataset_name=name,
        description=description,
        copy_images=True,
        n_classes=n_classes,
        min_images_per_class=config.get('sampling', {}).get('min_samples_per_species', 10),
        config=config
    )
    
    logger.info("Validating dataset...")
    validation = organizer.validate_dataset(dataset_path)
    
    logger.info("=" * 50)
    logger.info("DATASET ORGANIZATION COMPLETE")
    logger.info("=" * 50)
    logger.info(f"Dataset path: {dataset_path}")
    logger.info(f"Total species: {validation['stats'].get('total_species', 0)}")
    logger.info(f"Total images: {validation['stats'].get('total_images_manifest', 0)}")
    logger.info(f"Validation: {'PASSED' if validation['valid'] else 'FAILED'}")
    
    if validation['warnings']:
        logger.warning("Warnings:")
        for w in validation['warnings']:
            logger.warning(f"  {w}")
    
    if validation['errors']:
        logger.error("Errors:")
        for e in validation['errors']:
            logger.error(f"  {e}")
    
    logger.info("")
    logger.info("Generated files:")
    logger.info(f"  {dataset_path / 'species_manifest.json'}")
    logger.info(f"  {dataset_path / 'dataset_metadata.yaml'}")
    logger.info(f"  {dataset_path / 'statistics.json'}")
    logger.info(f"  {dataset_path / 'README.md'}")
    logger.info(f"  {dataset_path / 'images/'}")
    logger.info("=" * 50)
    
    return dataset_path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Organize final dataset for FSCL-Vision'
    )
    parser.add_argument(
        '--config',
        default='config/paraense_fauna.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--name',
        default=None,
        help='Dataset name'
    )
    parser.add_argument(
        '--n-classes',
        type=int,
        default=None,
        help='Limit to N classes with most images'
    )
    
    args = parser.parse_args()
    main(args.config, args.name, args.n_classes)
