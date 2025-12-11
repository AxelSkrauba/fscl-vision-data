# Image Downloader

Módulo: `src/image_downloader.py`

## Descripción

Descarga imágenes de observaciones de iNaturalist de forma paralela, con manejo robusto de errores, reintentos y guardado de metadatos.

## Clase Principal

### `ImageDownloader`

```python
from src.image_downloader import ImageDownloader

downloader = ImageDownloader(
    output_dir="./data/raw",
    max_workers=4,
    timeout=30,
    max_retries=3,
    image_size="large",
    save_metadata=True,
    logger=None
)
```

#### Parámetros del Constructor

| Parámetro | Tipo | Descripción | Valor por defecto |
|-----------|------|-------------|-------------------|
| `output_dir` | str/Path | Directorio de salida | `"./data/raw"` |
| `max_workers` | int | Workers paralelos | `4` |
| `timeout` | int | Timeout por descarga (segundos) | `30` |
| `max_retries` | int | Reintentos por imagen | `3` |
| `image_size` | str | Tamaño de imagen | `"large"` |
| `save_metadata` | bool | Guardar JSON por imagen | `True` |
| `logger` | Logger | Logger opcional | `None` |

#### Tamaños de Imagen

| Tamaño | Dimensión | Uso recomendado |
|--------|-----------|-----------------|
| `original` | Variable (hasta 4K) | Máxima calidad |
| `large` | 1024px lado mayor | Balance calidad/tamaño |
| `medium` | 500px lado mayor | Previsualizaciones |
| `small` | 240px lado mayor | Thumbnails |

## Métodos

### `download_observations`

Descarga imágenes de una lista de observaciones.

```python
result = downloader.download_observations(observations)
```

#### Parámetros

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `observations` | List[Dict] | Lista de observaciones de iNaturalist |

#### Retorno

```python
{
    'total_attempted': int,
    'successful': int,
    'failed': int,
    'skipped': int,  # Ya existían
    'by_species': Dict[str, int],
    'failed_ids': List[int],
    'total_size_bytes': int,
    'download_time_seconds': float
}
```

### `download_single`

Descarga una imagen individual.

```python
success = downloader.download_single(
    url="https://...",
    output_path="./image.jpg",
    metadata=None
)
```

### `get_image_url`

Obtiene la URL de la imagen en el tamaño especificado.

```python
url = downloader.get_image_url(photo, size="large")
```

## Estructura de Salida

```
raw/
├── turdus_rufiventris/
│   ├── 123456789.jpg
│   ├── 123456789.json
│   ├── 123456790.jpg
│   └── 123456790.json
└── ramphastos_toco/
    ├── 987654321.jpg
    └── 987654321.json
```

### Metadatos por Imagen

Cada archivo `.json` contiene:

```json
{
  "observation_id": 123456789,
  "photo_id": 987654,
  "species": "Turdus rufiventris",
  "taxon_id": 12738,
  "observed_on": "2024-01-15",
  "location": {
    "latitude": -25.68,
    "longitude": -54.45
  },
  "photographer": "usuario123",
  "license": "CC-BY-NC",
  "original_url": "https://...",
  "download_timestamp": "2024-12-11T10:30:00",
  "file_size_bytes": 125000
}
```

## Ejemplo Completo

```python
from src.image_downloader import ImageDownloader
import json

# Cargar observaciones
with open('observations.json') as f:
    observations = json.load(f)

# Crear downloader
downloader = ImageDownloader(
    output_dir="./data/raw",
    max_workers=8,
    image_size="large",
    save_metadata=True
)

# Descargar
result = downloader.download_observations(observations)

print(f"Intentadas: {result['total_attempted']}")
print(f"Exitosas: {result['successful']}")
print(f"Fallidas: {result['failed']}")
print(f"Tamaño total: {result['total_size_bytes'] / 1024 / 1024:.1f} MB")

# Reintentar fallidas
if result['failed_ids']:
    failed_obs = [o for o in observations if o['id'] in result['failed_ids']]
    retry_result = downloader.download_observations(failed_obs)
```

## Manejo de Errores

### Reintentos Automáticos

El downloader reintenta con backoff exponencial:

```python
for attempt in range(max_retries):
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return True
    except Exception as e:
        wait_time = 2 ** attempt  # 1s, 2s, 4s
        time.sleep(wait_time)
```

### Errores Comunes

| Error | Causa | Manejo |
|-------|-------|--------|
| Timeout | Conexión lenta | Reintento automático |
| 403 Forbidden | Imagen no disponible | Se omite |
| 404 Not Found | URL inválida | Se omite |
| Imagen corrupta | Descarga incompleta | Reintento |

### Validación de Imágenes

Cada imagen descargada se valida:

```python
def _validate_image(self, path):
    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except Exception:
        return False
```

## Reanudación

El downloader detecta imágenes ya descargadas:

```python
# Si el archivo existe y es válido, se omite
if output_path.exists() and self._validate_image(output_path):
    return {'status': 'skipped'}
```

Esto permite reanudar descargas interrumpidas sin repetir trabajo.

## Consideraciones

### Espacio en Disco

Estima el espacio necesario:

| Tamaño | KB/imagen | 1000 imágenes |
|--------|-----------|---------------|
| `small` | 10-30 | 10-30 MB |
| `medium` | 30-80 | 30-80 MB |
| `large` | 100-300 | 100-300 MB |
| `original` | 500-5000 | 0.5-5 GB |

### Ancho de Banda

Ajusta `max_workers` según tu conexión:

| Conexión | Workers recomendados |
|----------|---------------------|
| Lenta (< 10 Mbps) | 2-4 |
| Media (10-50 Mbps) | 4-8 |
| Rápida (> 50 Mbps) | 8-16 |

### Licencias

Las imágenes de iNaturalist tienen diferentes licencias. El downloader guarda la licencia en los metadatos para referencia.

## Dependencias

- `requests`: Descargas HTTP
- `concurrent.futures`: Paralelismo
- `Pillow`: Validación de imágenes
- [`image_utils.py`](utils/image_utils.md): Utilidades de imagen
