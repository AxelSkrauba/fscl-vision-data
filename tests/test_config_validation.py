"""
Tests de integracion para validar archivos de configuracion YAML.

Verifica que todos los datasets definan las claves requeridas
por el pipeline y que los tipos sean correctos.
"""

import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

CONFIG_DIR = Path(__file__).parent.parent / "config" / "datasets"
DATASET_YAMLS = list(CONFIG_DIR.glob("*.yaml"))


class TestDatasetConfigs:
    """Valida estructura de todos los YAML de datasets."""

    @pytest.mark.parametrize("config_path", DATASET_YAMLS, ids=lambda p: p.name)
    def test_dataset_has_required_sections(self, config_path):
        """Cada dataset debe tener al menos dataset, api, quality, sampling y fauna."""
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        assert "dataset" in config
        assert "api" in config
        assert "quality" in config
        assert "sampling" in config
        assert "fauna" in config

    @pytest.mark.parametrize("config_path", DATASET_YAMLS, ids=lambda p: p.name)
    def test_api_keys_match_script_expectations(self, config_path):
        """
        Verifica que las claves de rate limiting sean compatibles
        con la correccion aplicada en 01_fetch_observations.py.
        """
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        api = config.get("api", {})
        # Los scripts ahora soportan rate_limit_calls/rate_limit_period
        # o rate_limit_requests_per_minute/rate_limit_requests_per_day.
        has_new_keys = "rate_limit_calls" in api and "rate_limit_period" in api
        has_old_keys = (
            "rate_limit_requests_per_minute" in api
            and "rate_limit_requests_per_day" in api
        )
        assert has_new_keys or has_old_keys, (
            f"{config_path.name}: api debe definir rate_limit_calls/rate_limit_period "
            f"o rate_limit_requests_per_minute/rate_limit_requests_per_day"
        )

    @pytest.mark.parametrize("config_path", DATASET_YAMLS, ids=lambda p: p.name)
    def test_sampling_has_n_samples_per_species(self, config_path):
        """
        Verifica que sampling use 'n_samples_per_species' (no la clave
        obsoleta 'samples_per_specie') alineada con 05_select_samples.py.
        """
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        sampling = config.get("sampling", {})
        assert "n_samples_per_species" in sampling, (
            f"{config_path.name}: sampling debe contener 'n_samples_per_species'. "
            f"La clave obsoleta 'samples_per_species' ya no es soportada."
        )
        assert isinstance(sampling["n_samples_per_species"], int)
        assert sampling["n_samples_per_species"] > 0

    @pytest.mark.parametrize("config_path", DATASET_YAMLS, ids=lambda p: p.name)
    def test_fauna_taxa_have_name_and_taxon_id(self, config_path):
        """Cada entrada de fauna debe tener name y taxon_id."""
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        taxa = config.get("fauna", {}).get("taxa", [])
        assert len(taxa) > 0, f"{config_path.name}: no define taxa"

        for entry in taxa:
            assert "name" in entry, f"{config_path.name}: falta 'name' en taxon"
            assert "taxon_id" in entry, f"{config_path.name}: falta 'taxon_id' en taxon"
            assert isinstance(entry["taxon_id"], int)

    @pytest.mark.parametrize("config_path", DATASET_YAMLS, ids=lambda p: p.name)
    def test_quality_section_has_numeric_thresholds(self, config_path):
        """quality debe tener umbrales numericos."""
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        quality = config.get("quality", {})
        for key in ["minimum_width", "minimum_height", "quality_score_threshold"]:
            assert key in quality, f"{config_path.name}: falta '{key}' en quality"
            assert isinstance(quality[key], (int, float))

    def test_default_yaml_uses_n_samples_per_species(self):
        """El template default.yaml debe usar la clave normalizada."""
        default_path = Path(__file__).parent.parent / "config" / "default.yaml"
        with open(default_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        sampling = config.get("sampling", {})
        assert "n_samples_per_species" in sampling, (
            "default.yaml debe usar 'n_samples_per_species'"
        )
        assert "samples_per_species" not in sampling, (
            "default.yaml aun contiene la clave obsoleta 'samples_per_species'"
        )
