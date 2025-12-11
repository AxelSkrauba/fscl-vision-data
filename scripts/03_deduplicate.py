#!/usr/bin/env python3
"""
ETAPA 3: Deduplicacion de observaciones (mismo individuo fotografiado multiples veces).

Uso:
    python scripts/03_deduplicate.py --config config/paraense_fauna.yaml
    python scripts/03_deduplicate.py --config config/paraense_fauna.yaml --spatial-threshold 200
"""

import argparse
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.deduplicator import ObservationDeduplicator
from src.utils.logger import setup_logger


def main(
    config_path: str,
    spatial_threshold: int = None,
    temporal_threshold: int = None
):
    """
    Deduplica observaciones agrupando por individuo.
    
    Args:
        config_path: Ruta al archivo de configuracion YAML
        spatial_threshold: Override del umbral espacial en metros
        temporal_threshold: Override del umbral temporal en dias
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    data_dir = Path(config.get('data_dir', './data'))
    log_dir = data_dir / 'logs'
    cache_dir = data_dir / 'cache'
    
    logger = setup_logger(
        'deduplicate',
        log_dir=log_dir,
        level=config.get('logging', {}).get('level', 'INFO')
    )
    
    logger.info(f"Configuration loaded from {config_path}")
    
    obs_file = cache_dir / 'observations.json'
    if not obs_file.exists():
        logger.error(f"Observations file not found: {obs_file}")
        logger.error("Run 01_fetch_observations.py first")
        return
    
    with open(obs_file, 'r', encoding='utf-8') as f:
        observations = json.load(f)
    
    logger.info(f"Loaded {len(observations)} observations")
    
    dedup_config = config.get('deduplication', {})
    spatial_m = spatial_threshold or dedup_config.get('spatial_threshold_m', 100)
    temporal_d = temporal_threshold or dedup_config.get('temporal_threshold_days', 1)
    
    logger.info(f"Deduplication parameters: spatial={spatial_m}m, temporal={temporal_d}d")
    
    deduplicator = ObservationDeduplicator(
        spatial_threshold_m=spatial_m,
        temporal_threshold_days=temporal_d,
        logger=logger
    )
    
    result = deduplicator.deduplicate(observations)
    
    logger.info(deduplicator.get_dedup_summary(result))
    
    deduplicated_obs = [
        ind.best_observation for ind in result.unique_individuals
    ]
    
    output_file = cache_dir / 'observations_deduplicated.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(deduplicated_obs, f, indent=2, ensure_ascii=False, default=str)
    
    logger.info(f"Saved {len(deduplicated_obs)} deduplicated observations to {output_file}")
    
    stats_file = cache_dir / 'deduplication_stats.json'
    stats = {
        'total_original': result.total_original,
        'total_unique': result.total_unique,
        'duplicates_removed': result.duplicates_removed,
        'dedup_rate': result.dedup_rate,
        'by_species': result.by_species,
        'parameters': {
            'spatial_threshold_m': spatial_m,
            'temporal_threshold_days': temporal_d
        }
    }
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Saved deduplication stats to {stats_file}")
    
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Deduplicate observations (same individual)'
    )
    parser.add_argument(
        '--config',
        default='config/paraense_fauna.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--spatial-threshold',
        type=int,
        default=None,
        help='Spatial threshold in meters'
    )
    parser.add_argument(
        '--temporal-threshold',
        type=int,
        default=None,
        help='Temporal threshold in days'
    )
    
    args = parser.parse_args()
    main(args.config, args.spatial_threshold, args.temporal_threshold)
