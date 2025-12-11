"""
Utilidades para procesamiento de imagenes.
"""

import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
from io import BytesIO

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


class ImageUtils:
    """Utilidades para manipulacion y validacion de imagenes."""
    
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        
        if not PIL_AVAILABLE:
            self.logger.warning("PIL not available. Some features disabled.")
        if not CV2_AVAILABLE:
            self.logger.warning("OpenCV not available. Some features disabled.")
    
    def validate_image(self, image_path: Path) -> Dict[str, Any]:
        """
        Valida una imagen y retorna informacion basica.
        
        Args:
            image_path: Ruta a la imagen
        
        Returns:
            Dict con informacion de validacion:
            - valid: bool
            - width: int (si valid)
            - height: int (si valid)
            - format: str (si valid)
            - error: str (si not valid)
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            return {'valid': False, 'error': 'File does not exist'}
        
        if image_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            return {
                'valid': False,
                'error': f'Unsupported format: {image_path.suffix}'
            }
        
        if not PIL_AVAILABLE:
            return {
                'valid': True,
                'width': None,
                'height': None,
                'format': image_path.suffix.lower(),
                'warning': 'PIL not available for full validation'
            }
        
        try:
            with Image.open(image_path) as img:
                img.verify()
            
            with Image.open(image_path) as img:
                width, height = img.size
                img_format = img.format
            
            return {
                'valid': True,
                'width': width,
                'height': height,
                'format': img_format,
                'file_size_bytes': image_path.stat().st_size
            }
        
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def get_image_dimensions(
        self,
        image_path: Path
    ) -> Optional[Tuple[int, int]]:
        """
        Obtiene las dimensiones de una imagen.
        
        Args:
            image_path: Ruta a la imagen
        
        Returns:
            Tupla (width, height) o None si hay error
        """
        if not PIL_AVAILABLE:
            return None
        
        try:
            with Image.open(image_path) as img:
                return img.size
        except Exception as e:
            self.logger.warning(f"Error getting dimensions for {image_path}: {e}")
            return None
    
    def resize_image(
        self,
        image_path: Path,
        output_path: Path,
        max_size: int = 1024,
        quality: int = 90
    ) -> bool:
        """
        Redimensiona una imagen manteniendo aspect ratio.
        
        Args:
            image_path: Ruta de imagen origen
            output_path: Ruta de imagen destino
            max_size: Tamano maximo del lado mayor
            quality: Calidad JPEG (1-100)
        
        Returns:
            True si exitoso
        """
        if not PIL_AVAILABLE:
            self.logger.error("PIL required for resize_image")
            return False
        
        try:
            with Image.open(image_path) as img:
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                width, height = img.size
                
                if width > max_size or height > max_size:
                    if width > height:
                        new_width = max_size
                        new_height = int(height * max_size / width)
                    else:
                        new_height = max_size
                        new_width = int(width * max_size / height)
                    
                    img = img.resize(
                        (new_width, new_height),
                        Image.Resampling.LANCZOS
                    )
                
                output_path.parent.mkdir(parents=True, exist_ok=True)
                img.save(output_path, 'JPEG', quality=quality)
                return True
        
        except Exception as e:
            self.logger.error(f"Error resizing {image_path}: {e}")
            return False
    
    def load_image_cv2(self, image_path: Path) -> Optional['np.ndarray']:
        """
        Carga una imagen usando OpenCV.
        
        Args:
            image_path: Ruta a la imagen
        
        Returns:
            Array numpy BGR o None si hay error
        """
        if not CV2_AVAILABLE:
            self.logger.error("OpenCV required for load_image_cv2")
            return None
        
        try:
            img = cv2.imread(str(image_path))
            if img is None:
                self.logger.warning(f"Could not load image: {image_path}")
            return img
        except Exception as e:
            self.logger.error(f"Error loading {image_path}: {e}")
            return None
    
    def load_image_grayscale(self, image_path: Path) -> Optional['np.ndarray']:
        """
        Carga una imagen en escala de grises.
        
        Args:
            image_path: Ruta a la imagen
        
        Returns:
            Array numpy grayscale o None si hay error
        """
        if not CV2_AVAILABLE:
            self.logger.error("OpenCV required for load_image_grayscale")
            return None
        
        try:
            img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
            if img is None:
                self.logger.warning(f"Could not load image: {image_path}")
            return img
        except Exception as e:
            self.logger.error(f"Error loading {image_path}: {e}")
            return None
    
    @staticmethod
    def bytes_to_pil_image(image_bytes: bytes) -> Optional['Image.Image']:
        """
        Convierte bytes a imagen PIL.
        
        Args:
            image_bytes: Bytes de la imagen
        
        Returns:
            Imagen PIL o None si hay error
        """
        if not PIL_AVAILABLE:
            return None
        
        try:
            return Image.open(BytesIO(image_bytes))
        except Exception:
            return None
