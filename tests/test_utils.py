"""
Tests para modulos de utilidades.
"""

import pytest
import tempfile
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.rate_limiter import RateLimiter
from src.utils.geo_utils import GeoUtils, BoundingBox
from src.local_cache import LocalCache


class TestRateLimiter:
    """Tests para RateLimiter."""
    
    def test_init(self):
        """Test inicializacion."""
        limiter = RateLimiter(requests_per_minute=10, requests_per_day=100)
        assert limiter.rpm == 10
        assert limiter.rpd == 100
    
    def test_get_stats(self):
        """Test estadisticas."""
        limiter = RateLimiter(requests_per_minute=10, requests_per_day=100)
        stats = limiter.get_stats()
        
        assert 'requests_last_minute' in stats
        assert 'requests_today' in stats
        assert stats['rpm_limit'] == 10
        assert stats['rpd_limit'] == 100
    
    def test_wait_if_needed_no_wait(self):
        """Test que no espera si no hay limite alcanzado."""
        limiter = RateLimiter(requests_per_minute=100, requests_per_day=1000)
        
        import time
        start = time.time()
        limiter.wait_if_needed()
        elapsed = time.time() - start
        
        assert elapsed < 1.0


class TestGeoUtils:
    """Tests para GeoUtils."""
    
    def test_haversine_distance(self):
        """Test calculo de distancia."""
        lat1, lon1 = -25.5, -54.5
        lat2, lon2 = -25.6, -54.6
        
        distance = GeoUtils.haversine_distance(lat1, lon1, lat2, lon2, unit='km')
        
        assert 10 < distance < 20
    
    def test_haversine_distance_same_point(self):
        """Test distancia al mismo punto."""
        lat, lon = -25.5, -54.5
        
        distance = GeoUtils.haversine_distance(lat, lon, lat, lon)
        
        assert distance == 0
    
    def test_validate_coordinates_valid(self):
        """Test coordenadas validas."""
        assert GeoUtils.validate_coordinates(-25.5, -54.5) is True
        assert GeoUtils.validate_coordinates(0, 0) is True
        assert GeoUtils.validate_coordinates(90, 180) is True
        assert GeoUtils.validate_coordinates(-90, -180) is True
    
    def test_validate_coordinates_invalid(self):
        """Test coordenadas invalidas."""
        assert GeoUtils.validate_coordinates(None, -54.5) is False
        assert GeoUtils.validate_coordinates(-25.5, None) is False
        assert GeoUtils.validate_coordinates(91, 0) is False
        assert GeoUtils.validate_coordinates(0, 181) is False
    
    def test_degrees_to_meters(self):
        """Test conversion grados a metros."""
        meters = GeoUtils.degrees_to_meters(1, latitude=0)
        
        assert 100000 < meters < 120000
    
    def test_create_bounding_box(self):
        """Test creacion de bounding box."""
        bbox = GeoUtils.create_bounding_box_around_point(-25.5, -54.5, radius_km=10)
        
        assert bbox.north > -25.5
        assert bbox.south < -25.5
        assert bbox.east > -54.5
        assert bbox.west < -54.5


class TestBoundingBox:
    """Tests para BoundingBox."""
    
    def test_init(self):
        """Test inicializacion."""
        bbox = BoundingBox(north=-25.0, south=-26.0, east=-54.0, west=-55.0)
        
        assert bbox.north == -25.0
        assert bbox.south == -26.0
    
    def test_contains_inside(self):
        """Test punto dentro del bbox."""
        bbox = BoundingBox(north=-25.0, south=-26.0, east=-54.0, west=-55.0)
        
        assert bbox.contains(-25.5, -54.5) is True
    
    def test_contains_outside(self):
        """Test punto fuera del bbox."""
        bbox = BoundingBox(north=-25.0, south=-26.0, east=-54.0, west=-55.0)
        
        assert bbox.contains(-24.0, -54.5) is False
        assert bbox.contains(-25.5, -53.0) is False
    
    def test_to_inaturalist_format(self):
        """Test formato iNaturalist."""
        bbox = BoundingBox(north=-25.0, south=-26.0, east=-54.0, west=-55.0)
        
        result = bbox.to_inaturalist_format()
        
        assert result == "-26.0,-55.0,-25.0,-54.0"
    
    def test_invalid_bounds(self):
        """Test bounds invalidos."""
        with pytest.raises(ValueError):
            BoundingBox(north=-26.0, south=-25.0, east=-54.0, west=-55.0)


class TestLocalCache:
    """Tests para LocalCache."""
    
    def test_set_and_get(self):
        """Test guardar y obtener."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = LocalCache(Path(tmpdir), max_age_days=30)
            
            cache.set("test_key", {"data": "value"})
            result = cache.get("test_key")
            
            assert result == {"data": "value"}
    
    def test_get_nonexistent(self):
        """Test obtener key inexistente."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = LocalCache(Path(tmpdir))
            
            result = cache.get("nonexistent")
            
            assert result is None
    
    def test_exists(self):
        """Test verificar existencia."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = LocalCache(Path(tmpdir))
            
            cache.set("test_key", {"data": "value"})
            
            assert cache.exists("test_key") is True
            assert cache.exists("nonexistent") is False
    
    def test_delete(self):
        """Test eliminar entrada."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = LocalCache(Path(tmpdir))
            
            cache.set("test_key", {"data": "value"})
            cache.delete("test_key")
            
            assert cache.exists("test_key") is False
    
    def test_clear(self):
        """Test limpiar cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = LocalCache(Path(tmpdir))
            
            cache.set("key1", {"data": 1})
            cache.set("key2", {"data": 2})
            
            count = cache.clear()
            
            assert count == 2
            assert cache.exists("key1") is False
            assert cache.exists("key2") is False
    
    def test_stats(self):
        """Test estadisticas."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = LocalCache(Path(tmpdir))
            
            cache.set("key1", {"data": 1})
            cache.get("key1")
            cache.get("nonexistent")
            
            stats = cache.get_stats()
            
            assert stats['entries'] == 1
            assert stats['hits'] == 1
            assert stats['misses'] == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
