#!/usr/bin/env python3
"""
ETAPA 1: Obtencion de observaciones desde iNaturalist API.

Uso:
    python scripts/01_fetch_observations.py --config config/paraense_fauna.yaml
    python scripts/01_fetch_observations.py --config config/paraense_fauna.yaml --max-per-taxon 100
"""

import argparse
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api_client import iNaturalistAPIClient
from src.utils.logger import setup_logger


def main(config_path: str, max_per_taxon: int = None):
    """
    Obtiene observaciones desde iNaturalist segun configuracion.
    
    Args:
        config_path: Ruta al archivo de configuracion YAML
        max_per_taxon: Override del maximo de observaciones por taxon
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    data_dir = Path(config.get('data_dir', './data'))
    log_dir = data_dir / 'logs'
    cache_dir = data_dir / 'cache'
    
    logger = setup_logger(
        'fetch_observations',
        log_dir=log_dir,
        level=config.get('logging', {}).get('level', 'INFO')
    )
    
    logger.info(f"Configuration loaded from {config_path}")
    logger.info(f"Region: {config.get('geography', {}).get('region_name', 'Unknown')}")
    
    api_config = config.get('api', {})
    client = iNaturalistAPIClient(
        cache_dir=cache_dir,
        requests_per_minute=api_config.get('rate_limit_requests_per_minute', 100),
        requests_per_day=api_config.get('rate_limit_requests_per_day', 10000),
        max_retries=api_config.get('max_retries', 3),
        timeout=api_config.get('timeout_seconds', 30)
    )
    
    all_observations = []
    geography = config.get('geography', {})
    place_id = geography.get('place_id')
    
    bounds = geography.get('bounds')
    geo_bbox = None
    if bounds and not place_id:
        geo_bbox = f"{bounds['south']},{bounds['west']},{bounds['north']},{bounds['east']}"
    
    taxa = config.get('fauna', {}).get('taxa', [])
    
    if not taxa:
        logger.warning("No taxa defined in configuration. Fetching all fauna.")
        taxa = [{'name': 'All Animalia', 'taxon_id': 1}]
    
    for taxon_filter in taxa:
        taxon_name = taxon_filter.get('name', 'Unknown')
        taxon_id = taxon_filter.get('taxon_id')
        max_obs = max_per_taxon or taxon_filter.get('max_observations', 500)
        
        logger.info(f"Fetching observations for: {taxon_name} (taxon_id={taxon_id}, max={max_obs})")
        
        try:
            obs = client.search_observations(
                place_id=place_id,
                geo=geo_bbox,
                taxon_id=taxon_id,
                quality_grade='research',
                has_photos=True,
                max_results=max_obs,
                per_page=200
            )
            
            logger.info(f"  -> Found {len(obs)} observations for {taxon_name}")
            all_observations.extend(obs)
        
        except Exception as e:
            logger.error(f"  -> Error fetching {taxon_name}: {e}")
            continue
    
    output_file = cache_dir / 'observations.json'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_observations, f, indent=2, ensure_ascii=False, default=str)
    
    logger.info(f"Saved {len(all_observations)} observations to {output_file}")
    
    by_species = {}
    for obs in all_observations:
        taxon = obs.get('taxon', {})
        species = taxon.get('name', 'Unknown')
        by_species[species] = by_species.get(species, 0) + 1
    
    logger.info("=" * 50)
    logger.info("SUMMARY: Observations by species")
    logger.info("=" * 50)
    for species, count in sorted(by_species.items(), key=lambda x: -x[1]):
        logger.info(f"  {species}: {count}")
    logger.info("=" * 50)
    logger.info(f"Total: {len(all_observations)} observations, {len(by_species)} species")
    
    cache_stats = client.get_cache_stats()
    logger.info(f"Cache stats: {cache_stats['hits']} hits, {cache_stats['misses']} misses")
    
    return all_observations


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Fetch observations from iNaturalist API'
    )
    parser.add_argument(
        '--config',
        default='config/paraense_fauna.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--max-per-taxon',
        type=int,
        default=None,
        help='Override max observations per taxon'
    )
    
    args = parser.parse_args()
    main(args.config, args.max_per_taxon)
