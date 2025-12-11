#!/usr/bin/env python3
"""
Ejecuta el pipeline completo de preparacion de datos.

Uso:
    python scripts/helpers/run_full_pipeline.py --config config/paraense_fauna.yaml
    python scripts/helpers/run_full_pipeline.py --config config/paraense_fauna.yaml --skip-download
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.logger import setup_logger


def main(
    config_path: str,
    skip_fetch: bool = False,
    skip_download: bool = False,
    skip_dedup: bool = False,
    skip_quality: bool = False,
    skip_select: bool = False
):
    """
    Ejecuta el pipeline completo.
    
    Args:
        config_path: Ruta al archivo de configuracion
        skip_*: Flags para saltar etapas
    """
    logger = setup_logger('full_pipeline')
    
    start_time = time.time()
    
    logger.info("=" * 60)
    logger.info("FSCL-VISION DATA PIPELINE")
    logger.info("=" * 60)
    logger.info(f"Configuration: {config_path}")
    logger.info("")
    
    scripts_dir = Path(__file__).parent.parent
    
    stages = [
        ('01_fetch_observations', skip_fetch, 'Fetching observations from iNaturalist'),
        ('02_download_images', skip_download, 'Downloading images'),
        ('03_deduplicate', skip_dedup, 'Deduplicating observations'),
        ('04_assess_quality', skip_quality, 'Assessing image quality'),
        ('05_select_samples', skip_select, 'Selecting representative samples'),
        ('06_organize_dataset', False, 'Organizing final dataset'),
    ]
    
    for script_name, skip, description in stages:
        if skip:
            logger.info(f"[SKIP] {description}")
            continue
        
        logger.info(f"\n{'='*60}")
        logger.info(f"[STAGE] {description}")
        logger.info(f"{'='*60}\n")
        
        script_path = scripts_dir / f"{script_name}.py"
        
        if not script_path.exists():
            logger.error(f"Script not found: {script_path}")
            continue
        
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(script_name, script_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            module.main(config_path)
            
            logger.info(f"[OK] {description} completed")
        
        except Exception as e:
            logger.error(f"[FAIL] {description} failed: {e}")
            logger.error("Pipeline stopped due to error")
            return False
    
    elapsed = time.time() - start_time
    
    logger.info("\n" + "=" * 60)
    logger.info("PIPELINE COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Total time: {elapsed/60:.1f} minutes")
    logger.info("=" * 60)
    
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Run full data preparation pipeline'
    )
    parser.add_argument(
        '--config',
        default='config/paraense_fauna.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--skip-fetch',
        action='store_true',
        help='Skip fetching observations'
    )
    parser.add_argument(
        '--skip-download',
        action='store_true',
        help='Skip downloading images'
    )
    parser.add_argument(
        '--skip-dedup',
        action='store_true',
        help='Skip deduplication'
    )
    parser.add_argument(
        '--skip-quality',
        action='store_true',
        help='Skip quality assessment'
    )
    parser.add_argument(
        '--skip-select',
        action='store_true',
        help='Skip sample selection'
    )
    
    args = parser.parse_args()
    
    success = main(
        args.config,
        skip_fetch=args.skip_fetch,
        skip_download=args.skip_download,
        skip_dedup=args.skip_dedup,
        skip_quality=args.skip_quality,
        skip_select=args.skip_select
    )
    
    sys.exit(0 if success else 1)
