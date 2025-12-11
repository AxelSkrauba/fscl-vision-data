"""
Tests para el modulo de seleccion de muestras.
"""

import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.sample_selector import RepresentativeSampleSelector, SampleSelectionResult


class TestRepresentativeSampleSelector:
    """Tests para RepresentativeSampleSelector."""
    
    @pytest.fixture
    def sample_observations(self):
        """Observaciones de ejemplo."""
        observations = []
        
        for species_id in [100, 200]:
            for i in range(30):
                observations.append({
                    'id': species_id * 100 + i,
                    'taxon': {
                        'id': species_id,
                        'name': f'Species {species_id}'
                    },
                    'latitude': -25.5 + (i * 0.01),
                    'longitude': -54.5 + (i * 0.01),
                    'observed_on': f'2023-{(i % 12) + 1:02d}-15',
                    'quality_score': 50 + (i % 50),
                    'photos': [{'id': species_id * 100 + i}]
                })
        
        return observations
    
    def test_init(self):
        """Test inicializacion."""
        selector = RepresentativeSampleSelector(method='clustering')
        
        assert selector.method == 'clustering'
        assert selector.random_state == 42
    
    def test_select_samples_clustering(self, sample_observations):
        """Test seleccion por clustering."""
        selector = RepresentativeSampleSelector(method='clustering')
        
        result = selector.select_samples(
            sample_observations,
            n_samples_per_species=10,
            min_samples_per_species=5
        )
        
        assert result.total_selected <= 20
        assert len(result.by_species) == 2
    
    def test_select_samples_quality(self, sample_observations):
        """Test seleccion por calidad."""
        selector = RepresentativeSampleSelector(method='quality')
        
        result = selector.select_samples(
            sample_observations,
            n_samples_per_species=10
        )
        
        for obs in result.selected:
            assert obs.get('quality_score', 0) >= 50
    
    def test_select_samples_random(self, sample_observations):
        """Test seleccion aleatoria."""
        selector = RepresentativeSampleSelector(method='random')
        
        result = selector.select_samples(
            sample_observations,
            n_samples_per_species=10
        )
        
        assert result.total_selected <= 20
    
    def test_select_samples_stratified(self, sample_observations):
        """Test seleccion estratificada."""
        selector = RepresentativeSampleSelector(method='stratified')
        
        result = selector.select_samples(
            sample_observations,
            n_samples_per_species=10
        )
        
        assert result.total_selected <= 20
    
    def test_min_samples_filter(self, sample_observations):
        """Test filtro de minimo de muestras."""
        few_samples = sample_observations[:5]
        few_samples.extend([
            {
                'id': 999,
                'taxon': {'id': 999, 'name': 'Rare Species'},
                'latitude': -25.5,
                'longitude': -54.5,
                'observed_on': '2023-06-15',
                'quality_score': 80,
                'photos': [{'id': 999}]
            }
        ])
        
        selector = RepresentativeSampleSelector(method='quality')
        
        result = selector.select_samples(
            few_samples,
            n_samples_per_species=10,
            min_samples_per_species=3
        )
        
        assert 999 not in result.by_species
    
    def test_empty_observations(self):
        """Test con lista vacia."""
        selector = RepresentativeSampleSelector()
        
        result = selector.select_samples([], n_samples_per_species=10)
        
        assert result.total_selected == 0
        assert len(result.selected) == 0
    
    def test_balance_dataset(self, sample_observations):
        """Test balanceo de dataset."""
        selector = RepresentativeSampleSelector()
        
        balanced = selector.balance_dataset(
            sample_observations,
            target_per_species=15
        )
        
        by_species = {}
        for obs in balanced:
            sp_id = obs['taxon']['id']
            by_species[sp_id] = by_species.get(sp_id, 0) + 1
        
        for count in by_species.values():
            assert count <= 15
    
    def test_reproducibility(self, sample_observations):
        """Test reproducibilidad con misma semilla."""
        selector1 = RepresentativeSampleSelector(method='random', random_state=42)
        selector2 = RepresentativeSampleSelector(method='random', random_state=42)
        
        result1 = selector1.select_samples(sample_observations, n_samples_per_species=5)
        result2 = selector2.select_samples(sample_observations, n_samples_per_species=5)
        
        ids1 = sorted([o['id'] for o in result1.selected])
        ids2 = sorted([o['id'] for o in result2.selected])
        
        assert ids1 == ids2


class TestSampleSelectionResult:
    """Tests para SampleSelectionResult."""
    
    def test_dataclass_fields(self):
        """Test campos del dataclass."""
        result = SampleSelectionResult(
            selected=[{'id': 1}],
            total_candidates=100,
            total_selected=10,
            by_species={100: 5, 200: 5},
            selection_method='clustering'
        )
        
        assert result.total_candidates == 100
        assert result.total_selected == 10
        assert result.selection_method == 'clustering'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
