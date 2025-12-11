# Etapa 2: Descarga de Imágenes

Script: `scripts/02_download_images.py`

## Descripción

Esta etapa descarga las imágenes de las observaciones obtenidas en la etapa anterior, guardando tanto las imágenes como sus metadatos asociados.

## Uso

```bash
python scripts/02_download_images.py --config config/mi_config.yaml
```

### Argumentos

| Argumento | Descripción | Valor por defecto |
|-----------|-------------|-------------------|
| `--config` | Ruta al archivo de configuración YAML | `config/paraense_fauna.yaml` |
| `--workers` | Número de workers paralelos | Valor en config o 4 |

## Funcionamiento

1. **Carga de observaciones**: Lee el archivo `observations.json` generado en la etapa anterior
2. **Extracción de URLs**: Obtiene las URLs de las fotos de cada observación
3. **Descarga paralela**: Utiliza ThreadPoolExecutor para descargas concurrentes
4. **Validación**: Verifica la integridad de cada imagen descargada
5. **Metadatos**: Guarda un archivo JSON con información de cada imagen

## Parámetros de Configuración Relevantes

```yaml
download:
  max_workers: 4           # Workers paralelos
  image_size: "large"      # Tamaño: original, large, medium, small
  save_metadata: true      # Guardar JSON por imagen
  timeout: 30              # Timeout por descarga
```

## Salida

### Estructura de directorios

```
data/{dataset}/raw/
├── turdus_rufiventris/
│   ├── 123456789.jpg
│   ├── 123456789.json
│   ├── 123456790.jpg
│   └── 123456790.json
└── ramphastos_toco/
    ├── 987654321.jpg
    └── 987654321.json
```

### Metadatos por imagen

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
  "download_timestamp": "2024-12-11T10:30:00"
}
```

### Estadísticas

`data/{dataset}/cache/download_stats.json`

```json
{
  "total_attempted": 500,
  "successful": 485,
  "failed": 15,
  "by_species": {
    "Turdus rufiventris": 245,
    "Ramphastos toco": 240
  },
  "total_size_mb": 125.5,
  "download_time_seconds": 180.3
}
```

## Tamaños de Imagen

iNaturalist proporciona imágenes en diferentes tamaños:

| Tamaño | Dimensión aproximada | Uso recomendado |
|--------|---------------------|-----------------|
| `original` | Variable (hasta 4K) | Máxima calidad, más espacio |
| `large` | 1024px lado mayor | Balance calidad/tamaño |
| `medium` | 500px lado mayor | Previsualizaciones |
| `small` | 240px lado mayor | Thumbnails |

Para entrenamiento de modelos, se recomienda `large` u `original`.

## Manejo de Errores

El descargador implementa:

- **Reintentos automáticos**: 3 intentos por imagen con backoff exponencial
- **Timeout configurable**: Evita bloqueos en conexiones lentas
- **Validación de imagen**: Verifica que el archivo sea una imagen válida
- **Registro de fallos**: Guarda lista de descargas fallidas para reintentar

### Errores comunes

| Error | Causa | Solución |
|-------|-------|----------|
| Timeout | Conexión lenta | Aumentar timeout o reducir workers |
| 403 Forbidden | Imagen no disponible | Se omite automáticamente |
| Imagen corrupta | Descarga incompleta | Reintento automático |

## Consideraciones

### Espacio en Disco

Estima el espacio necesario antes de ejecutar:
- Imágenes `large`: ~100-300 KB por imagen
- Imágenes `original`: ~500 KB - 5 MB por imagen

Para 1000 imágenes en tamaño `large`: ~150-300 MB

### Ancho de Banda

La descarga paralela puede saturar conexiones lentas. Ajustar `max_workers` según la conexión disponible:
- Conexión lenta: 2-4 workers
- Conexión rápida: 8-16 workers

### Reanudación

Si la descarga se interrumpe, el script detecta imágenes ya descargadas y las omite en ejecuciones posteriores.

## Módulos Utilizados

- [`image_downloader.py`](../modules/image_downloader.md) - Lógica de descarga
- [`image_utils.py`](../modules/utils/image_utils.md) - Validación de imágenes

## Siguiente Etapa

Una vez descargadas las imágenes, proceder a [Etapa 3: Deduplicación](03_deduplicate.md).
