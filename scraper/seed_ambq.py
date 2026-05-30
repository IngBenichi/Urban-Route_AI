"""
seed_ambq.py — Carga las rutas de resoluciones AMBQ en PostgreSQL
Lee: scraper/data/ambq/rutas_ambq.json
Inserta: filas en la tabla `routes` con campos AMBQ enriquecidos

Uso:
    python seed_ambq.py           → inserta/actualiza rutas AMBQ
    python seed_ambq.py --clear   → elimina solo las rutas de fuente=ambq_resolucion antes de insertar

Requiere que las migraciones estén aplicadas (incluida 0002_add_ambq_fields).
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

RUTAS_FILE = Path(__file__).parent / "data" / "ambq" / "rutas_ambq.json"

# Paleta de colores por empresa (cíclica si hay más de 22)
EMPRESA_COLORS = [
    "#6366F1", "#8B5CF6", "#A855F7", "#EC4899", "#F43F5E",
    "#EF4444", "#F97316", "#F59E0B", "#EAB308", "#84CC16",
    "#22C55E", "#10B981", "#14B8A6", "#06B6D4", "#0EA5E9",
    "#3B82F6", "#60A5FA", "#818CF8", "#C084FC", "#F472B6",
    "#FB7185", "#34D399",
]


def get_db_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    url = url.replace("postgresql+psycopg2://", "postgresql://")
    if not url.startswith("postgresql://"):
        url = os.environ.get(
            "SYNC_DATABASE_URL",
            "postgresql://urbanroute:changeme@localhost:5432/urbanroutedb",
        )
    return url.replace("postgresql+asyncpg://", "postgresql://").replace("postgresql+psycopg2://", "postgresql://")


async def seed(clear: bool = False):
    if not RUTAS_FILE.exists():
        print(f"❌ No se encontró {RUTAS_FILE}")
        print("   Ejecuta primero: python ambq_scraper.py --only-parse")
        sys.exit(1)

    with open(RUTAS_FILE, encoding="utf-8") as f:
        rutas = json.load(f)

    print(f"📋 {len(rutas)} rutas AMBQ cargadas desde JSON")

    db_url = get_db_url()
    print(f"Conectando a: {db_url[:45]}...")
    conn = await asyncpg.connect(db_url)

    try:
        if clear:
            await conn.execute(
                "DELETE FROM routes WHERE fuente = 'ambq_resolucion'"
            )
            print("🗑  Eliminadas rutas AMBQ existentes")

        # Asignar colores por empresa (consistente via índice)
        empresas_vistas: dict[str, str] = {}
        color_idx = 0

        insertadas = 0
        actualizadas = 0
        omitidas = 0

        for ruta in rutas:
            empresa = ruta.get("empresa", "")
            codigos = ruta.get("codigos", [])
            denominacion = ruta.get("denominacion", "").strip()
            recorrido = ruta.get("recorrido", "").strip()
            calles = ruta.get("calles", [])

            # Determinar código principal y nombre de la ruta
            codigo_principal = codigos[0] if codigos else None
            # Nombre: preferir denominación, sino empresa + código
            if denominacion:
                nombre = denominacion
            elif codigo_principal:
                nombre = f"{empresa} – {codigo_principal}"
            else:
                nombre = empresa or "Sin nombre"

            # Truncar nombre a 255 chars
            nombre = nombre[:255]

            # Color por empresa
            if empresa not in empresas_vistas:
                empresas_vistas[empresa] = EMPRESA_COLORS[color_idx % len(EMPRESA_COLORS)]
                color_idx += 1
            color = empresas_vistas[empresa]

            # Si no hay código, no podemos detectar duplicados fácilmente → usar pdf como clave
            clave_codigo = codigo_principal
            clave_pdf = ruta.get("pdf", "")

            # Verificar si ya existe (por código principal o pdf + empresa)
            existing_id = None
            if clave_codigo:
                existing_id = await conn.fetchval(
                    "SELECT id FROM routes WHERE code = $1 AND fuente = 'ambq_resolucion'",
                    clave_codigo,
                )
            if not existing_id and clave_pdf:
                existing_id = await conn.fetchval(
                    "SELECT id FROM routes WHERE empresa = $1 AND recorrido IS NOT NULL "
                    "AND name LIKE $2 AND fuente = 'ambq_resolucion'",
                    empresa,
                    f"%{clave_pdf[:30]}%",
                )

            if existing_id:
                # Actualizar registro existente
                await conn.execute(
                    """UPDATE routes
                       SET name=$1, code=$2, color=$3, empresa=$4,
                           recorrido=$5, calles=$6
                       WHERE id=$7""",
                    nombre, clave_codigo, color, empresa,
                    recorrido or None,
                    json.dumps(calles, ensure_ascii=False) if calles else None,
                    existing_id,
                )
                actualizadas += 1
            else:
                # Insertar nueva ruta
                await conn.execute(
                    """INSERT INTO routes (name, code, color, empresa, recorrido, calles, fuente)
                       VALUES ($1, $2, $3, $4, $5, $6, 'ambq_resolucion')""",
                    nombre, clave_codigo, color, empresa,
                    recorrido or None,
                    json.dumps(calles, ensure_ascii=False) if calles else None,
                )
                insertadas += 1

        print(f"\n✅ Resultado:")
        print(f"   Insertadas:   {insertadas}")
        print(f"   Actualizadas: {actualizadas}")
        print(f"   Empresas:     {len(empresas_vistas)}")

        # Verificar total de rutas AMBQ en DB
        total_ambq = await conn.fetchval(
            "SELECT count(*) FROM routes WHERE fuente = 'ambq_resolucion'"
        )
        total_all = await conn.fetchval("SELECT count(*) FROM routes")
        print(f"\n   Rutas AMBQ en DB: {total_ambq}")
        print(f"   Total rutas en DB: {total_all}")

    finally:
        await conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed AMBQ routes into PostgreSQL")
    parser.add_argument("--clear", action="store_true", help="Eliminar rutas AMBQ antes de insertar")
    args = parser.parse_args()

    asyncio.run(seed(clear=args.clear))
