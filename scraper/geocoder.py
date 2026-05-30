"""
geocoder.py — Geocodifica las paradas únicas usando Nominatim (OpenStreetMap)
Lee: scraper/data/routes_raw.json
Genera: scraper/data/stops_geocoded.json

Uso:
    python geocoder.py

Respeta el límite de 1 req/s de Nominatim.
Las paradas que no se puedan geocodificar quedan con lat/lon = null.
"""

import json
import time
from pathlib import Path
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

INPUT_FILE = Path(__file__).parent / "data" / "routes_raw.json"
OUTPUT_FILE = Path(__file__).parent / "data" / "stops_geocoded.json"

# Barranquilla bounding box para validar resultados (lat 10.8–11.1, lon -74.95–-74.6)
BARRANQUILLA_LAT_MIN = 10.75
BARRANQUILLA_LAT_MAX = 11.15
BARRANQUILLA_LON_MIN = -75.05
BARRANQUILLA_LON_MAX = -74.55
GEOCODE_DELAY = 1.1  # segundos entre requests (Nominatim policy: 1 req/s)


def normalize_stop_name(name: str) -> str:
    """Normaliza el nombre de una parada para usarla como clave de caché."""
    return name.strip().upper()


def build_geocode_query(stop_name: str) -> str:
    """Construye la query de geocodificación añadiendo contexto de Barranquilla."""
    # Limpiar prefijos redundantes
    clean = stop_name.strip()
    return f"{clean}, Barranquilla, Colombia"


def is_in_barranquilla(lat: float, lon: float) -> bool:
    """Verifica que las coordenadas estén dentro del área metropolitana de Barranquilla."""
    return (
        BARRANQUILLA_LAT_MIN <= lat <= BARRANQUILLA_LAT_MAX
        and BARRANQUILLA_LON_MIN <= lon <= BARRANQUILLA_LON_MAX
    )


def geocode_stop(geolocator: Nominatim, stop_name: str) -> dict | None:
    """Intenta geocodificar una parada. Retorna dict con lat/lon o None si falla."""
    query = build_geocode_query(stop_name)

    # Intentar hasta 2 veces
    for attempt in range(2):
        try:
            location = geolocator.geocode(
                query,
                exactly_one=True,
                timeout=10,
                language="es",
            )
            if location:
                lat, lon = location.latitude, location.longitude
                if is_in_barranquilla(lat, lon):
                    return {"lat": lat, "lon": lon, "address": location.address}
                else:
                    # Resultado fuera de Barranquilla — intentar sin país
                    return None
            return None
        except GeocoderTimedOut:
            if attempt == 0:
                time.sleep(2)
            continue
        except GeocoderServiceError:
            return None

    return None


def main():
    if not INPUT_FILE.exists():
        print(f"❌ Archivo no encontrado: {INPUT_FILE}")
        print("   Ejecuta primero: python scraper.py")
        return

    with open(INPUT_FILE, encoding="utf-8") as f:
        routes = json.load(f)

    # Recolectar paradas únicas
    unique_stops: set[str] = set()
    for route in routes:
        for stop in route.get("stops_raw", []):
            normalized = normalize_stop_name(stop)
            if normalized:
                unique_stops.add(normalized)

    print(f"Paradas únicas a geocodificar: {len(unique_stops)}")
    estimated_minutes = (len(unique_stops) * GEOCODE_DELAY) / 60
    print(f"Tiempo estimado: ~{estimated_minutes:.1f} minutos")

    geolocator = Nominatim(user_agent="UrbanRouteAI/1.0 (barranquilla-bus-research)")

    # Cargar caché existente si hay
    geocoded: dict[str, dict | None] = {}
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            geocoded = json.load(f)
        cached = sum(1 for v in geocoded.values() if v is not None)
        print(f"Caché cargada: {len(geocoded)} paradas, {cached} con coordenadas")

    stops_list = sorted(unique_stops - set(geocoded.keys()))
    total = len(stops_list)

    for i, stop_name in enumerate(stops_list, 1):
        result = geocode_stop(geolocator, stop_name)
        geocoded[stop_name] = result

        status = f"✓ {result['lat']:.4f},{result['lon']:.4f}" if result else "✗ sin resultado"
        print(f"[{i}/{total}] {stop_name[:50]:<50} {status}")

        # Guardar progreso cada 20 paradas
        if i % 20 == 0:
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(geocoded, f, ensure_ascii=False, indent=2)

        time.sleep(GEOCODE_DELAY)

    # Guardar resultado final
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(geocoded, f, ensure_ascii=False, indent=2)

    success = sum(1 for v in geocoded.values() if v is not None)
    total_all = len(geocoded)
    print(f"\n✅ Geocodificación completa:")
    print(f"   {success}/{total_all} paradas geocodificadas ({success/total_all*100:.1f}%)")
    print(f"   Guardado en: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
