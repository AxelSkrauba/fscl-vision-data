#!/usr/bin/env python3
"""
ETAPA 4: Evaluacion de calidad de imagenes descargadas.

Uso:
    python scripts/04_assess_quality.py --config config/paraense_fauna.yaml
    python scripts/04_assess_quality.py --config config/paraense_fauna.yaml --min-quality 50
"""

import argparse
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.quality_assessor import ImageQualityAssessor
from src.utils.logger import setup_logger


def main(config_path: str, min_quality: float = None):
    """
    Evalua calidad de imagenes descargadas.
    
    Args:
        config_path: Ruta al archivo de configuracion YAML
        min_quality: Override del score minimo de calidad
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    data_dir = Path(config.get('data_dir', './data'))
    log_dir = data_dir / 'logs'
    cache_dir = data_dir / 'cache'
    raw_dir = data_dir / 'raw'
    
    logger = setup_logger(
        'assess_quality',
        log_dir=log_dir,
        level=config.get('logging', {}).get('level', 'INFO')
    )
    
    logger.info(f"Configuration loaded from {config_path}")
    
    dedup_file = cache_dir / 'observations_deduplicated.json'
    if not dedup_file.exists():
        logger.warning(f"Deduplicated file not found: {dedup_file}")
        logger.warning("Falling back to original observations")
        dedup_file = cache_dir / 'observations.json'
    
    if not dedup_file.exists():
        logger.error(f"Observations file not found")
        logger.error("Run previous pipeline stages first")
        return
    
    with open(dedup_file, 'r', encoding='utf-8') as f:
        observations = json.load(f)
    
    logger.info(f"Loaded {len(observations)} observations")
    
    quality_config = config.get('quality', {})
    assessor = ImageQualityAssessor(logger=logger)
    
    image_paths = []
    obs_by_path = {}
    
    for obs in observations:
        taxon = obs.get('taxon', {})
        species_id = taxon.get('id')
        obs_id = obs.get('id')
        photos = obs.get('photos', [])
        
        if not photos or not species_id:
            continue
        
        photo_id = photos[0].get('id', 0)
        filename = f"{obs_id}_{photo_id}.jpg"
        image_path = raw_dir / str(species_id) / filename
        
        if image_path.exists():
            image_paths.append(image_path)
            obs_by_path[str(image_path)] = obs
    
    logger.info(f"Found {len(image_paths)} images to assess")
    
    if not image_paths:
        logger.error("No images found. Run 02_download_images.py first")
        return
    
    def progress_callback(current, total):
        logger.info(f"Progress: {current}/{total} ({current/total*100:.1f}%)")
    
    logger.info("Assessing image quality...")
    scores = assessor.assess_batch(image_paths, progress_callback=progress_callback)
    
    for path_str, quality_scores in scores.items():
        if path_str in obs_by_path:
            obs_by_path[path_str]['quality_score'] = quality_scores.overall
            obs_by_path[path_str]['quality_details'] = quality_scores.to_dict()
    
    observations_with_quality = list(obs_by_path.values())
    
    min_score = min_quality or quality_config.get('quality_score_threshold', 40)
    
    filtered_obs = [
        obs for obs in observations_with_quality
        if obs.get('quality_score', 0) >= min_score
    ]
    
    logger.info(f"Quality filter: {len(filtered_obs)}/{len(observations_with_quality)} passed (min={min_score})")
    
    output_file = cache_dir / 'observations_quality.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(filtered_obs, f, indent=2, ensure_ascii=False, default=str)
    
    logger.info(f"Saved {len(filtered_obs)} quality-filtered observations to {output_file}")
    
    stats = assessor.get_statistics(scores)
    
    logger.info("=" * 50)
    logger.info("QUALITY ASSESSMENT SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Total images assessed: {len(scores)}")
    logger.info(f"Passed quality filter: {len(filtered_obs)}")
    logger.info(f"Rejected: {len(observations_with_quality) - len(filtered_obs)}")
    logger.info("")
    logger.info("Quality metrics (overall):")
    if 'overall' in stats:
        logger.info(f"  Mean: {stats['overall']['mean']:.1f}")
        logger.info(f"  Std: {stats['overall']['std']:.1f}")
        logger.info(f"  Min: {stats['overall']['min']:.1f}")
        logger.info(f"  Max: {stats['overall']['max']:.1f}")
    logger.info("=" * 50)
    
    stats_file = cache_dir / 'quality_stats.json'
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Saved quality stats to {stats_file}")
    
    return filtered_obs


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Assess quality of downloaded images'
    )
    parser.add_argument(
        '--config',
        default='config/paraense_fauna.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--min-quality',
        type=float,
        default=None,
        help='Minimum quality score (0-100)'
    )
    
    args = parser.parse_args()
    main(args.config, args.min_quality)
