"""
Tests para el modulo de evaluacion de calidad.
"""

import pytest
import tempfile
from pathlib import Path

import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.quality_assessor import ImageQualityAssessor, QualityScores

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


class TestQualityScores:
    """Tests para QualityScores dataclass."""
    
    def test_init(self):
        """Test inicializacion."""
        scores = QualityScores(
            sharpness=80.0,
            exposure=70.0,
            contrast=75.0,
            composition=65.0,
            blur=85.0,
            overall=75.0
        )
        
        assert scores.sharpness == 80.0
        assert scores.overall == 75.0
    
    def test_to_dict(self):
        """Test conversion a diccionario."""
        scores = QualityScores(
            sharpness=80.0,
            exposure=70.0,
            contrast=75.0,
            composition=65.0,
            blur=85.0,
            overall=75.0
        )
        
        d = scores.to_dict()
        
        assert d['sharpness'] == 80.0
        assert d['overall'] == 75.0
        assert len(d) == 6


class TestImageQualityAssessor:
    """Tests para ImageQualityAssessor."""
    
    def test_init_default_weights(self):
        """Test inicializacion con pesos por defecto."""
        assessor = ImageQualityAssessor()
        
        assert assessor.weights['sharpness'] == 0.30
        assert assessor.weights['exposure'] == 0.20
        assert sum(assessor.weights.values()) == pytest.approx(1.0)
    
    def test_init_custom_weights(self):
        """Test inicializacion con pesos personalizados."""
        custom_weights = {
            'sharpness': 0.5,
            'exposure': 0.2,
            'contrast': 0.1,
            'composition': 0.1,
            'blur': 0.1
        }
        
        assessor = ImageQualityAssessor(weights=custom_weights)
        
        assert assessor.weights['sharpness'] == 0.5
    
    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_assess_quality_synthetic(self):
        """Test evaluacion con imagen sintetica."""
        with tempfile.TemporaryDirectory() as tmpdir:
            img_path = Path(tmpdir) / "test.jpg"
            img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            cv2.imwrite(str(img_path), img)
            
            assessor = ImageQualityAssessor()
            scores = assessor.assess_quality(img_path)
            
            assert scores is not None
            assert 0 <= scores.overall <= 100
            assert 0 <= scores.sharpness <= 100
    
    def test_assess_quality_nonexistent(self):
        """Test evaluacion de imagen inexistente."""
        assessor = ImageQualityAssessor()
        
        scores = assessor.assess_quality(Path("/nonexistent/image.jpg"))
        
        assert scores is None
    
    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_assess_batch(self):
        """Test evaluacion por lotes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = []
            for i in range(3):
                img_path = Path(tmpdir) / f"test_{i}.jpg"
                img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
                cv2.imwrite(str(img_path), img)
                paths.append(img_path)
            
            assessor = ImageQualityAssessor()
            results = assessor.assess_batch(paths)
            
            assert len(results) == 3
    
    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_filter_by_quality(self):
        """Test filtrado por calidad."""
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = []
            for i in range(5):
                img_path = Path(tmpdir) / f"test_{i}.jpg"
                img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
                cv2.imwrite(str(img_path), img)
                paths.append(img_path)
            
            assessor = ImageQualityAssessor()
            scores = assessor.assess_batch(paths)
            
            passed = assessor.filter_by_quality(scores, min_overall=0)
            
            assert len(passed) <= len(scores)
    
    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_get_statistics(self):
        """Test calculo de estadisticas."""
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = []
            for i in range(3):
                img_path = Path(tmpdir) / f"test_{i}.jpg"
                img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
                cv2.imwrite(str(img_path), img)
                paths.append(img_path)
            
            assessor = ImageQualityAssessor()
            scores = assessor.assess_batch(paths)
            stats = assessor.get_statistics(scores)
            
            assert 'overall' in stats
            assert 'mean' in stats['overall']
            assert 'std' in stats['overall']
    
    def test_get_statistics_empty(self):
        """Test estadisticas con diccionario vacio."""
        assessor = ImageQualityAssessor()
        
        stats = assessor.get_statistics({})
        
        assert stats == {}
    
    def test_normalize_score(self):
        """Test normalizacion de scores."""
        result = ImageQualityAssessor._normalize_score(50, 0, 100)
        assert result == 50.0
        
        result = ImageQualityAssessor._normalize_score(0, 0, 100)
        assert result == 0.0
        
        result = ImageQualityAssessor._normalize_score(100, 0, 100)
        assert result == 100.0
        
        result = ImageQualityAssessor._normalize_score(150, 0, 100)
        assert result == 100.0
        
        result = ImageQualityAssessor._normalize_score(-50, 0, 100)
        assert result == 0.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
