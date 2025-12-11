#!/usr/bin/env python3
"""
ETAPA 2: Descarga de imagenes desde URLs de iNaturalist.

Uso:
    python scripts/02_download_images.py --config config/paraense_fauna.yaml
    python scripts/02_download_images.py --config config/paraense_fauna.yaml --workers 8
"""

import argparse
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.image_downloader import ImageDownloader
from src.utils.logger import setup_logger


def main(config_path: str, workers: int = None):
    """
    Descarga imagenes de las observaciones obtenidas.
    
    Args:
        config_path: Ruta al archivo de configuracion YAML
        workers: Override del numero de workers paralelos
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    data_dir = Path(config.get('data_dir', './data'))
    log_dir = data_dir / 'logs'
    cache_dir = data_dir / 'cache'
    raw_dir = data_dir / 'raw'
    
    logger = setup_logger(
        'download_images',
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
    
    logger.info(f"Loaded {len(observations)} observations from {obs_file}")
    
    api_config = config.get('api', {})
    n_workers = workers or api_config.get('download_workers', 4)
    
    downloader = ImageDownloader(
        max_workers=n_workers,
        timeout=api_config.get('timeout_seconds', 30),
        max_retries=api_config.get('max_retries', 3),
        logger=logger
    )
    
    def progress_callback(current, total):
        logger.info(f"Progress: {current}/{total} ({current/total*100:.1f}%)")
    
    logger.info(f"Starting download with {n_workers} workers...")
    
    stats = downloader.download_batch(
        observations=observations,
        output_dir=raw_dir,
        max_photos_per_obs=1,
        progress_callback=progress_callback
    )
    
    logger.info("=" * 50)
    logger.info("DOWNLOAD SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Total images: {stats.total}")
    logger.info(f"Downloaded: {stats.downloaded}")
    logger.info(f"Skipped (existing): {stats.skipped}")
    logger.info(f"Failed: {stats.failed}")
    logger.info(f"Total size: {stats.total_bytes / 1024 / 1024:.1f} MB")
    logger.info(f"Time: {stats.total_time_seconds:.1f} seconds")
    
    if stats.errors:
        logger.warning(f"Errors ({len(stats.errors)}):")
        for err in stats.errors[:10]:
            logger.warning(f"  {err['url']}: {err['error']}")
        if len(stats.errors) > 10:
            logger.warning(f"  ... and {len(stats.errors) - 10} more")
    
    logger.info("=" * 50)
    
    return stats


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Download images from iNaturalist observations'
    )
    parser.add_argument(
        '--config',
        default='config/paraense_fauna.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=None,
        help='Number of parallel download workers'
    )
    
    args = parser.parse_args()
    main(args.config, args.workers)
