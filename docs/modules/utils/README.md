# Utilidades

Módulos auxiliares que proporcionan funcionalidades comunes utilizadas por los módulos principales.

## Módulos

| Módulo | Archivo | Descripción |
|--------|---------|-------------|
| [Logger](logger.md) | `src/utils/logger.py` | Sistema de logging estructurado |
| [Rate Limiter](rate_limiter.md) | `src/utils/rate_limiter.py` | Control de tasa de llamadas API |
| [Geo Utils](geo_utils.md) | `src/utils/geo_utils.py` | Utilidades geográficas |
| [Image Utils](image_utils.md) | `src/utils/image_utils.py` | Procesamiento de imágenes |

## Uso

Las utilidades se importan desde el paquete `src.utils`:

```python
from src.utils import (
    setup_logger,
    RateLimiter,
    GeoUtils,
    BoundingBox,
    ImageUtils
)
```

O individualmente:

```python
from src.utils.logger import setup_logger
from src.utils.rate_limiter import RateLimiter
from src.utils.geo_utils import GeoUtils, BoundingBox
from src.utils.image_utils import ImageUtils
```
