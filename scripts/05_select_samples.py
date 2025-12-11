#!/usr/bin/env python3
"""
ETAPA 5: Seleccion de muestras representativas.

Uso:
    python scripts/05_select_samples.py --config config/paraense_fauna.yaml
    python scripts/05_select_samples.py --config config/paraense_fauna.yaml --samples-per-species 30
"""

import argparse
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.sample_selector import RepresentativeSampleSelector
from src.utils.logger import setup_logger


def main(
    config_path: str,
    samples_per_species: int = None,
    method: str = None
):
    """
    Selecciona muestras representativas del dataset.
    
    Args:
        config_path: Ruta al archivo de configuracion YAML
        samples_per_species: Override del numero de muestras por especie
        method: Override del metodo de seleccion
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    data_dir = Path(config.get('data_dir', './data'))
    log_dir = data_dir / 'logs'
    cache_dir = data_dir / 'cache'
    
    logger = setup_logger(
        'select_samples',
        log_dir=log_dir,
        level=config.get('logging', {}).get('level', 'INFO')
    )
    
    logger.info(f"Configuration loaded from {config_path}")
    
    quality_file = cache_dir / 'observations_quality.json'
    if not quality_file.exists():
        logger.warning(f"Quality file not found: {quality_file}")
        logger.warning("Falling back to deduplicated observations")
        quality_file = cache_dir / 'observations_deduplicated.json'
    
    if not quality_file.exists():
        quality_file = cache_dir / 'observations.json'
    
    if not quality_file.exists():
        logger.error("No observations file found")
        logger.error("Run previous pipeline stages first")
        return
    
    with open(quality_file, 'r', encoding='utf-8') as f:
        observations = json.load(f)
    
    logger.info(f"Loaded {len(observations)} observations from {quality_file}")
    
    sampling_config = config.get('sampling', {})
    n_samples = samples_per_species or sampling_config.get('samples_per_species', 50)
    selection_method = method or sampling_config.get('method', 'clustering')
    min_samples = sampling_config.get('min_samples_per_species', 10)
    
    logger.info(f"Selection parameters: method={selection_method}, n={n_samples}, min={min_samples}")
    
    selector = RepresentativeSampleSelector(
        method=selection_method,
        random_state=42,
        logger=logger
    )
    
    result = selector.select_samples(
        observations=observations,
        n_samples_per_species=n_samples,
        min_samples_per_species=min_samples
    )
    
    output_file = cache_dir / 'observations_selected.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result.selected, f, indent=2, ensure_ascii=False, default=str)
    
    logger.info(f"Saved {len(result.selected)} selected observations to {output_file}")
    
    logger.info("=" * 50)
    logger.info("SAMPLE SELECTION SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Method: {result.selection_method}")
    logger.info(f"Total candidates: {result.total_candidates}")
    logger.info(f"Total selected: {result.total_selected}")
    logger.info(f"Species included: {len(result.by_species)}")
    logger.info("")
    logger.info("By species:")
    for species_id, count in sorted(result.by_species.items(), key=lambda x: -x[1]):
        obs = next((o for o in result.selected if o.get('taxon', {}).get('id') == species_id), None)
        species_name = obs.get('taxon', {}).get('name', 'Unknown') if obs else 'Unknown'
        logger.info(f"  {species_name}: {count}")
    logger.info("=" * 50)
    
    stats_file = cache_dir / 'selection_stats.json'
    stats = {
        'method': result.selection_method,
        'total_candidates': result.total_candidates,
        'total_selected': result.total_selected,
        'by_species': {str(k): v for k, v in result.by_species.items()},
        'parameters': {
            'samples_per_species': n_samples,
            'min_samples_per_species': min_samples
        }
    }
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Saved selection stats to {stats_file}")
    
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Select representative samples'
    )
    parser.add_argument(
        '--config',
        default='config/paraense_fauna.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--samples-per-species',
        type=int,
        default=None,
        help='Number of samples per species'
    )
    parser.add_argument(
        '--method',
        choices=['clustering', 'stratified', 'quality', 'random'],
        default=None,
        help='Selection method'
    )
    
    args = parser.parse_args()
    main(args.config, args.samples_per_species, args.method)
