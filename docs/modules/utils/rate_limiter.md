# Rate Limiter

Módulo: `src/utils/rate_limiter.py`

## Descripción

Implementa un controlador de tasa de llamadas thread-safe para respetar los límites de la API de iNaturalist y evitar errores 429 (Too Many Requests).

## Clase Principal

### `RateLimiter`

```python
from src.utils.rate_limiter import RateLimiter

limiter = RateLimiter(
    calls_per_period=60,
    period_seconds=60
)
```

#### Parámetros del Constructor

| Parámetro | Tipo | Descripción | Valor por defecto |
|-----------|------|-------------|-------------------|
| `calls_per_period` | int | Llamadas máximas por período | `60` |
| `period_seconds` | int | Duración del período en segundos | `60` |

## Métodos

### `wait_if_needed`

Espera si es necesario antes de realizar una llamada.

```python
limiter.wait_if_needed()
# Ahora es seguro hacer la llamada
response = requests.get(url)
```

Este método:
1. Verifica si se ha alcanzado el límite de llamadas
2. Si es así, espera hasta que se libere capacidad
3. Registra la llamada actual

### `get_stats`

Obtiene estadísticas del rate limiter.

```python
stats = limiter.get_stats()
```

#### Retorno

```python
{
    'calls_in_period': int,      # Llamadas en el período actual
    'calls_remaining': int,       # Llamadas disponibles
    'period_seconds': int,        # Duración del período
    'next_reset': float           # Segundos hasta reset
}
```

### `reset`

Reinicia el contador de llamadas.

```python
limiter.reset()
```

## Ejemplo Completo

```python
from src.utils.rate_limiter import RateLimiter
import requests

# Crear limiter: 60 llamadas por minuto
limiter = RateLimiter(calls_per_period=60, period_seconds=60)

urls = [f"https://api.example.com/item/{i}" for i in range(100)]

for url in urls:
    # Esperar si es necesario
    limiter.wait_if_needed()
    
    # Hacer llamada
    response = requests.get(url)
    
    # Mostrar estadísticas
    stats = limiter.get_stats()
    print(f"Llamadas restantes: {stats['calls_remaining']}")
```

## Thread Safety

El rate limiter es thread-safe y puede usarse con múltiples threads:

```python
from concurrent.futures import ThreadPoolExecutor

limiter = RateLimiter(calls_per_period=60, period_seconds=60)

def fetch_url(url):
    limiter.wait_if_needed()  # Thread-safe
    return requests.get(url)

with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(fetch_url, urls))
```

## Algoritmo

El rate limiter utiliza una ventana deslizante:

```python
def wait_if_needed(self):
    with self._lock:
        now = time.time()
        
        # Limpiar llamadas fuera del período
        self._calls = [t for t in self._calls if now - t < self.period_seconds]
        
        # Si alcanzamos el límite, esperar
        if len(self._calls) >= self.calls_per_period:
            oldest_call = self._calls[0]
            wait_time = self.period_seconds - (now - oldest_call)
            if wait_time > 0:
                time.sleep(wait_time)
        
        # Registrar esta llamada
        self._calls.append(time.time())
```

## Integración con API Client

El `iNaturalistAPIClient` utiliza internamente un `RateLimiter`:

```python
class iNaturalistAPIClient:
    def __init__(self, rate_limit_calls=60, rate_limit_period=60):
        self._rate_limiter = RateLimiter(
            calls_per_period=rate_limit_calls,
            period_seconds=rate_limit_period
        )
    
    def _make_request(self, url, params):
        self._rate_limiter.wait_if_needed()
        return requests.get(url, params=params)
```

## Consideraciones

### Límites de iNaturalist

La API de iNaturalist permite aproximadamente:
- 60 llamadas por minuto para usuarios no autenticados
- 100 llamadas por minuto para usuarios autenticados

### Backoff Exponencial

Para errores 429, el API client implementa backoff exponencial adicional:

```python
for attempt in range(max_retries):
    try:
        response = self._make_request(url, params)
        if response.status_code == 429:
            wait_time = 2 ** attempt * 10  # 10s, 20s, 40s
            time.sleep(wait_time)
            continue
        return response
    except Exception:
        pass
```
