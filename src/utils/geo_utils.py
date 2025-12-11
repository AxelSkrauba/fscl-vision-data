"""
Utilidades geograficas para filtrado y validacion de coordenadas.
"""

import math
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class BoundingBox:
    """Representa un bounding box geografico."""
    north: float
    south: float
    east: float
    west: float
    
    def __post_init__(self):
        if self.north < self.south:
            raise ValueError(
                f"North ({self.north}) must be >= South ({self.south})"
            )
        if self.east < self.west:
            pass
    
    def contains(self, lat: float, lon: float) -> bool:
        """Verifica si un punto esta dentro del bounding box."""
        lat_ok = self.south <= lat <= self.north
        
        if self.west <= self.east:
            lon_ok = self.west <= lon <= self.east
        else:
            lon_ok = lon >= self.west or lon <= self.east
        
        return lat_ok and lon_ok
    
    def to_inaturalist_format(self) -> str:
        """Convierte a formato de iNaturalist API (swlat,swlng,nelat,nelng)."""
        return f"{self.south},{self.west},{self.north},{self.east}"
    
    @classmethod
    def from_dict(cls, d: Dict[str, float]) -> 'BoundingBox':
        """Crea BoundingBox desde diccionario."""
        return cls(
            north=d['north'],
            south=d['south'],
            east=d['east'],
            west=d['west']
        )


class GeoUtils:
    """Utilidades para calculos geograficos."""
    
    EARTH_RADIUS_KM = 6371.0
    EARTH_RADIUS_M = 6371000.0
    
    @staticmethod
    def haversine_distance(
        lat1: float, lon1: float,
        lat2: float, lon2: float,
        unit: str = 'km'
    ) -> float:
        """
        Calcula la distancia entre dos puntos usando la formula de Haversine.
        
        Args:
            lat1, lon1: Coordenadas del primer punto (grados)
            lat2, lon2: Coordenadas del segundo punto (grados)
            unit: Unidad de retorno ('km' o 'm')
        
        Returns:
            Distancia en la unidad especificada
        """
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (
            math.sin(delta_lat / 2) ** 2 +
            math.cos(lat1_rad) * math.cos(lat2_rad) *
            math.sin(delta_lon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        if unit == 'm':
            return GeoUtils.EARTH_RADIUS_M * c
        return GeoUtils.EARTH_RADIUS_KM * c
    
    @staticmethod
    def validate_coordinates(
        lat: Optional[float],
        lon: Optional[float]
    ) -> bool:
        """
        Valida que las coordenadas sean validas.
        
        Args:
            lat: Latitud
            lon: Longitud
        
        Returns:
            True si las coordenadas son validas
        """
        if lat is None or lon is None:
            return False
        
        try:
            lat = float(lat)
            lon = float(lon)
        except (TypeError, ValueError):
            return False
        
        return -90 <= lat <= 90 and -180 <= lon <= 180
    
    @staticmethod
    def degrees_to_meters(degrees: float, latitude: float = 0) -> float:
        """
        Convierte grados a metros aproximados.
        
        Args:
            degrees: Cantidad de grados
            latitude: Latitud de referencia (afecta conversion de longitud)
        
        Returns:
            Distancia aproximada en metros
        """
        meters_per_degree_lat = 111320
        meters_per_degree_lon = 111320 * math.cos(math.radians(latitude))
        
        return degrees * (meters_per_degree_lat + meters_per_degree_lon) / 2
    
    @staticmethod
    def meters_to_degrees(meters: float, latitude: float = 0) -> float:
        """
        Convierte metros a grados aproximados.
        
        Args:
            meters: Distancia en metros
            latitude: Latitud de referencia
        
        Returns:
            Distancia aproximada en grados
        """
        meters_per_degree_lat = 111320
        meters_per_degree_lon = 111320 * math.cos(math.radians(latitude))
        
        avg_meters_per_degree = (meters_per_degree_lat + meters_per_degree_lon) / 2
        return meters / avg_meters_per_degree
    
    @staticmethod
    def create_bounding_box_around_point(
        lat: float,
        lon: float,
        radius_km: float
    ) -> BoundingBox:
        """
        Crea un bounding box cuadrado alrededor de un punto.
        
        Args:
            lat: Latitud del centro
            lon: Longitud del centro
            radius_km: Radio en kilometros
        
        Returns:
            BoundingBox centrado en el punto
        """
        lat_delta = radius_km / 111.32
        lon_delta = radius_km / (111.32 * math.cos(math.radians(lat)))
        
        return BoundingBox(
            north=min(90, lat + lat_delta),
            south=max(-90, lat - lat_delta),
            east=lon + lon_delta,
            west=lon - lon_delta
        )
