# Etapa 1: Obtención de Observaciones

Script: `scripts/01_fetch_observations.py`

## Descripción

Esta etapa consulta la API de iNaturalist para obtener observaciones de las especies configuradas en la región geográfica especificada.

## Uso

```bash
python scripts/01_fetch_observations.py --config config/mi_config.yaml
```

### Argumentos

| Argumento | Descripción | Valor por defecto |
|-----------|-------------|-------------------|
| `--config` | Ruta al archivo de configuración YAML | `config/paraense_fauna.yaml` |

## Funcionamiento

1. **Carga de configuración**: Lee el archivo YAML con parámetros de geografía y especies
2. **Inicialización del cliente API**: Configura rate-limiting y caché local
3. **Iteración por especies**: Para cada taxón configurado:
   - Construye la consulta con filtros geográficos y de calidad
   - Pagina automáticamente hasta obtener el máximo de observaciones
   - Respeta los límites de tasa de la API
4. **Almacenamiento**: Guarda todas las observaciones en un archivo JSON

## Parámetros de Configuración Relevantes

```yaml
geography:
  place_id: 10422          # ID del lugar en iNaturalist
  
fauna:
  taxa:
    - name: "Especie"
      taxon_id: 12345
      max_observations: 500

api:
  quality_grade: "research"  # Solo observaciones verificadas
  rate_limit_calls: 60
  rate_limit_period: 60
```

## Salida

### Archivo principal

`data/{dataset}/cache/observations.json`

Contiene un array de observaciones con la estructura de respuesta de iNaturalist:

```json
[
  {
    "id": 123456789,
    "observed_on": "2024-01-15",
    "taxon": {
      "id": 12738,
      "name": "Turdus rufiventris",
      "rank": "species"
    },
    "geojson": {
      "type": "Point",
      "coordinates": [-54.45, -25.68]
    },
    "photos": [
      {
        "id": 987654,
        "url": "https://inaturalist-open-data.s3.amazonaws.com/..."
      }
    ],
    "quality_grade": "research",
    "user": {
      "login": "usuario123"
    }
  }
]
```

### Estadísticas

`data/{dataset}/cache/fetch_stats.json`

```json
{
  "total_observations": 500,
  "by_species": {
    "12738": {"name": "Turdus rufiventris", "count": 250},
    "18793": {"name": "Ramphastos toco", "count": 250}
  },
  "fetch_time_seconds": 45.2
}
```

## Consideraciones

### Rate Limiting

La API de iNaturalist tiene límites de tasa. El cliente implementa:
- Espera automática entre llamadas
- Reintentos con backoff exponencial en caso de error 429
- Caché local para evitar llamadas repetidas

### Calidad de Datos

Se recomienda usar `quality_grade: "research"` para obtener observaciones:
- Verificadas por la comunidad
- Con identificación a nivel de especie
- Con coordenadas geográficas
- Con al menos una foto

### Verificación de IDs

Antes de ejecutar, verificar que los IDs sean correctos:

```bash
# Verificar place_id
curl "https://api.inaturalist.org/v1/places/autocomplete?q=Misiones"

# Verificar taxon_id
curl "https://api.inaturalist.org/v1/taxa?q=Turdus+rufiventris&rank=species"
```

## Errores Comunes

| Error | Causa | Solución |
|-------|-------|----------|
| 404 Not Found | `place_id` inválido | Verificar ID en la API |
| 422 Unprocessable Entity | Parámetros inválidos | Revisar configuración |
| 429 Too Many Requests | Rate limit excedido | Esperar o reducir llamadas |
| 0 observaciones | Filtros muy restrictivos | Ampliar región o relajar filtros |

## Módulos Utilizados

- [`api_client.py`](../modules/api_client.md) - Cliente de la API
- [`local_cache.py`](../modules/local_cache.md) - Caché de respuestas
- [`rate_limiter.py`](../modules/utils/rate_limiter.md) - Control de tasa

## Siguiente Etapa

Una vez obtenidas las observaciones, proceder a [Etapa 2: Descarga de Imágenes](02_download_images.md).
