"""
Deduplicacion inteligente basada en clustering espacio-temporal.

Agrupa observaciones que probablemente corresponden al mismo individuo
basandose en proximidad geografica y temporal.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
from datetime import datetime
from dataclasses import dataclass, field

import numpy as np
from sklearn.cluster import DBSCAN


@dataclass
class UniqueIndividual:
    """Representa un individuo unico identificado."""
    individual_id: str
    species: str
    species_id: int
    observations: List[Dict[str, Any]]
    best_observation: Dict[str, Any]
    n_duplicates: int
    date_range: Tuple[str, str]
    location_centroid: Tuple[float, float]


@dataclass
class DeduplicationResult:
    """Resultado del proceso de deduplicacion."""
    unique_individuals: List[UniqueIndividual]
    total_original: int
    total_unique: int
    duplicates_removed: int
    dedup_rate: float
    by_species: Dict[int, Dict[str, int]] = field(default_factory=dict)


class ObservationDeduplicator:
    """
    Agrupa observaciones del mismo individuo usando clustering espacio-temporal.
    
    Estrategia:
    1. Agrupar por especie
    2. DBSCAN en espacio 3D normalizado: (lat, lon, dia_del_ano)
    3. De cada cluster, seleccionar la mejor observacion
    
    Heuristicas para "mejor observacion":
    - Mayor resolucion de foto
    - Mayor engagement (likes + comentarios)
    - Mejor calidad visual (si disponible)
    """
    
    def __init__(
        self,
        spatial_threshold_m: float = 100,
        temporal_threshold_days: int = 1,
        min_samples: int = 1,
        logger: Optional[logging.Logger] = None
    ):
        """
        Inicializa el deduplicador.
        
        Args:
            spatial_threshold_m: Distancia maxima en metros para considerar duplicado
            temporal_threshold_days: Dias maximos entre observaciones para agrupar
            min_samples: Minimo de muestras para formar cluster (DBSCAN)
            logger: Logger opcional
        """
        self.spatial_threshold_m = spatial_threshold_m
        self.temporal_threshold_days = temporal_threshold_days
        self.min_samples = min_samples
        self.logger = logger or logging.getLogger(__name__)
    
    def deduplicate(
        self,
        observations: List[Dict[str, Any]]
    ) -> DeduplicationResult:
        """
        Agrupa observaciones del mismo individuo.
        
        Args:
            observations: Lista de observaciones de iNaturalist
        
        Returns:
            DeduplicationResult con individuos unicos y estadisticas
        """
        if not observations:
            return DeduplicationResult(
                unique_individuals=[],
                total_original=0,
                total_unique=0,
                duplicates_removed=0,
                dedup_rate=0.0
            )
        
        by_species = defaultdict(list)
        for obs in observations:
            taxon = obs.get('taxon', {})
            species_id = taxon.get('id')
            if species_id is not None:
                by_species[species_id].append(obs)
        
        all_unique = []
        species_stats = {}
        
        for species_id, species_obs in by_species.items():
            species_name = species_obs[0].get('taxon', {}).get('name', 'Unknown')
            
            valid_obs = [
                obs for obs in species_obs
                if self._has_valid_coordinates(obs)
            ]
            
            if not valid_obs:
                self.logger.warning(
                    f"No valid coordinates for species {species_name}, skipping"
                )
                continue
            
            clusters = self._cluster_observations(valid_obs)
            
            for cluster_id, cluster_obs in clusters.items():
                best_obs = self._select_best_observation(cluster_obs)
                
                dates = [
                    obs.get('observed_on', '') for obs in cluster_obs
                    if obs.get('observed_on')
                ]
                date_range = (min(dates), max(dates)) if dates else ('', '')
                
                coords = [self._extract_coordinates(obs) for obs in cluster_obs]
                lats = [c[0] for c in coords if c[0] is not None]
                lons = [c[1] for c in coords if c[1] is not None]
                centroid = (np.mean(lats) if lats else 0, np.mean(lons) if lons else 0)
                
                individual = UniqueIndividual(
                    individual_id=f"{species_id}_{cluster_id}",
                    species=species_name,
                    species_id=species_id,
                    observations=cluster_obs,
                    best_observation=best_obs,
                    n_duplicates=len(cluster_obs) - 1,
                    date_range=date_range,
                    location_centroid=centroid
                )
                all_unique.append(individual)
            
            original_count = len(species_obs)
            unique_count = len(clusters)
            species_stats[species_id] = {
                'name': species_name,
                'original': original_count,
                'unique': unique_count,
                'removed': original_count - unique_count,
                'dedup_rate': 1 - (unique_count / original_count) if original_count > 0 else 0
            }
            
            self.logger.info(
                f"{species_name}: {original_count} -> {unique_count} "
                f"({species_stats[species_id]['dedup_rate']*100:.1f}% dedup)"
            )
        
        total_original = len(observations)
        total_unique = len(all_unique)
        
        return DeduplicationResult(
            unique_individuals=all_unique,
            total_original=total_original,
            total_unique=total_unique,
            duplicates_removed=total_original - total_unique,
            dedup_rate=1 - (total_unique / total_original) if total_original > 0 else 0,
            by_species=species_stats
        )
    
    def _extract_coordinates(self, observation: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
        """
        Extrae coordenadas de una observacion de iNaturalist.
        
        iNaturalist puede tener coordenadas en varios formatos:
        - latitude/longitude directos
        - geojson.coordinates [lon, lat]
        - location string "lat,lon"
        
        Returns:
            Tuple (latitude, longitude) o (None, None) si no hay coordenadas
        """
        lat = observation.get('latitude')
        lon = observation.get('longitude')
        
        if lat is not None and lon is not None:
            try:
                return float(lat), float(lon)
            except (TypeError, ValueError):
                pass
        
        geojson = observation.get('geojson')
        if geojson and isinstance(geojson, dict):
            coords = geojson.get('coordinates')
            if coords and len(coords) >= 2:
                try:
                    return float(coords[1]), float(coords[0])
                except (TypeError, ValueError, IndexError):
                    pass
        
        location = observation.get('location')
        if location and isinstance(location, str):
            parts = location.split(',')
            if len(parts) >= 2:
                try:
                    return float(parts[0]), float(parts[1])
                except (ValueError, IndexError):
                    pass
        
        return None, None
    
    def _has_valid_coordinates(self, observation: Dict[str, Any]) -> bool:
        """Verifica si una observacion tiene coordenadas validas."""
        lat, lon = self._extract_coordinates(observation)
        
        if lat is None or lon is None:
            return False
        
        return -90 <= lat <= 90 and -180 <= lon <= 180
    
    def _cluster_observations(
        self,
        observations: List[Dict[str, Any]]
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Agrupa observaciones usando DBSCAN en espacio espacio-temporal.
        
        Args:
            observations: Lista de observaciones con coordenadas validas
        
        Returns:
            Dict mapping cluster_id -> lista de observaciones
        """
        if len(observations) < 2:
            return {0: observations}
        
        features = []
        for obs in observations:
            lat, lon = self._extract_coordinates(obs)
            if lat is None or lon is None:
                lat, lon = 0.0, 0.0
            
            observed_on = obs.get('observed_on', '')
            day_of_year = self._date_to_day_of_year(observed_on)
            
            features.append([lat, lon, day_of_year])
        
        features = np.array(features)
        
        features_normalized = features.copy()
        
        features_normalized[:, 0] = features[:, 0] * 111000
        features_normalized[:, 1] = features[:, 1] * 111000 * np.cos(np.radians(np.mean(features[:, 0])))
        
        temporal_scale = self.spatial_threshold_m / self.temporal_threshold_days
        features_normalized[:, 2] = features[:, 2] * temporal_scale
        
        eps = np.sqrt(
            self.spatial_threshold_m ** 2 +
            (self.temporal_threshold_days * temporal_scale) ** 2
        )
        
        try:
            clustering = DBSCAN(
                eps=eps,
                min_samples=self.min_samples,
                metric='euclidean'
            ).fit(features_normalized)
            
            labels = clustering.labels_
        except Exception as e:
            self.logger.warning(f"DBSCAN failed: {e}. Treating all as unique.")
            labels = list(range(len(observations)))
        
        clusters = defaultdict(list)
        for label, obs in zip(labels, observations):
            if label == -1:
                new_label = max(clusters.keys(), default=-1) + 1
                clusters[new_label].append(obs)
            else:
                clusters[label].append(obs)
        
        return dict(clusters)
    
    def _date_to_day_of_year(self, date_str: str) -> int:
        """Convierte fecha string a dia del ano (1-365)."""
        if not date_str:
            return 182
        
        try:
            if 'T' in date_str:
                date_str = date_str.split('T')[0]
            
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            return dt.timetuple().tm_yday
        except (ValueError, TypeError):
            return 182
    
    def _select_best_observation(
        self,
        cluster_obs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Selecciona la mejor observacion de un cluster.
        
        Criterios (en orden de peso):
        1. Resolucion de foto (40%)
        2. Calidad visual si disponible (30%)
        3. Engagement - likes + comentarios (20%)
        4. Recencia (10%)
        
        Args:
            cluster_obs: Lista de observaciones del mismo cluster
        
        Returns:
            Mejor observacion del cluster
        """
        if not cluster_obs:
            return {}
        
        if len(cluster_obs) == 1:
            return cluster_obs[0]
        
        scores = []
        
        for obs in cluster_obs:
            score = 0.0
            
            photos = obs.get('photos', [])
            if photos:
                photo = photos[0]
                dims = photo.get('original_dimensions', {})
                width = dims.get('width', 640)
                height = dims.get('height', 480)
                resolution = width * height
                
                resolution_score = min(100, (resolution / (1920 * 1080)) * 100)
                score += resolution_score * 0.4
            else:
                score += 25 * 0.4
            
            quality_score = obs.get('quality_score', 50)
            score += quality_score * 0.3
            
            faves = obs.get('faves_count', 0) or 0
            comments = obs.get('comments_count', 0) or 0
            engagement = faves + comments
            engagement_score = min(100, engagement * 10)
            score += engagement_score * 0.2
            
            observed_on = obs.get('observed_on', '')
            if observed_on:
                try:
                    dt = datetime.strptime(observed_on.split('T')[0], '%Y-%m-%d')
                    days_old = (datetime.now() - dt).days
                    recency_score = max(0, 100 - (days_old / 365) * 10)
                    score += recency_score * 0.1
                except (ValueError, TypeError):
                    score += 50 * 0.1
            else:
                score += 50 * 0.1
            
            scores.append(score)
        
        best_idx = int(np.argmax(scores))
        return cluster_obs[best_idx]
    
    def get_dedup_summary(
        self,
        result: DeduplicationResult
    ) -> str:
        """
        Genera un resumen legible del resultado de deduplicacion.
        
        Args:
            result: Resultado de deduplicacion
        
        Returns:
            String con resumen formateado
        """
        lines = [
            "=" * 50,
            "DEDUPLICATION SUMMARY",
            "=" * 50,
            f"Total original observations: {result.total_original}",
            f"Unique individuals identified: {result.total_unique}",
            f"Duplicates removed: {result.duplicates_removed}",
            f"Overall dedup rate: {result.dedup_rate * 100:.1f}%",
            "",
            "By species:",
            "-" * 30
        ]
        
        for species_id, stats in result.by_species.items():
            lines.append(
                f"  {stats['name']}: {stats['original']} -> {stats['unique']} "
                f"({stats['dedup_rate']*100:.1f}% removed)"
            )
        
        lines.append("=" * 50)
        
        return "\n".join(lines)
