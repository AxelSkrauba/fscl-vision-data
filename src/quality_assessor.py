"""
Evaluacion de calidad de imagenes mediante multiples metricas.

Evalua sharpness, exposure, contrast, composicion y blur para
determinar la calidad general de cada imagen.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

import numpy as np

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


@dataclass
class QualityScores:
    """Scores de calidad para una imagen."""
    sharpness: float
    exposure: float
    contrast: float
    composition: float
    blur: float
    overall: float
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'sharpness': self.sharpness,
            'exposure': self.exposure,
            'contrast': self.contrast,
            'composition': self.composition,
            'blur': self.blur,
            'overall': self.overall
        }


class ImageQualityAssessor:
    """
    Evalua multiples aspectos de calidad de imagen.
    
    Metricas evaluadas:
    1. Sharpness (Laplacian variance) - Nitidez de la imagen
    2. Exposure (histogram distribution) - Exposicion correcta
    3. Contrast (dynamic range) - Rango dinamico
    4. Composition (entropy) - Complejidad visual
    5. Blur detection (frequency analysis) - Deteccion de desenfoque
    
    Cada metrica retorna un score de 0-100.
    """
    
    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Inicializa el evaluador de calidad.
        
        Args:
            weights: Pesos personalizados para cada metrica.
                    Default: sharpness=0.30, exposure=0.20, contrast=0.20,
                            composition=0.15, blur=0.15
            logger: Logger opcional
        """
        self.logger = logger or logging.getLogger(__name__)
        
        self.weights = weights or {
            'sharpness': 0.30,
            'exposure': 0.20,
            'contrast': 0.20,
            'composition': 0.15,
            'blur': 0.15
        }
        
        if not CV2_AVAILABLE:
            self.logger.warning(
                "OpenCV not available. Quality assessment will be limited."
            )
    
    def assess_quality(self, image_path: Path) -> Optional[QualityScores]:
        """
        Evalua la calidad de una imagen.
        
        Args:
            image_path: Ruta a la imagen
        
        Returns:
            QualityScores con scores 0-100 para cada metrica,
            o None si hay error
        """
        if not CV2_AVAILABLE:
            self.logger.warning("OpenCV required for quality assessment")
            return QualityScores(
                sharpness=50, exposure=50, contrast=50,
                composition=50, blur=50, overall=50
            )
        
        image_path = Path(image_path)
        
        if not image_path.exists():
            self.logger.warning(f"Image not found: {image_path}")
            return None
        
        try:
            img = cv2.imread(str(image_path))
            if img is None:
                self.logger.warning(f"Could not load image: {image_path}")
                return None
            
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            sharpness = self._assess_sharpness(gray)
            exposure = self._assess_exposure(gray)
            contrast = self._assess_contrast(gray)
            composition = self._assess_composition(gray)
            blur = self._assess_blur(gray)
            
            overall = (
                sharpness * self.weights['sharpness'] +
                exposure * self.weights['exposure'] +
                contrast * self.weights['contrast'] +
                composition * self.weights['composition'] +
                blur * self.weights['blur']
            )
            
            return QualityScores(
                sharpness=sharpness,
                exposure=exposure,
                contrast=contrast,
                composition=composition,
                blur=blur,
                overall=overall
            )
        
        except Exception as e:
            self.logger.error(f"Error assessing {image_path}: {e}")
            return None
    
    def _assess_sharpness(self, gray: np.ndarray) -> float:
        """
        Evalua nitidez usando varianza del Laplaciano.
        
        Mayor varianza = imagen mas nitida.
        """
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()
        
        return self._normalize_score(variance, min_val=100, max_val=2000)
    
    def _assess_exposure(self, gray: np.ndarray) -> float:
        """
        Evalua exposicion analizando distribucion del histograma.
        
        Penaliza imagenes muy oscuras o muy brillantes.
        Ideal: ~15% pixeles oscuros, ~10% pixeles brillantes.
        """
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist_norm = hist.flatten() / hist.sum()
        
        dark_ratio = np.sum(hist_norm[:64])
        bright_ratio = np.sum(hist_norm[192:])
        mid_ratio = np.sum(hist_norm[64:192])
        
        dark_penalty = abs(dark_ratio - 0.15) * 100
        bright_penalty = abs(bright_ratio - 0.10) * 100
        
        score = 100 - (dark_penalty + bright_penalty)
        
        if mid_ratio < 0.5:
            score -= 20
        
        return max(0, min(100, score))
    
    def _assess_contrast(self, gray: np.ndarray) -> float:
        """
        Evalua contraste usando desviacion estandar.
        
        Mayor std = mayor contraste.
        """
        std = gray.std()
        
        return self._normalize_score(std, min_val=20, max_val=80)
    
    def _assess_composition(self, gray: np.ndarray) -> float:
        """
        Evalua composicion usando entropia de Shannon.
        
        Mayor entropia = imagen mas compleja/interesante.
        """
        entropy = self._calculate_entropy(gray)
        
        return self._normalize_score(entropy, min_val=4.0, max_val=7.5)
    
    def _assess_blur(self, gray: np.ndarray) -> float:
        """
        Detecta blur usando varianza del Laplaciano.
        
        Retorna score alto si la imagen NO esta borrosa.
        """
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()
        
        blur_threshold = 100
        
        if variance < blur_threshold:
            return max(0, (variance / blur_threshold) * 50)
        else:
            return min(100, 50 + (variance - blur_threshold) / 40)
    
    @staticmethod
    def _normalize_score(
        value: float,
        min_val: float,
        max_val: float
    ) -> float:
        """Normaliza un valor al rango 0-100."""
        if max_val <= min_val:
            return 50.0
        
        normalized = (value - min_val) / (max_val - min_val) * 100
        return max(0.0, min(100.0, normalized))
    
    @staticmethod
    def _calculate_entropy(image: np.ndarray) -> float:
        """Calcula entropia de Shannon de una imagen."""
        hist = cv2.calcHist([image], [0], None, [256], [0, 256])
        hist = hist.flatten()
        hist = hist / hist.sum()
        
        hist = hist[hist > 0]
        entropy = -np.sum(hist * np.log2(hist))
        
        return entropy
    
    def assess_batch(
        self,
        image_paths: List[Path],
        progress_callback: Optional[callable] = None
    ) -> Dict[str, QualityScores]:
        """
        Evalua calidad de multiples imagenes.
        
        Args:
            image_paths: Lista de rutas a imagenes
            progress_callback: Callback opcional para progreso
        
        Returns:
            Dict mapping path -> QualityScores
        """
        results = {}
        total = len(image_paths)
        
        for i, path in enumerate(image_paths):
            scores = self.assess_quality(path)
            if scores is not None:
                results[str(path)] = scores
            
            if progress_callback and (i + 1) % 100 == 0:
                progress_callback(i + 1, total)
            
            if (i + 1) % 500 == 0:
                self.logger.info(f"Assessed {i + 1}/{total} images")
        
        self.logger.info(f"Quality assessment complete: {len(results)}/{total} images")
        return results
    
    def filter_by_quality(
        self,
        scores: Dict[str, QualityScores],
        min_overall: float = 40.0,
        min_sharpness: Optional[float] = None,
        max_blur: Optional[float] = None
    ) -> List[str]:
        """
        Filtra imagenes por umbrales de calidad.
        
        Args:
            scores: Dict de scores por imagen
            min_overall: Score overall minimo
            min_sharpness: Sharpness minimo (opcional)
            max_blur: Blur maximo permitido (opcional)
        
        Returns:
            Lista de paths que pasan los filtros
        """
        passed = []
        
        for path, score in scores.items():
            if score.overall < min_overall:
                continue
            
            if min_sharpness is not None and score.sharpness < min_sharpness:
                continue
            
            if max_blur is not None and score.blur < (100 - max_blur):
                continue
            
            passed.append(path)
        
        self.logger.info(
            f"Quality filter: {len(passed)}/{len(scores)} images passed "
            f"(min_overall={min_overall})"
        )
        
        return passed
    
    def get_statistics(
        self,
        scores: Dict[str, QualityScores]
    ) -> Dict[str, Dict[str, float]]:
        """
        Calcula estadisticas de los scores de calidad.
        
        Args:
            scores: Dict de scores por imagen
        
        Returns:
            Dict con mean, std, min, max para cada metrica
        """
        if not scores:
            return {}
        
        metrics = ['sharpness', 'exposure', 'contrast', 'composition', 'blur', 'overall']
        stats = {}
        
        for metric in metrics:
            values = [getattr(s, metric) for s in scores.values()]
            stats[metric] = {
                'mean': float(np.mean(values)),
                'std': float(np.std(values)),
                'min': float(np.min(values)),
                'max': float(np.max(values)),
                'median': float(np.median(values))
            }
        
        return stats
