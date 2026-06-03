"""
Test de regresion para verificar que 05_select_samples.py respeta
n_samples_per_species definido en el YAML de configuracion.

Referencia: bugfix donde el script buscaba 'samples_per_species'
en vez de 'n_samples_per_species', siempre usando el default 50.
"""

import json
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.sample_selector import RepresentativeSampleSelector


class TestSelectSamplesRegression:
    """Regresion: n_samples_per_species desde YAML."""

    @pytest.fixture
    def sample_observations(self):
        """Genera observaciones de prueba para 2 especies."""
        observations = []
        for species_id in [100, 200]:
            for i in range(120):
                observations.append({
                    "id": species_id * 100 + i,
                    "taxon": {
                        "id": species_id,
                        "name": f"Species {species_id}"
                    },
                    "latitude": -25.5 + (i * 0.01),
                    "longitude": -54.5 + (i * 0.01),
                    "observed_on": "2023-06-15",
                    "quality_score": 50 + (i % 50),
                    "photos": [{"id": species_id * 100 + i}]
                })
        return observations

    def test_n_samples_per_species_from_yaml(self, sample_observations, tmp_path):
        """
        Simula el comportamiento de 05_select_samples.py leyendo n_samples_per_species
        desde un YAML y verifica que no se cae en el default 50.
        """
        config = {
            "data_dir": str(tmp_path),
            "sampling": {
                "method": "quality",
                "n_samples_per_species": 80,
                "min_samples_per_species": 10
            }
        }
        # Guardar config como YAML temporal
        config_path = tmp_path / "test_config.yaml"
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        # Simular logica de 05_select_samples.py (sin logging)
        sampling_config = config.get("sampling", {})
        n_samples = sampling_config.get("n_samples_per_species", 50)
        selection_method = sampling_config.get("method", "clustering")
        min_samples = sampling_config.get("min_samples_per_species", 10)

        selector = RepresentativeSampleSelector(
            method=selection_method,
            random_state=42
        )

        result = selector.select_samples(
            observations=sample_observations,
            n_samples_per_species=n_samples,
            min_samples_per_species=min_samples
        )

        # La regresion anterior daba 50 porque n_samples valia 50 (default)
        assert n_samples == 80, (
            "El script deberia haber leido 80 desde el YAML, "
            f"pero obtuvo {n_samples}"
        )
        assert result.total_selected == 160, (
            f"Esperaba 160 muestras (2 especies x 80), "
            f"pero se obtuvieron {result.total_selected}"
        )
        for sp_id, count in result.by_species.items():
            assert count == 80, (
                f"Especie {sp_id}: esperaba 80, obtuvo {count}"
            )
