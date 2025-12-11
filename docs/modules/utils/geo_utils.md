# Geo Utils

Módulo: `src/utils/geo_utils.py`

## Descripción

Proporciona utilidades geográficas para cálculos de distancia, validación de coordenadas y manejo de bounding boxes.

## Clases y Funciones

### `GeoUtils`

Clase con métodos estáticos para operaciones geográficas.

```python
from src.utils.geo_utils import GeoUtils
```

#### Métodos

##### `haversine_distance`

Calcula la distancia entre dos puntos geográficos usando la fórmula de Haversine.

```python
distance_km = GeoUtils.haversine_distance(
    lat1=-25.68, lon1=-54.45,
    lat2=-25.70, lon2=-54.50
)
```

**Parámetros:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `lat1` | float | Latitud del punto 1 |
| `lon1` | float | Longitud del punto 1 |
| `lat2` | float | Latitud del punto 2 |
| `lon2` | float | Longitud del punto 2 |

**Retorno:** Distancia en kilómetros.

##### `validate_coordinates`

Valida que las coordenadas estén en rangos válidos.

```python
is_valid = GeoUtils.validate_coordinates(lat=-25.68, lon=-54.45)
```

**Rangos válidos:**
- Latitud: -90 a 90
- Longitud: -180 a 180

##### `degrees_to_meters`

Convierte grados a metros aproximados.

```python
meters = GeoUtils.degrees_to_meters(degrees=0.001, latitude=-25.68)
```

**Nota:** La conversión depende de la latitud debido a la curvatura de la Tierra.

##### `create_bounding_box`

Crea un bounding box alrededor de un punto central.

```python
bbox = GeoUtils.create_bounding_box(
    center_lat=-25.68,
    center_lon=-54.45,
    radius_km=10
)
```

### `BoundingBox`

Clase para representar y operar con bounding boxes geográficos.

```python
from src.utils.geo_utils import BoundingBox

bbox = BoundingBox(
    north=-25.0,
    south=-28.0,
    east=-53.5,
    west=-56.0
)
```

#### Parámetros del Constructor

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `north` | float | Latitud norte (máxima) |
| `south` | float | Latitud sur (mínima) |
| `east` | float | Longitud este (máxima) |
| `west` | float | Longitud oeste (mínima) |

#### Métodos

##### `contains`

Verifica si un punto está dentro del bounding box.

```python
is_inside = bbox.contains(lat=-25.68, lon=-54.45)
```

##### `to_inaturalist_format`

Convierte a formato de iNaturalist (swlat,swlng,nelat,nelng).

```python
format_str = bbox.to_inaturalist_format()
# "-28.0,-56.0,-25.0,-53.5"
```

##### `area_km2`

Calcula el área aproximada en kilómetros cuadrados.

```python
area = bbox.area_km2()
```

##### `center`

Obtiene el punto central del bounding box.

```python
center_lat, center_lon = bbox.center()
```

## Ejemplo Completo

```python
from src.utils.geo_utils import GeoUtils, BoundingBox

# Calcular distancia entre dos observaciones
obs1 = {"latitude": -25.68, "longitude": -54.45}
obs2 = {"latitude": -25.70, "longitude": -54.50}

distance = GeoUtils.haversine_distance(
    obs1["latitude"], obs1["longitude"],
    obs2["latitude"], obs2["longitude"]
)
print(f"Distancia: {distance:.2f} km")

# Crear bounding box para Misiones
misiones_bbox = BoundingBox(
    north=-25.0,
    south=-28.0,
    east=-53.5,
    west=-56.0
)

# Verificar si una observación está en Misiones
if misiones_bbox.contains(-25.68, -54.45):
    print("Observación dentro de Misiones")

# Formato para API de iNaturalist
print(f"Bounding box: {misiones_bbox.to_inaturalist_format()}")

# Área de la región
print(f"Área: {misiones_bbox.area_km2():.0f} km²")
```

## Fórmula de Haversine

La distancia se calcula usando:

```python
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Radio de la Tierra en km
    
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    return R * c
```

## Consideraciones

### Precisión

- La fórmula de Haversine asume una Tierra esférica
- Error típico: < 0.3% para distancias cortas
- Para mayor precisión, usar fórmula de Vincenty

### Coordenadas

- Latitud positiva = Norte, negativa = Sur
- Longitud positiva = Este, negativa = Oeste
- Argentina está en latitudes negativas y longitudes negativas
