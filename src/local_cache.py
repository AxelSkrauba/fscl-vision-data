"""
Cache local en disco para respuestas de API.
"""

import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any


class LocalCache:
    """
    Cache simple en disco (JSON) con control de antiguedad.
    
    Almacena respuestas de API en archivos JSON individuales,
    usando hash MD5 de la key como nombre de archivo.
    """
    
    def __init__(
        self,
        cache_dir: Path,
        max_age_days: int = 30,
        logger: Optional[logging.Logger] = None
    ):
        """
        Inicializa el cache local.
        
        Args:
            cache_dir: Directorio para almacenar archivos de cache
            max_age_days: Dias maximos antes de considerar entrada expirada
            logger: Logger opcional
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_age_days = max_age_days
        self.logger = logger or logging.getLogger(__name__)
        
        self._hits = 0
        self._misses = 0
    
    def _get_cache_path(self, key: str) -> Path:
        """Genera path consistente para una key usando hash MD5."""
        hash_key = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{hash_key}.json"
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene valor del cache si existe y no ha expirado.
        
        Args:
            key: Clave de cache (tipicamente endpoint + params)
        
        Returns:
            Datos cacheados o None si no existe/expiro
        """
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            self._misses += 1
            return None
        
        try:
            mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
            age_days = (datetime.now() - mtime).days
            
            if age_days > self.max_age_days:
                self.logger.debug(
                    f"Cache expired for key (age: {age_days}d > {self.max_age_days}d)"
                )
                cache_path.unlink()
                self._misses += 1
                return None
            
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._hits += 1
            return data
        
        except json.JSONDecodeError as e:
            self.logger.warning(f"Corrupted cache file, removing: {e}")
            cache_path.unlink(missing_ok=True)
            self._misses += 1
            return None
        
        except Exception as e:
            self.logger.warning(f"Error reading cache: {e}")
            self._misses += 1
            return None
    
    def set(self, key: str, value: Dict[str, Any]) -> bool:
        """
        Guarda valor en cache.
        
        Args:
            key: Clave de cache
            value: Datos a cachear (debe ser serializable a JSON)
        
        Returns:
            True si se guardo exitosamente
        """
        cache_path = self._get_cache_path(key)
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(value, f, ensure_ascii=False, default=str)
            return True
        
        except Exception as e:
            self.logger.error(f"Error writing cache: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        Verifica si una key existe en cache y no ha expirado.
        
        Args:
            key: Clave a verificar
        
        Returns:
            True si existe y es valida
        """
        return self.get(key) is not None
    
    def delete(self, key: str) -> bool:
        """
        Elimina una entrada del cache.
        
        Args:
            key: Clave a eliminar
        
        Returns:
            True si se elimino (o no existia)
        """
        cache_path = self._get_cache_path(key)
        try:
            cache_path.unlink(missing_ok=True)
            return True
        except Exception as e:
            self.logger.error(f"Error deleting cache entry: {e}")
            return False
    
    def clear(self) -> int:
        """
        Elimina todas las entradas del cache.
        
        Returns:
            Numero de archivos eliminados
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                count += 1
            except Exception as e:
                self.logger.warning(f"Error deleting {cache_file}: {e}")
        
        self.logger.info(f"Cache cleared: {count} files removed")
        self._hits = 0
        self._misses = 0
        return count
    
    def cleanup_expired(self) -> int:
        """
        Elimina entradas expiradas del cache.
        
        Returns:
            Numero de archivos eliminados
        """
        count = 0
        now = datetime.now()
        
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
                age_days = (now - mtime).days
                
                if age_days > self.max_age_days:
                    cache_file.unlink()
                    count += 1
            except Exception as e:
                self.logger.warning(f"Error checking {cache_file}: {e}")
        
        if count > 0:
            self.logger.info(f"Cleanup: {count} expired files removed")
        
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estadisticas del cache.
        
        Returns:
            Dict con estadisticas
        """
        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        hit_rate = 0.0
        total_requests = self._hits + self._misses
        if total_requests > 0:
            hit_rate = self._hits / total_requests
        
        return {
            'entries': len(cache_files),
            'total_size_mb': total_size / (1024 * 1024),
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate': hit_rate,
            'cache_dir': str(self.cache_dir),
            'max_age_days': self.max_age_days
        }
