# API Client

Módulo: `src/api_client.py`

## Descripción

Cliente para interactuar con la API v1 de iNaturalist. Implementa rate-limiting, caché local, reintentos automáticos y paginación.

## Clase Principal

### `iNaturalistAPIClient`

```python
from src.api_client import iNaturalistAPIClient

client = iNaturalistAPIClient(
    cache_dir="./data/cache",
    rate_limit_calls=60,
    rate_limit_period=60,
    max_retries=3,
    timeout=30,
    logger=None
)
```

#### Parámetros del Constructor

| Parámetro | Tipo | Descripción | Valor por defecto |
|-----------|------|-------------|-------------------|
| `cache_dir` | str | Directorio para caché local | `"./data/cache"` |
| `rate_limit_calls` | int | Llamadas máximas por período | `60` |
| `rate_limit_period` | int | Período en segundos | `60` |
| `max_retries` | int | Reintentos en caso de error | `3` |
| `timeout` | int | Timeout de conexión | `30` |
| `logger` | Logger | Logger opcional | `None` |

## Métodos

### `search_observations`

Busca observaciones con filtros específicos.

```python
observations = client.search_observations(
    taxon_id=12738,
    taxon_name=None,
    place_id=10422,
    quality_grade="research",
    geo=True,
    license=None,
    per_page=200,
    max_results=500,
    order_by="observed_on",
    order="desc"
)
```

#### Parámetros

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `taxon_id` | int | ID del taxón en iNaturalist |
| `taxon_name` | str | Nombre del taxón (alternativa a ID) |
| `place_id` | int | ID del lugar geográfico |
| `quality_grade` | str | `"research"`, `"needs_id"`, `"casual"` |
| `geo` | bool | Solo observaciones con coordenadas |
| `license` | str | Filtrar por licencia |
| `per_page` | int | Resultados por página (máx 200) |
| `max_results` | int | Máximo total de resultados |
| `order_by` | str | Campo de ordenamiento |
| `order` | str | `"asc"` o `"desc"` |

#### Retorno

Lista de diccionarios con la estructura de observación de iNaturalist.

### `get_observation`

Obtiene una observación específica por ID.

```python
observation = client.get_observation(observation_id=123456789)
```

### `get_taxon`

Obtiene información de un taxón.

```python
taxon = client.get_taxon(taxon_id=12738)
```

### `search_taxa`

Busca taxones por nombre.

```python
taxa = client.search_taxa(
    query="Turdus rufiventris",
    rank="species",
    limit=10
)
```

### `get_places`

Busca lugares por nombre.

```python
places = client.get_places(
    query="Misiones",
    limit=5
)
```

**Nota**: Utiliza el endpoint `/places/autocomplete`.

## Características

### Rate Limiting

El cliente respeta los límites de la API de iNaturalist:

```python
# Configuración por defecto: 60 llamadas por minuto
client = iNaturalistAPIClient(
    rate_limit_calls=60,
    rate_limit_period=60
)
```

El rate limiter es thread-safe y espera automáticamente cuando se alcanza el límite.

### Caché Local

Las respuestas se cachean localmente para evitar llamadas repetidas:

```python
client = iNaturalistAPIClient(cache_dir="./data/cache")

# Primera llamada: consulta la API
obs1 = client.search_observations(taxon_id=12738)

# Segunda llamada: usa caché
obs2 = client.search_observations(taxon_id=12738)
```

El caché tiene una antigüedad configurable (por defecto 7 días).

### Reintentos Automáticos

En caso de errores transitorios, el cliente reintenta con backoff exponencial:

```python
client = iNaturalistAPIClient(max_retries=3)
# Reintenta hasta 3 veces con esperas de 1s, 2s, 4s
```

### Paginación Automática

Para obtener más de 200 resultados, el cliente pagina automáticamente:

```python
# Obtiene hasta 1000 resultados paginando internamente
observations = client.search_observations(
    taxon_id=12738,
    max_results=1000,
    per_page=200
)
```

## Manejo de Errores

```python
from requests.exceptions import HTTPError

try:
    observations = client.search_observations(taxon_id=99999999)
except HTTPError as e:
    if e.response.status_code == 404:
        print("Taxón no encontrado")
    elif e.response.status_code == 422:
        print("Parámetros inválidos")
    elif e.response.status_code == 429:
        print("Rate limit excedido")
```

## Ejemplo Completo

```python
from src.api_client import iNaturalistAPIClient
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear cliente
client = iNaturalistAPIClient(
    cache_dir="./data/cache",
    logger=logger
)

# Buscar observaciones de Turdus rufiventris en Misiones
observations = client.search_observations(
    taxon_id=12738,
    place_id=10422,
    quality_grade="research",
    max_results=100
)

print(f"Obtenidas {len(observations)} observaciones")

# Procesar resultados
for obs in observations[:5]:
    taxon = obs.get('taxon', {})
    print(f"  {obs['id']}: {taxon.get('name')} - {obs.get('observed_on')}")
```

## Dependencias

- `requests`: Llamadas HTTP
- [`local_cache.py`](local_cache.md): Caché de respuestas
- [`rate_limiter.py`](utils/rate_limiter.md): Control de tasa

## API de iNaturalist

Documentación oficial: https://api.inaturalist.org/v1/docs/
