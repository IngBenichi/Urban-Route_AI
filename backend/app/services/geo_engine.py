import math
from typing import Optional


EARTH_RADIUS_KM = 6371.0


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula la distancia en km entre dos puntos geográficos usando Haversine."""
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return EARTH_RADIUS_KM * c


def estimated_time_min(distance_km: float, speed_kmh: float = 20.0) -> int:
    """Tiempo estimado de viaje en minutos dado una distancia y velocidad promedio."""
    if speed_kmh <= 0:
        return 0
    return max(1, round((distance_km / speed_kmh) * 60))


def route_distance_km(stops: list) -> float:
    """Suma la distancia total de una secuencia de paraderos con coordenadas."""
    total = 0.0
    coords = [(s.lat, s.lon) for s in stops if s.lat is not None and s.lon is not None]
    for i in range(len(coords) - 1):
        total += haversine(coords[i][0], coords[i][1], coords[i + 1][0], coords[i + 1][1])
    return round(total, 2)


def stops_within_radius(
    center_lat: float,
    center_lon: float,
    stops: list,
    radius_km: float = 0.5,
) -> list:
    """Retorna los paraderos dentro de un radio dado de un punto central."""
    return [
        s for s in stops
        if s.lat is not None and s.lon is not None
        and haversine(center_lat, center_lon, s.lat, s.lon) <= radius_km
    ]
