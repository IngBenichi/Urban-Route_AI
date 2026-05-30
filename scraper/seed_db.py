"""
seed_db.py — Carga los datos scrapeados en PostgreSQL
Lee: scraper/data/routes_raw.json + scraper/data/stops_geocoded.json
Inserta: routes, stops y route_stops en la base de datos

Uso:
    python seed_db.py [--clear]  (--clear elimina datos existentes)

Requiere que la DB esté corriendo y las migraciones aplicadas.
Configura DATABASE_URL en .env o en variable de entorno.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

import asyncpg
from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).parent.parent / ".env")

ROUTES_FILE = Path(__file__).parent / "data" / "routes_raw.json"
GEOCODED_FILE = Path(__file__).parent / "data" / "stops_geocoded.json"

# Colores asignados cíclicamente a las rutas
ROUTE_COLORS = [
    "#3B82F6", "#EF4444", "#10B981", "#F59E0B", "#8B5CF6",
    "#EC4899", "#14B8A6", "#F97316", "#6366F1", "#84CC16",
    "#06B6D4", "#A855F7", "#F43F5E", "#22C55E", "#EAB308",
]


def get_db_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    # Reemplazar asyncpg por psycopg (seed usa asyncpg directamente)
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    if not url.startswith("postgresql://"):
        url = os.environ.get("SYNC_DATABASE_URL", "postgresql://urbanroute:changeme@localhost:5432/urbanroutedb")
    return url.replace("postgresql+asyncpg://", "postgresql://")


def normalize(name: str) -> str:
    return name.strip().upper()


async def seed(clear: bool = False):
    if not ROUTES_FILE.exists():
        print(f"❌ No se encontró {ROUTES_FILE}")
        print("   Ejecuta primero: python scraper.py")
        sys.exit(1)

    if not GEOCODED_FILE.exists():
        print(f"⚠  No se encontró {GEOCODED_FILE} — los stops se cargarán sin coordenadas")
        geocoded: dict = {}
    else:
        with open(GEOCODED_FILE, encoding="utf-8") as f:
            geocoded = json.load(f)

    with open(ROUTES_FILE, encoding="utf-8") as f:
        routes_data = json.load(f)

    db_url = get_db_url()
    print(f"Conectando a: {db_url[:40]}...")
    conn = await asyncpg.connect(db_url)

    try:
        if clear:
            print("Limpiando datos existentes...")
            await conn.execute("TRUNCATE route_stops, stops, routes, user_queries RESTART IDENTITY CASCADE")

        # ── Paso 1: Recolectar todos los stops únicos ──────────────────────────
        stop_name_to_id: dict[str, int] = {}

        all_stop_names: set[str] = set()
        for route in routes_data:
            for stop_name in route.get("stops_raw", []):
                all_stop_names.add(normalize(stop_name))

        print(f"\nInsertando {len(all_stop_names)} paradas únicas...")
        for stop_name in sorted(all_stop_names):
            coords = geocoded.get(stop_name, None)
            lat = coords["lat"] if coords else None
            lon = coords["lon"] if coords else None

            # Usar INSERT ... ON CONFLICT para idempotencia
            row = await conn.fetchrow(
                """
                INSERT INTO stops (name, lat, lon)
                VALUES ($1, $2, $3)
                ON CONFLICT DO NOTHING
                RETURNING id
                """,
                stop_name, lat, lon,
            )
            if row:
                stop_name_to_id[stop_name] = row["id"]
            else:
                # Si ya existe, obtener el ID
                existing = await conn.fetchrow("SELECT id FROM stops WHERE name = $1", stop_name)
                if existing:
                    stop_name_to_id[stop_name] = existing["id"]

        print(f"✓ {len(stop_name_to_id)} paradas procesadas")

        # ── Paso 2: Insertar rutas y route_stops ──────────────────────────────
        print(f"\nInsertando {len(routes_data)} rutas...")
        routes_inserted = 0
        for i, route in enumerate(routes_data):
            stops_raw = route.get("stops_raw", [])
            if not stops_raw:
                continue

            color = ROUTE_COLORS[i % len(ROUTE_COLORS)]
            row = await conn.fetchrow(
                "INSERT INTO routes (name, color) VALUES ($1, $2) RETURNING id",
                route["name"], color,
            )
            route_id = row["id"]
            routes_inserted += 1

            # Insertar route_stops
            for order_idx, stop_name in enumerate(stops_raw):
                stop_id = stop_name_to_id.get(normalize(stop_name))
                if stop_id:
                    await conn.execute(
                        """
                        INSERT INTO route_stops (route_id, stop_id, order_index)
                        VALUES ($1, $2, $3)
                        ON CONFLICT ON CONSTRAINT uq_route_stop_order DO NOTHING
                        """,
                        route_id, stop_id, order_idx,
                    )

            if routes_inserted % 10 == 0:
                print(f"  {routes_inserted} rutas insertadas...")

        print(f"\n✅ Seed completo:")
        print(f"   Rutas: {routes_inserted}")
        print(f"   Paradas únicas: {len(stop_name_to_id)}")

    finally:
        await conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Carga datos de rutas en la DB")
    parser.add_argument("--clear", action="store_true", help="Limpiar datos existentes antes de cargar")
    args = parser.parse_args()
    asyncio.run(seed(clear=args.clear))
