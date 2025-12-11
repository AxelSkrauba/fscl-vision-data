# Local Cache

Módulo: `src/local_cache.py`

## Descripción

Implementa un sistema de caché local en disco para almacenar respuestas de API, evitando llamadas repetidas y mejorando el rendimiento del pipeline.

## Clase Principal

### `LocalCache`

```python
from src.local_cache import LocalCache

cache = LocalCache(
    cache_dir="./data/cache",
    max_age_days=7,
    logger=None
)
```

#### Parámetros del Constructor

| Parámetro | Tipo | Descripción | Valor por defecto |
|-----------|------|-------------|-------------------|
| `cache_dir` | str/Path | Directorio de caché | `"./data/cache"` |
| `max_age_days` | int | Antigüedad máxima en días | `7` |
| `logger` | Logger | Logger opcional | `None` |

## Métodos

### `set`

Almacena un valor en el caché.

```python
cache.set(key="observations_12738", value=observations_data)
```

#### Parámetros

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `key` | str | Clave única para el valor |
| `value` | Any | Valor a almacenar (serializable a JSON) |

### `get`

Recupera un valor del caché.

```python
value = cache.get(key="observations_12738", default=None)
```

#### Parámetros

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `key` | str | Clave del valor |
| `default` | Any | Valor por defecto si no existe |

#### Retorno

El valor almacenado o `default` si no existe o está expirado.

### `exists`

Verifica si una clave existe y no está expirada.

```python
if cache.exists("observations_12738"):
    data = cache.get("observations_12738")
```

### `delete`

Elimina una entrada del caché.

```python
cache.delete("observations_12738")
```

### `clear`

Elimina todas las entradas del caché.

```python
cache.clear()
```

### `cleanup`

Elimina entradas expiradas.

```python
removed_count = cache.cleanup()
```

### `get_stats`

Obtiene estadísticas del caché.

```python
stats = cache.get_stats()
```

#### Retorno

```python
{
    'total_entries': int,
    'total_size_bytes': int,
    'oldest_entry': datetime,
    'newest_entry': datetime,
    'expired_entries': int
}
```

## Estructura de Almacenamiento

```
cache/
├── observations_12738.json
├── observations_18793.json
├── taxa_12738.json
└── _cache_metadata.json
```

Cada archivo contiene:

```json
{
  "key": "observations_12738",
  "created_at": "2024-12-11T10:30:00",
  "expires_at": "2024-12-18T10:30:00",
  "data": {...}
}
```

## Ejemplo Completo

```python
from src.local_cache import LocalCache

# Crear caché
cache = LocalCache(
    cache_dir="./data/cache",
    max_age_days=7
)

# Verificar si existe
key = "observations_taxon_12738_place_10422"
if cache.exists(key):
    # Usar caché
    observations = cache.get(key)
    print(f"Usando caché: {len(observations)} observaciones")
else:
    # Obtener de API
    observations = api_client.search_observations(...)
    # Guardar en caché
    cache.set(key, observations)
    print(f"Guardado en caché: {len(observations)} observaciones")

# Estadísticas
stats = cache.get_stats()
print(f"Entradas: {stats['total_entries']}")
print(f"Tamaño: {stats['total_size_bytes'] / 1024:.1f} KB")

# Limpiar expirados
removed = cache.cleanup()
print(f"Eliminadas {removed} entradas expiradas")
```

## Generación de Claves

El API client genera claves únicas basadas en los parámetros de la consulta:

```python
def _generate_cache_key(self, endpoint, params):
    # Ordenar parámetros para consistencia
    sorted_params = sorted(params.items())
    params_str = "&".join(f"{k}={v}" for k, v in sorted_params)
    
    # Hash para claves largas
    key = f"{endpoint}_{params_str}"
    if len(key) > 200:
        key = f"{endpoint}_{hashlib.md5(params_str.encode()).hexdigest()}"
    
    return key
```

## Consideraciones

### Invalidación

El caché se invalida automáticamente después de `max_age_days`. Para forzar actualización:

```python
# Eliminar entrada específica
cache.delete("observations_12738")

# O limpiar todo
cache.clear()
```

### Espacio en Disco

El caché puede crecer significativamente. Ejecuta `cleanup()` periódicamente:

```python
# Limpiar expirados
cache.cleanup()

# O establecer max_age_days más corto
cache = LocalCache(max_age_days=3)
```

### Thread Safety

El caché es thread-safe para operaciones básicas mediante locks de archivo.

### Serialización

Solo se pueden cachear valores serializables a JSON:
- Diccionarios
- Listas
- Strings, números, booleanos
- None

Objetos complejos deben convertirse primero.

## Dependencias

- `json`: Serialización
- `pathlib`: Manejo de rutas
- `datetime`: Control de expiración
