# Logger

Módulo: `src/utils/logger.py`

## Descripción

Proporciona un sistema de logging estructurado con salida a consola y archivos, con formato consistente para todo el pipeline.

## Función Principal

### `setup_logger`

```python
from src.utils.logger import setup_logger

logger = setup_logger(
    name="mi_modulo",
    log_dir="./data/logs",
    level="INFO",
    console=True,
    file=True
)
```

#### Parámetros

| Parámetro | Tipo | Descripción | Valor por defecto |
|-----------|------|-------------|-------------------|
| `name` | str | Nombre del logger | Requerido |
| `log_dir` | str/Path | Directorio para archivos de log | `None` |
| `level` | str | Nivel de logging | `"INFO"` |
| `console` | bool | Habilitar salida a consola | `True` |
| `file` | bool | Habilitar salida a archivo | `True` |

#### Niveles Disponibles

| Nivel | Uso |
|-------|-----|
| `DEBUG` | Información detallada para debugging |
| `INFO` | Confirmación de operaciones normales |
| `WARNING` | Situaciones inesperadas pero manejables |
| `ERROR` | Errores que impiden una operación |
| `CRITICAL` | Errores graves que detienen el programa |

## Formato de Salida

### Consola

```
2024-12-11 10:30:00,123 - mi_modulo - INFO - Mensaje de log
```

### Archivo

Los archivos se crean con el nombre del logger:

```
logs/
├── fetch_observations.log
├── download_images.log
└── deduplicate.log
```

## Ejemplo Completo

```python
from src.utils.logger import setup_logger

# Configurar logger
logger = setup_logger(
    name="mi_pipeline",
    log_dir="./data/logs",
    level="DEBUG"
)

# Usar logger
logger.info("Iniciando proceso")
logger.debug(f"Parámetros: {params}")

try:
    result = process_data()
    logger.info(f"Procesados {len(result)} elementos")
except Exception as e:
    logger.error(f"Error en proceso: {e}")
    raise

logger.info("Proceso completado")
```

## Integración con Módulos

Todos los módulos principales aceptan un logger opcional:

```python
from src.utils.logger import setup_logger
from src.api_client import iNaturalistAPIClient

logger = setup_logger("pipeline", log_dir="./logs")

client = iNaturalistAPIClient(logger=logger)
# Los logs del cliente usarán el mismo logger
```

## Rotación de Logs

Para pipelines de larga duración, considera implementar rotación:

```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    "pipeline.log",
    maxBytes=10*1024*1024,  # 10 MB
    backupCount=5
)
```
