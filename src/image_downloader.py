"""
Descargador de imagenes desde URLs de iNaturalist con reintentos y validacion.
"""

import requests
import logging
import threading
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

from .utils.image_utils import ImageUtils


@dataclass
class DownloadResult:
    """Resultado de una descarga de imagen."""
    success: bool
    url: str
    output_path: Optional[Path] = None
    error: Optional[str] = None
    file_size_bytes: int = 0
    download_time_ms: float = 0


@dataclass
class BatchDownloadStats:
    """Estadisticas de descarga por lotes."""
    total: int = 0
    downloaded: int = 0
    skipped: int = 0
    failed: int = 0
    total_bytes: int = 0
    total_time_seconds: float = 0
    errors: List[Dict[str, str]] = field(default_factory=list)


class ImageDownloader:
    """
    Descargador de imagenes con soporte para paralelismo y reintentos.
    
    Caracteristicas:
    - Descarga paralela con ThreadPoolExecutor
    - Reintentos con backoff exponencial
    - Validacion de imagenes descargadas
    - Skip automatico de archivos existentes
    - Guardado de metadata JSON junto a cada imagen
    """
    
    def __init__(
        self,
        max_workers: int = 4,
        timeout: int = 30,
        max_retries: int = 3,
        logger: Optional[logging.Logger] = None
    ):
        """
        Inicializa el descargador.
        
        Args:
            max_workers: Numero de threads para descarga paralela
            timeout: Timeout en segundos para cada descarga
            max_retries: Numero maximo de reintentos por imagen
            logger: Logger opcional
        """
        self.max_workers = max_workers
        self.timeout = timeout
        self.max_retries = max_retries
        self.logger = logger or logging.getLogger(__name__)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'fscl-vision-data/1.0 (research project)'
        })
        
        self.image_utils = ImageUtils(logger=self.logger)
        
        self._lock = threading.Lock()
        self._stats = BatchDownloadStats()
    
    def _get_best_photo_url(self, photo: Dict[str, Any]) -> str:
        """
        Obtiene la mejor URL disponible para una foto.
        
        iNaturalist proporciona diferentes tamaños. Priorizamos:
        1. original (si disponible)
        2. large
        3. medium
        4. url base
        
        Args:
            photo: Dict con datos de foto de iNaturalist
        
        Returns:
            URL de la mejor version disponible
        """
        url = photo.get('url', '')
        
        if not url:
            return ''
        
        if 'original' in url:
            return url
        
        size_replacements = [
            ('square', 'original'),
            ('small', 'original'),
            ('medium', 'large'),
            ('thumb', 'large'),
        ]
        
        for old, new in size_replacements:
            if old in url:
                large_url = url.replace(old, new)
                return large_url
        
        return url
    
    def download_image(
        self,
        url: str,
        output_path: Path,
        metadata: Optional[Dict[str, Any]] = None,
        skip_existing: bool = True
    ) -> DownloadResult:
        """
        Descarga una imagen individual.
        
        Args:
            url: URL de la imagen
            output_path: Ruta de destino
            metadata: Metadata opcional para guardar como JSON
            skip_existing: Si True, salta archivos que ya existen
        
        Returns:
            DownloadResult con estado de la descarga
        """
        output_path = Path(output_path)
        
        if skip_existing and output_path.exists():
            return DownloadResult(
                success=True,
                url=url,
                output_path=output_path,
                file_size_bytes=output_path.stat().st_size
            )
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        start_time = time.time()
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(
                    url,
                    timeout=self.timeout,
                    stream=True
                )
                response.raise_for_status()
                
                content_type = response.headers.get('content-type', '')
                if 'image' not in content_type.lower():
                    return DownloadResult(
                        success=False,
                        url=url,
                        error=f"Not an image: {content_type}"
                    )
                
                content = response.content
                
                with open(output_path, 'wb') as f:
                    f.write(content)
                
                validation = self.image_utils.validate_image(output_path)
                if not validation.get('valid', False):
                    output_path.unlink(missing_ok=True)
                    return DownloadResult(
                        success=False,
                        url=url,
                        error=f"Invalid image: {validation.get('error', 'unknown')}"
                    )
                
                if metadata:
                    metadata_path = output_path.with_suffix('.json')
                    with open(metadata_path, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)
                
                download_time = (time.time() - start_time) * 1000
                
                return DownloadResult(
                    success=True,
                    url=url,
                    output_path=output_path,
                    file_size_bytes=len(content),
                    download_time_ms=download_time
                )
            
            except requests.exceptions.Timeout:
                self.logger.warning(
                    f"Timeout downloading {url} (attempt {attempt + 1}/{self.max_retries})"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
            
            except requests.exceptions.RequestException as e:
                self.logger.warning(
                    f"Error downloading {url} (attempt {attempt + 1}/{self.max_retries}): {e}"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
            
            except Exception as e:
                return DownloadResult(
                    success=False,
                    url=url,
                    error=str(e)
                )
        
        return DownloadResult(
            success=False,
            url=url,
            error=f"Failed after {self.max_retries} attempts"
        )
    
    def download_observation_images(
        self,
        observation: Dict[str, Any],
        output_dir: Path,
        max_photos_per_obs: int = 1
    ) -> List[DownloadResult]:
        """
        Descarga imagenes de una observacion.
        
        Args:
            observation: Dict de observacion de iNaturalist
            output_dir: Directorio base de salida
            max_photos_per_obs: Maximo de fotos por observacion
        
        Returns:
            Lista de DownloadResult
        """
        results = []
        
        photos = observation.get('photos', [])
        if not photos:
            return results
        
        taxon = observation.get('taxon', {})
        species_id = taxon.get('id', 'unknown')
        obs_id = observation.get('id', 'unknown')
        
        species_dir = Path(output_dir) / str(species_id)
        
        for i, photo in enumerate(photos[:max_photos_per_obs]):
            photo_id = photo.get('id', i)
            url = self._get_best_photo_url(photo)
            
            if not url:
                continue
            
            filename = f"{obs_id}_{photo_id}.jpg"
            output_path = species_dir / filename
            
            metadata = self._extract_observation_metadata(observation, photo)
            
            result = self.download_image(url, output_path, metadata=metadata)
            results.append(result)
        
        return results
    
    def _extract_observation_metadata(
        self,
        observation: Dict[str, Any],
        photo: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extrae metadata relevante de una observacion."""
        taxon = observation.get('taxon', {})
        user = observation.get('user', {})
        
        return {
            'observation_id': observation.get('id'),
            'photo_id': photo.get('id'),
            'species': taxon.get('name'),
            'species_id': taxon.get('id'),
            'common_name': taxon.get('preferred_common_name'),
            'rank': taxon.get('rank'),
            'observed_on': observation.get('observed_on'),
            'time_observed_at': observation.get('time_observed_at'),
            'created_at': observation.get('created_at'),
            'location': {
                'latitude': observation.get('latitude'),
                'longitude': observation.get('longitude'),
                'accuracy_m': observation.get('positional_accuracy'),
                'place_guess': observation.get('place_guess')
            },
            'user': {
                'id': user.get('id'),
                'login': user.get('login')
            },
            'quality_grade': observation.get('quality_grade'),
            'license_code': photo.get('license_code'),
            'attribution': photo.get('attribution'),
            'url_original': photo.get('url'),
            'faves_count': observation.get('faves_count', 0),
            'comments_count': observation.get('comments_count', 0)
        }
    
    def download_batch(
        self,
        observations: List[Dict[str, Any]],
        output_dir: Path,
        max_photos_per_obs: int = 1,
        progress_callback: Optional[callable] = None
    ) -> BatchDownloadStats:
        """
        Descarga imagenes de multiples observaciones en paralelo.
        
        Args:
            observations: Lista de observaciones de iNaturalist
            output_dir: Directorio base de salida
            max_photos_per_obs: Maximo de fotos por observacion
            progress_callback: Callback opcional para reportar progreso
        
        Returns:
            BatchDownloadStats con estadisticas de la descarga
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self._stats = BatchDownloadStats()
        start_time = time.time()
        
        download_tasks = []
        for obs in observations:
            photos = obs.get('photos', [])
            if not photos:
                continue
            
            taxon = obs.get('taxon', {})
            species_id = taxon.get('id', 'unknown')
            obs_id = obs.get('id', 'unknown')
            
            for i, photo in enumerate(photos[:max_photos_per_obs]):
                photo_id = photo.get('id', i)
                url = self._get_best_photo_url(photo)
                
                if not url:
                    continue
                
                species_dir = output_dir / str(species_id)
                filename = f"{obs_id}_{photo_id}.jpg"
                output_path = species_dir / filename
                
                metadata = self._extract_observation_metadata(obs, photo)
                
                download_tasks.append({
                    'url': url,
                    'output_path': output_path,
                    'metadata': metadata
                })
        
        self._stats.total = len(download_tasks)
        self.logger.info(f"Starting download of {self._stats.total} images...")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(
                    self.download_image,
                    task['url'],
                    task['output_path'],
                    task['metadata']
                ): task
                for task in download_tasks
            }
            
            for i, future in enumerate(as_completed(futures)):
                task = futures[future]
                
                try:
                    result = future.result()
                    
                    with self._lock:
                        if result.success:
                            if result.file_size_bytes > 0:
                                self._stats.downloaded += 1
                                self._stats.total_bytes += result.file_size_bytes
                            else:
                                self._stats.skipped += 1
                        else:
                            self._stats.failed += 1
                            self._stats.errors.append({
                                'url': result.url,
                                'error': result.error
                            })
                
                except Exception as e:
                    with self._lock:
                        self._stats.failed += 1
                        self._stats.errors.append({
                            'url': task['url'],
                            'error': str(e)
                        })
                
                if progress_callback and (i + 1) % 10 == 0:
                    progress_callback(i + 1, self._stats.total)
                
                if (i + 1) % 100 == 0:
                    self.logger.info(
                        f"Progress: {i + 1}/{self._stats.total} "
                        f"(downloaded: {self._stats.downloaded}, "
                        f"skipped: {self._stats.skipped}, "
                        f"failed: {self._stats.failed})"
                    )
        
        self._stats.total_time_seconds = time.time() - start_time
        
        self.logger.info(
            f"Download complete: {self._stats.downloaded} downloaded, "
            f"{self._stats.skipped} skipped, {self._stats.failed} failed "
            f"in {self._stats.total_time_seconds:.1f}s "
            f"({self._stats.total_bytes / 1024 / 1024:.1f} MB)"
        )
        
        return self._stats
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadisticas de la ultima descarga."""
        return {
            'total': self._stats.total,
            'downloaded': self._stats.downloaded,
            'skipped': self._stats.skipped,
            'failed': self._stats.failed,
            'total_bytes': self._stats.total_bytes,
            'total_mb': self._stats.total_bytes / 1024 / 1024,
            'total_time_seconds': self._stats.total_time_seconds,
            'errors_count': len(self._stats.errors)
        }
