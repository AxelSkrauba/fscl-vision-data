"""
Tests para el modulo de deduplicacion.
"""

import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.deduplicator import ObservationDeduplicator, DeduplicationResult


class TestObservationDeduplicator:
    """Tests para ObservationDeduplicator."""
    
    @pytest.fixture
    def sample_observations(self):
        """Observaciones de ejemplo para tests."""
        return [
            {
                'id': 1,
                'taxon': {'id': 100, 'name': 'Species A'},
                'latitude': -25.5,
                'longitude': -54.5,
                'observed_on': '2023-06-15',
                'photos': [{'id': 1, 'url': 'http://example.com/1.jpg'}]
            },
            {
                'id': 2,
                'taxon': {'id': 100, 'name': 'Species A'},
                'latitude': -25.5001,
                'longitude': -54.5001,
                'observed_on': '2023-06-15',
                'photos': [{'id': 2, 'url': 'http://example.com/2.jpg'}]
            },
            {
                'id': 3,
                'taxon': {'id': 100, 'name': 'Species A'},
                'latitude': -26.0,
                'longitude': -55.0,
                'observed_on': '2023-07-20',
                'photos': [{'id': 3, 'url': 'http://example.com/3.jpg'}]
            },
            {
                'id': 4,
                'taxon': {'id': 200, 'name': 'Species B'},
                'latitude': -25.5,
                'longitude': -54.5,
                'observed_on': '2023-06-15',
                'photos': [{'id': 4, 'url': 'http://example.com/4.jpg'}]
            },
        ]
    
    def test_init(self):
        """Test inicializacion."""
        dedup = ObservationDeduplicator(
            spatial_threshold_m=100,
            temporal_threshold_days=1
        )
        
        assert dedup.spatial_threshold_m == 100
        assert dedup.temporal_threshold_days == 1
    
    def test_deduplicate_empty(self):
        """Test deduplicacion de lista vacia."""
        dedup = ObservationDeduplicator()
        
        result = dedup.deduplicate([])
        
        assert result.total_original == 0
        assert result.total_unique == 0
        assert result.dedup_rate == 0
    
    def test_deduplicate_groups_nearby(self, sample_observations):
        """Test que agrupa observaciones cercanas."""
        dedup = ObservationDeduplicator(
            spatial_threshold_m=500,
            temporal_threshold_days=1
        )
        
        result = dedup.deduplicate(sample_observations)
        
        assert result.total_original == 4
        assert result.total_unique < 4
    
    def test_deduplicate_separates_species(self, sample_observations):
        """Test que separa diferentes especies."""
        dedup = ObservationDeduplicator(
            spatial_threshold_m=1000,
            temporal_threshold_days=30
        )
        
        result = dedup.deduplicate(sample_observations)
        
        species_ids = set()
        for ind in result.unique_individuals:
            species_ids.add(ind.species_id)
        
        assert 100 in species_ids
        assert 200 in species_ids
    
    def test_deduplicate_separates_distant(self, sample_observations):
        """Test que separa observaciones distantes."""
        dedup = ObservationDeduplicator(
            spatial_threshold_m=100,
            temporal_threshold_days=1
        )
        
        result = dedup.deduplicate(sample_observations)
        
        species_a_individuals = [
            ind for ind in result.unique_individuals
            if ind.species_id == 100
        ]
        
        assert len(species_a_individuals) >= 2
    
    def test_dedup_rate(self, sample_observations):
        """Test calculo de tasa de deduplicacion."""
        dedup = ObservationDeduplicator(
            spatial_threshold_m=500,
            temporal_threshold_days=1
        )
        
        result = dedup.deduplicate(sample_observations)
        
        expected_rate = 1 - (result.total_unique / result.total_original)
        assert abs(result.dedup_rate - expected_rate) < 0.001
    
    def test_best_observation_selection(self, sample_observations):
        """Test seleccion de mejor observacion."""
        sample_observations[0]['faves_count'] = 10
        sample_observations[1]['faves_count'] = 1
        
        dedup = ObservationDeduplicator(
            spatial_threshold_m=500,
            temporal_threshold_days=1
        )
        
        result = dedup.deduplicate(sample_observations)
        
        for ind in result.unique_individuals:
            assert ind.best_observation is not None
            assert 'id' in ind.best_observation
    
    def test_handles_missing_coordinates(self):
        """Test manejo de coordenadas faltantes."""
        observations = [
            {
                'id': 1,
                'taxon': {'id': 100, 'name': 'Species A'},
                'latitude': None,
                'longitude': None,
                'observed_on': '2023-06-15',
                'photos': [{'id': 1}]
            },
            {
                'id': 2,
                'taxon': {'id': 100, 'name': 'Species A'},
                'latitude': -25.5,
                'longitude': -54.5,
                'observed_on': '2023-06-15',
                'photos': [{'id': 2}]
            },
        ]
        
        dedup = ObservationDeduplicator()
        result = dedup.deduplicate(observations)
        
        assert result.total_unique >= 1
    
    def test_get_dedup_summary(self, sample_observations):
        """Test generacion de resumen."""
        dedup = ObservationDeduplicator()
        result = dedup.deduplicate(sample_observations)
        
        summary = dedup.get_dedup_summary(result)
        
        assert 'DEDUPLICATION SUMMARY' in summary
        assert 'Total original observations' in summary


class TestDeduplicationResult:
    """Tests para DeduplicationResult."""
    
    def test_dataclass_fields(self):
        """Test campos del dataclass."""
        result = DeduplicationResult(
            unique_individuals=[],
            total_original=10,
            total_unique=5,
            duplicates_removed=5,
            dedup_rate=0.5
        )
        
        assert result.total_original == 10
        assert result.total_unique == 5
        assert result.duplicates_removed == 5
        assert result.dedup_rate == 0.5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
