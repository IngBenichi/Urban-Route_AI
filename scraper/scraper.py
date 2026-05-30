"""
scraper.py — Extrae rutas de https://lasrutasdebarranquilla.wordpress.com
Genera: scraper/data/routes_raw.json

Uso:
    python scraper.py

Salida (routes_raw.json):
[
  {
    "name": "COOASOATLÁN CALLE 72 TCHERASSI",
    "url": "https://...",
    "stops_raw": ["NEVADA CIUDAD SALITRE", "Calle 66", ...]
  },
  ...
]
"""

import asyncio
import json
import re
import time
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

BASE_URL = "https://lasrutasdebarranquilla.wordpress.com"
OUTPUT_FILE = Path(__file__).parent / "data" / "routes_raw.json"
DELAY_SECONDS = 1.5  # Cortesía con el servidor WordPress


def parse_recorrido(text: str) -> list[str]:
    """
    Divide el texto del recorrido en paradas individuales.
    Toma solo el tramo de IDA (antes de que el texto repita el punto inicial).
    """
    # Separar por " – " (guión largo con espacios) o " - " (guión corto)
    raw = re.split(r"\s+[–\-]\s+", text.strip())
    stops = [s.strip() for s in raw if s.strip()]

    if len(stops) < 2:
        return stops

    # Detectar punto de retorno: el primer stop suele repetirse al final
    first_stop_normalized = stops[0].upper()
    halfway = len(stops) // 2

    for i in range(halfway, len(stops)):
        if stops[i].upper() == first_stop_normalized:
            return stops[:i]  # Solo la ida

    # Si no se detecta retorno, retornar la primera mitad
    return stops[: (len(stops) // 2) + 1]


async def fetch_page(client: httpx.AsyncClient, url: str) -> str:
    """Descarga una página y retorna su HTML."""
    resp = await client.get(url, timeout=20.0)
    resp.raise_for_status()
    return resp.text


def extract_route_links(html: str) -> list[dict]:
    """Extrae todos los links de rutas del sidebar de la página principal."""
    soup = BeautifulSoup(html, "html.parser")
    routes = []

    # Los links de rutas están en el widget del sidebar (h3 "RUTAS DE BUSES")
    # WordPress usa <aside class="widget ..."> o <div class="widget ...">
    for widget in soup.find_all(["div", "aside"], class_="widget"):
        heading = widget.find(["h2", "h3", "h4"])
        if heading and "RUTAS" in heading.get_text(strip=True).upper():
            for a_tag in widget.find_all("a", href=True):
                href = a_tag["href"]
                name = a_tag.get_text(strip=True)
                if name and href.startswith(BASE_URL) and href != BASE_URL:
                    routes.append({"name": name, "url": href})

    # Deduplicar por URL
    seen = set()
    unique = []
    for r in routes:
        if r["url"] not in seen:
            seen.add(r["url"])
            unique.append(r)

    return unique


def extract_recorrido(html: str) -> str | None:
    """Extrae el texto del RECORRIDO de la página de una ruta."""
    soup = BeautifulSoup(html, "html.parser")
    content = soup.find("div", class_="entry-content") or soup.find("div", class_="post-content")

    if not content:
        # Fallback: buscar el cuerpo principal del post
        content = soup.find("article") or soup.find("main")

    if not content:
        return None

    full_text = content.get_text(separator="\n", strip=True)

    # Buscar la sección que dice RECORRIDO
    lines = full_text.split("\n")
    recorrido_start = None
    for i, line in enumerate(lines):
        if "RECORRIDO" in line.upper():
            recorrido_start = i + 1
            break

    if recorrido_start is None:
        return None

    # Tomar las líneas siguientes hasta encontrar una sección nueva o fin
    recorrido_lines = []
    for line in lines[recorrido_start:]:
        stripped = line.strip()
        if not stripped:
            continue
        # Parar si encontramos otra sección de encabezado
        if stripped.upper() in ("COMPARTE ESTO:", "NOS HAN VISITADO", "RUTAS DE BUSES", "ENTRADAS ANTERIORES"):
            break
        if stripped.startswith("Compartir en") or stripped.startswith("Suscribirse"):
            break
        recorrido_lines.append(stripped)

    return " ".join(recorrido_lines)


async def scrape_routes() -> list[dict]:
    headers = {
        "User-Agent": "UrbanRouteAI/1.0 (research project; contact: urban-route-ai@localhost)"
    }
    OUTPUT_FILE.parent.mkdir(exist_ok=True)

    # Continuar desde donde se dejó si ya existe el archivo
    results = []
    done_urls: set[str] = set()
    if OUTPUT_FILE.exists() and OUTPUT_FILE.stat().st_size > 2:
        try:
            with open(OUTPUT_FILE, encoding="utf-8") as f:
                results = json.load(f)
            done_urls = {r["url"] for r in results}
            print(f"↩ Retomando desde {len(results)} rutas ya guardadas.")
        except Exception:
            results = []

    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        print("Descargando página principal...")
        main_html = await fetch_page(client, BASE_URL)
        route_links = extract_route_links(main_html)
        print(f"Se encontraron {len(route_links)} rutas en el sidebar.")

        results_map = {r["url"]: r for r in results}

        for i, route in enumerate(route_links, 1):
            if route["url"] in done_urls:
                print(f"[{i}/{len(route_links)}] ✓ Ya procesada: {route['name']}")
                continue
            print(f"[{i}/{len(route_links)}] Scrapeando: {route['name']}")
            try:
                html = await fetch_page(client, route["url"])
                recorrido_text = extract_recorrido(html)

                if recorrido_text:
                    stops = parse_recorrido(recorrido_text)
                    entry = {
                        "name": route["name"],
                        "url": route["url"],
                        "stops_raw": stops,
                        "recorrido_text": recorrido_text,
                    }
                    print(f"  → {len(stops)} paradas extraídas")
                else:
                    print(f"  ⚠ No se encontró RECORRIDO en esta página")
                    entry = {
                        "name": route["name"],
                        "url": route["url"],
                        "stops_raw": [],
                        "recorrido_text": "",
                    }
            except Exception as exc:
                print(f"  ✗ Error: {exc}")
                entry = {
                    "name": route["name"],
                    "url": route["url"],
                    "stops_raw": [],
                    "recorrido_text": "",
                    "error": str(exc),
                }

            results_map[route["url"]] = entry
            # Guardar progreso después de cada ruta
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(list(results_map.values()), f, ensure_ascii=False, indent=2)

            if i < len(route_links):
                time.sleep(DELAY_SECONDS)

    return list(results_map.values())


def main():
    OUTPUT_FILE.parent.mkdir(exist_ok=True)

    routes = asyncio.run(scrape_routes())

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(routes, f, ensure_ascii=False, indent=2)

    total_stops = sum(len(r["stops_raw"]) for r in routes)
    routes_with_stops = sum(1 for r in routes if r["stops_raw"])
    print(f"\n✅ Scraping completo:")
    print(f"   Rutas: {len(routes)} total, {routes_with_stops} con paradas")
    print(f"   Paradas totales (con repetición): {total_stops}")
    print(f"   Guardado en: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
