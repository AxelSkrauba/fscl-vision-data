"""
Seleccion inteligente de muestras representativas.

Selecciona un subset de imagenes que maximiza diversidad visual,
geografica y temporal mientras mantiene calidad uniforme.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
from dataclasses import dataclass

import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


@dataclass
class SampleSelectionResult:
    """Resultado de la seleccion de muestras."""
    selected: List[Dict[str, Any]]
    total_candidates: int
    total_selected: int
    by_species: Dict[int, int]
    selection_method: str


class RepresentativeSampleSelector:
    """
    Selecciona muestras representativas de un conjunto de observaciones.
    
    Estrategias disponibles:
    1. 'clustering': K-means en espacio de features, selecciona mejor de cada cluster
    2. 'stratified': Muestreo estratificado por ubicacion/tiempo
    3. 'quality': Selecciona top-N por calidad
    4. 'random': Seleccion aleatoria (baseline)
    
    El objetivo es maximizar:
    - Diversidad visual (diferentes angulos, iluminacion)
    - Diversidad geografica (diferentes ubicaciones)
    - Diversidad temporal (diferentes epocas del ano)
    - Calidad uniforme (evitar outliers de baja calidad)
    """
    
    def __init__(
        self,
        method: str = 'clustering',
        random_state: int = 42,
        logger: Optional[logging.Logger] = None
    ):
        """
        Inicializa el selector.
        
        Args:
            method: Metodo de seleccion ('clustering', 'stratified', 'quality', 'random')
            random_state: Semilla para reproducibilidad
            logger: Logger opcional
        """
        self.method = method
        self.random_state = random_state
        self.logger = logger or logging.getLogger(__name__)
        
        self._rng = np.random.RandomState(random_state)
    
    def select_samples(
        self,
        observations: List[Dict[str, Any]],
        n_samples_per_species: int = 50,
        min_samples_per_species: int = 10,
        diversity_weight: float = 0.7,
        quality_weight: float = 0.3
    ) -> SampleSelectionResult:
        """
        Selecciona muestras representativas.
        
        Args:
            observations: Lista de observaciones (con quality_score si disponible)
            n_samples_per_species: Numero objetivo de muestras por especie
            min_samples_per_species: Minimo de muestras para incluir especie
            diversity_weight: Peso de diversidad en seleccion (0-1)
            quality_weight: Peso de calidad en seleccion (0-1)
        
        Returns:
            SampleSelectionResult con muestras seleccionadas
        """
        by_species = defaultdict(list)
        for obs in observations:
            taxon = obs.get('taxon', {})
            species_id = taxon.get('id')
            if species_id is not None:
                by_species[species_id].append(obs)
        
        all_selected = []
        species_counts = {}
        
        for species_id, species_obs in by_species.items():
            species_name = species_obs[0].get('taxon', {}).get('name', 'Unknown')
            
            if len(species_obs) < min_samples_per_species:
                self.logger.warning(
                    f"Species {species_name} has only {len(species_obs)} samples "
                    f"(min: {min_samples_per_species}), skipping"
                )
                continue
            
            n_to_select = min(n_samples_per_species, len(species_obs))
            
            if self.method == 'clustering':
                selected = self._select_by_clustering(
                    species_obs, n_to_select, diversity_weight, quality_weight
                )
            elif self.method == 'stratified':
                selected = self._select_stratified(species_obs, n_to_select)
            elif self.method == 'quality':
                selected = self._select_by_quality(species_obs, n_to_select)
            else:
                selected = self._select_random(species_obs, n_to_select)
            
            all_selected.extend(selected)
            species_counts[species_id] = len(selected)
            
            self.logger.info(
                f"{species_name}: selected {len(selected)}/{len(species_obs)} samples"
            )
        
        return SampleSelectionResult(
            selected=all_selected,
            total_candidates=len(observations),
            total_selected=len(all_selected),
            by_species=species_counts,
            selection_method=self.method
        )
    
    def _select_by_clustering(
        self,
        observations: List[Dict[str, Any]],
        n_samples: int,
        diversity_weight: float,
        quality_weight: float
    ) -> List[Dict[str, Any]]:
        """
        Selecciona usando K-means clustering en espacio de features.
        
        De cada cluster, selecciona la observacion con mejor balance
        diversidad-calidad.
        """
        if len(observations) <= n_samples:
            return observations
        
        features = self._extract_features(observations)
        
        if features is None or len(features) < n_samples:
            return self._select_by_quality(observations, n_samples)
        
        n_clusters = min(n_samples, len(observations))
        
        try:
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)
            
            kmeans = KMeans(
                n_clusters=n_clusters,
                random_state=self.random_state,
                n_init=10
            )
            labels = kmeans.fit_predict(features_scaled)
            
        except Exception as e:
            self.logger.warning(f"Clustering failed: {e}. Falling back to quality.")
            return self._select_by_quality(observations, n_samples)
        
        selected = []
        
        for cluster_id in range(n_clusters):
            cluster_mask = labels == cluster_id
            cluster_indices = np.where(cluster_mask)[0]
            
            if len(cluster_indices) == 0:
                continue
            
            cluster_obs = [observations[i] for i in cluster_indices]
            
            best_obs = self._select_best_from_cluster(
                cluster_obs, quality_weight
            )
            selected.append(best_obs)
        
        if len(selected) < n_samples:
            remaining = [obs for obs in observations if obs not in selected]
            remaining.sort(
                key=lambda o: o.get('quality_score', 50),
                reverse=True
            )
            selected.extend(remaining[:n_samples - len(selected)])
        
        return selected[:n_samples]
    
    def _select_stratified(
        self,
        observations: List[Dict[str, Any]],
        n_samples: int
    ) -> List[Dict[str, Any]]:
        """
        Seleccion estratificada por ubicacion y tiempo.
        
        Divide el espacio geografico-temporal en celdas y
        selecciona de cada celda.
        """
        if len(observations) <= n_samples:
            return observations
        
        n_geo_bins = max(2, int(np.sqrt(n_samples)))
        n_time_bins = max(2, n_samples // n_geo_bins)
        
        lats = [obs.get('latitude', 0) for obs in observations]
        lons = [obs.get('longitude', 0) for obs in observations]
        
        lat_bins = np.linspace(min(lats), max(lats) + 0.001, n_geo_bins + 1)
        lon_bins = np.linspace(min(lons), max(lons) + 0.001, n_geo_bins + 1)
        
        strata = defaultdict(list)
        
        for obs in observations:
            lat = obs.get('latitude', 0)
            lon = obs.get('longitude', 0)
            
            lat_bin = np.digitize(lat, lat_bins) - 1
            lon_bin = np.digitize(lon, lon_bins) - 1
            
            observed_on = obs.get('observed_on', '')
            month = self._extract_month(observed_on)
            time_bin = month // (12 // n_time_bins) if month else 0
            
            stratum_key = (lat_bin, lon_bin, time_bin)
            strata[stratum_key].append(obs)
        
        selected = []
        samples_per_stratum = max(1, n_samples // len(strata)) if strata else 1
        
        for stratum_obs in strata.values():
            stratum_obs.sort(
                key=lambda o: o.get('quality_score', 50),
                reverse=True
            )
            selected.extend(stratum_obs[:samples_per_stratum])
        
        if len(selected) < n_samples:
            remaining = [obs for obs in observations if obs not in selected]
            remaining.sort(
                key=lambda o: o.get('quality_score', 50),
                reverse=True
            )
            selected.extend(remaining[:n_samples - len(selected)])
        
        return selected[:n_samples]
    
    def _select_by_quality(
        self,
        observations: List[Dict[str, Any]],
        n_samples: int
    ) -> List[Dict[str, Any]]:
        """Selecciona las N observaciones de mayor calidad."""
        sorted_obs = sorted(
            observations,
            key=lambda o: o.get('quality_score', 50),
            reverse=True
        )
        return sorted_obs[:n_samples]
    
    def _select_random(
        self,
        observations: List[Dict[str, Any]],
        n_samples: int
    ) -> List[Dict[str, Any]]:
        """Seleccion aleatoria."""
        if len(observations) <= n_samples:
            return observations
        
        indices = self._rng.choice(
            len(observations),
            size=n_samples,
            replace=False
        )
        return [observations[i] for i in indices]
    
    def _extract_features(
        self,
        observations: List[Dict[str, Any]]
    ) -> Optional[np.ndarray]:
        """
        Extrae features para clustering.
        
        Features:
        - Latitud, Longitud (geografico)
        - Dia del ano (temporal)
        - Quality score (calidad)
        """
        features = []
        
        for obs in observations:
            lat = obs.get('latitude')
            lon = obs.get('longitude')
            
            if lat is None or lon is None:
                continue
            
            observed_on = obs.get('observed_on', '')
            day_of_year = self._date_to_day_of_year(observed_on)
            
            quality = obs.get('quality_score', 50)
            
            features.append([
                float(lat),
                float(lon),
                float(day_of_year),
                float(quality)
            ])
        
        if not features:
            return None
        
        return np.array(features)
    
    def _select_best_from_cluster(
        self,
        cluster_obs: List[Dict[str, Any]],
        quality_weight: float
    ) -> Dict[str, Any]:
        """Selecciona la mejor observacion de un cluster."""
        if len(cluster_obs) == 1:
            return cluster_obs[0]
        
        best_obs = max(
            cluster_obs,
            key=lambda o: o.get('quality_score', 50)
        )
        return best_obs
    
    def _date_to_day_of_year(self, date_str: str) -> int:
        """Convierte fecha a dia del ano."""
        if not date_str:
            return 182
        
        try:
            if 'T' in date_str:
                date_str = date_str.split('T')[0]
            
            parts = date_str.split('-')
            if len(parts) >= 2:
                month = int(parts[1])
                day = int(parts[2]) if len(parts) > 2 else 15
                return (month - 1) * 30 + day
            return 182
        except (ValueError, IndexError):
            return 182
    
    def _extract_month(self, date_str: str) -> int:
        """Extrae mes de una fecha."""
        if not date_str:
            return 6
        
        try:
            if 'T' in date_str:
                date_str = date_str.split('T')[0]
            
            parts = date_str.split('-')
            if len(parts) >= 2:
                return int(parts[1])
            return 6
        except (ValueError, IndexError):
            return 6
    
    def balance_dataset(
        self,
        observations: List[Dict[str, Any]],
        target_per_species: int,
        allow_undersampling: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Balancea el dataset para tener igual numero de muestras por especie.
        
        Args:
            observations: Lista de observaciones
            target_per_species: Numero objetivo por especie
            allow_undersampling: Si permitir reducir especies con mas muestras
        
        Returns:
            Lista balanceada de observaciones
        """
        by_species = defaultdict(list)
        for obs in observations:
            taxon = obs.get('taxon', {})
            species_id = taxon.get('id')
            if species_id is not None:
                by_species[species_id].append(obs)
        
        balanced = []
        
        for species_id, species_obs in by_species.items():
            if len(species_obs) >= target_per_species:
                if allow_undersampling:
                    selected = self._select_by_quality(species_obs, target_per_species)
                else:
                    selected = species_obs
            else:
                selected = species_obs
            
            balanced.extend(selected)
        
        self.logger.info(
            f"Balanced dataset: {len(observations)} -> {len(balanced)} "
            f"({len(by_species)} species)"
        )
        
        return balanced
