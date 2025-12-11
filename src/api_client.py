"""
Cliente robusto para iNaturalist API v1 con rate-limiting y caching.
"""

import requests
import json
import time
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from .local_cache import LocalCache
from .utils.rate_limiter import RateLimiter


class iNaturalistAPIClient:
    """
    Cliente para iNaturalist API v1.
    
    Caracteristicas:
    - Rate limiting automatico (respeta limites de API)
    - Caching local de respuestas
    - Reintentos con backoff exponencial
    - Paginacion automatica
    """
    
    BASE_URL = "https://api.inaturalist.org/v1"
    
    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        max_retries: int = 3,
        requests_per_minute: int = 100,
        requests_per_day: int = 10000,
        cache_max_age_days: int = 30,
        timeout: int = 30,
        logger: Optional[logging.Logger] = None
    ):
        """
        Inicializa el cliente de iNaturalist API.
        
        Args:
            cache_dir: Directorio para cache local. Si None, usa ./cache
            max_retries: Numero maximo de reintentos por request
            requests_per_minute: Limite de requests por minuto
            requests_per_day: Limite de requests por dia
            cache_max_age_days: Dias maximos de validez del cache
            timeout: Timeout en segundos para requests
            logger: Logger opcional
        """
        self.logger = logger or logging.getLogger(__name__)
        self.max_retries = max_retries
        self.timeout = timeout
        
        cache_path = cache_dir or Path("./cache")
        self.cache = LocalCache(
            cache_dir=cache_path,
            max_age_days=cache_max_age_days,
            logger=self.logger
        )
        
        self.rate_limiter = RateLimiter(
            requests_per_minute=requests_per_minute,
            requests_per_day=requests_per_day,
            logger=self.logger
        )
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'fscl-vision-data/1.0 (research project)',
            'Accept': 'application/json'
        })
    
    def _make_request(
        self,
        endpoint: str,
        params: Dict[str, Any],
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Realiza un request a la API con retry y caching.
        
        Args:
            endpoint: Endpoint de la API (sin BASE_URL)
            params: Parametros del request
            use_cache: Si usar cache local
        
        Returns:
            Respuesta JSON de la API
        
        Raises:
            requests.exceptions.RequestException: Si falla despues de reintentos
        """
        cache_key = f"{endpoint}:{json.dumps(params, sort_keys=True)}"
        
        if use_cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                self.logger.debug(f"Cache hit for {endpoint}")
                return cached
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        for attempt in range(self.max_retries):
            self.rate_limiter.wait_if_needed()
            
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.timeout
                )
                
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    self.rate_limiter.handle_rate_limit_error(retry_after)
                    continue
                
                response.raise_for_status()
                data = response.json()
                
                if use_cache:
                    self.cache.set(cache_key, data)
                
                return data
            
            except requests.exceptions.Timeout:
                self.logger.warning(
                    f"Timeout on attempt {attempt + 1}/{self.max_retries}"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise
            
            except requests.exceptions.RequestException as e:
                self.logger.warning(
                    f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise
        
        raise requests.exceptions.RequestException(
            f"Failed after {self.max_retries} attempts"
        )
    
    def search_observations(
        self,
        place_id: Optional[int] = None,
        geo: Optional[str] = None,
        taxon_id: Optional[int] = None,
        taxon_name: Optional[str] = None,
        quality_grade: str = 'research',
        has_photos: bool = True,
        per_page: int = 200,
        max_results: Optional[int] = None,
        order_by: str = 'observed_on',
        order: str = 'desc',
        license: Optional[str] = None,
        photo_license: Optional[str] = None,
        observed_on_year: Optional[int] = None,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Busca observaciones con multiples filtros.
        
        Args:
            place_id: ID de lugar en iNaturalist
            geo: Bounding box "swlat,swlng,nelat,nelng"
            taxon_id: ID de taxon para filtrar
            taxon_name: Nombre de taxon (alternativa a taxon_id)
            quality_grade: 'research', 'needs_id', o 'casual'
            has_photos: Solo observaciones con fotos
            per_page: Resultados por pagina (max 200)
            max_results: Limite total de resultados
            order_by: Campo para ordenar ('observed_on', 'created_at', etc.)
            order: 'asc' o 'desc'
            license: Filtro de licencia (ej: 'cc-by')
            photo_license: Filtro de licencia de fotos
            observed_on_year: Filtrar por ano de observacion
            use_cache: Si usar cache local
        
        Returns:
            Lista de observaciones (dicts)
        """
        all_observations = []
        page = 1
        
        while True:
            params = {
                'quality_grade': quality_grade,
                'per_page': min(per_page, 200),
                'page': page,
                'order_by': order_by,
                'order': order
            }
            
            if place_id is not None:
                params['place_id'] = place_id
            if geo is not None:
                params['geo'] = geo
            if taxon_id is not None:
                params['taxon_id'] = taxon_id
            if taxon_name is not None:
                params['taxon_name'] = taxon_name
            if license is not None:
                params['license'] = license
            if photo_license is not None:
                params['photo_license'] = photo_license
            if observed_on_year is not None:
                params['year'] = observed_on_year
            
            try:
                response = self._make_request(
                    'observations',
                    params,
                    use_cache=use_cache
                )
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Failed to fetch observations: {e}")
                break
            
            results = response.get('results', [])
            total_results = response.get('total_results', 0)
            
            if not results:
                break
            
            all_observations.extend(results)
            
            self.logger.info(
                f"Page {page}: {len(results)} observations "
                f"(total fetched: {len(all_observations)}/{total_results})"
            )
            
            if max_results and len(all_observations) >= max_results:
                all_observations = all_observations[:max_results]
                break
            
            if len(all_observations) >= total_results:
                break
            
            if len(all_observations) >= 10000:
                self.logger.warning(
                    "Reached iNaturalist pagination limit (10000). "
                    "Consider using more specific filters."
                )
                break
            
            page += 1
        
        self.logger.info(f"Total observations fetched: {len(all_observations)}")
        return all_observations
    
    def get_observation(
        self,
        observation_id: int,
        use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene una observacion especifica por ID.
        
        Args:
            observation_id: ID de la observacion
            use_cache: Si usar cache local
        
        Returns:
            Observacion o None si no existe
        """
        try:
            response = self._make_request(
                f'observations/{observation_id}',
                {},
                use_cache=use_cache
            )
            results = response.get('results', [])
            return results[0] if results else None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get observation {observation_id}: {e}")
            return None
    
    def get_taxa(
        self,
        query: Optional[str] = None,
        taxon_id: Optional[int] = None,
        rank: Optional[str] = None,
        limit: int = 10,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Busca informacion taxonomica.
        
        Args:
            query: Texto de busqueda (nombre comun o cientifico)
            taxon_id: ID de taxon especifico
            rank: Filtrar por rango ('species', 'genus', etc.)
            limit: Numero maximo de resultados
            use_cache: Si usar cache local
        
        Returns:
            Lista de taxa
        """
        params = {'per_page': limit}
        
        if query is not None:
            params['q'] = query
        if taxon_id is not None:
            params['taxon_id'] = taxon_id
        if rank is not None:
            params['rank'] = rank
        
        try:
            response = self._make_request('taxa', params, use_cache=use_cache)
            return response.get('results', [])
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get taxa: {e}")
            return []
    
    def get_places(
        self,
        query: str,
        limit: int = 10,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Busca lugares por nombre.
        
        Args:
            query: Texto de busqueda
            limit: Numero maximo de resultados
            use_cache: Si usar cache local
        
        Returns:
            Lista de lugares
        """
        params = {'q': query, 'per_page': limit}
        
        try:
            response = self._make_request('places', params, use_cache=use_cache)
            return response.get('results', [])
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get places: {e}")
            return []
    
    def get_species_counts(
        self,
        place_id: Optional[int] = None,
        taxon_id: Optional[int] = None,
        quality_grade: str = 'research',
        limit: int = 500,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Obtiene conteo de especies para una region/taxon.
        
        Args:
            place_id: ID de lugar
            taxon_id: ID de taxon padre
            quality_grade: Filtro de calidad
            limit: Numero maximo de especies
            use_cache: Si usar cache local
        
        Returns:
            Lista de especies con conteos
        """
        params = {
            'quality_grade': quality_grade,
            'per_page': min(limit, 500)
        }
        
        if place_id is not None:
            params['place_id'] = place_id
        if taxon_id is not None:
            params['taxon_id'] = taxon_id
        
        try:
            response = self._make_request(
                'observations/species_counts',
                params,
                use_cache=use_cache
            )
            return response.get('results', [])
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get species counts: {e}")
            return []
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Retorna estadisticas del cache."""
        return self.cache.get_stats()
    
    def get_rate_limit_stats(self) -> Dict[str, Any]:
        """Retorna estadisticas del rate limiter."""
        return self.rate_limiter.get_stats()
    
    def clear_cache(self) -> int:
        """Limpia el cache local."""
        return self.cache.clear()
