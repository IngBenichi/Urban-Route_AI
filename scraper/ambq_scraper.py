"""
Scraper AMBQ — Área Metropolitana de Barranquilla
Extrae links de PDFs de resoluciones de rutas para todas las empresas
y descarga + analiza cada PDF buscando nombres de paradas y rutas.

Uso:
    uv run python ambq_scraper.py                   # scrape + descarga + parse
    uv run python ambq_scraper.py --only-index      # solo obtener índice de PDFs
    uv run python ambq_scraper.py --only-parse      # solo parsear PDFs ya descargados
"""

import argparse
import json
import re
import time
from pathlib import Path

import httpx
import pdfplumber

# ── Configuración ────────────────────────────────────────────────────────────

BASE_URL = "https://www.ambq.gov.co/transporte/transporte-publico-colectivo"

COMPANIES = [
    ("COOTRAB",        "resoluciones-cootrab"),
    ("TRANSMECAR",     "resoluciones-transmecar"),
    ("FLOTA ROJA",     "resoluciones-flota-roja"),
    ("TRANSDIAZ",      "resoluciones-transdiaz"),
    ("EMBUSA",         "resoluciones-embusa"),
    ("MONTERREY",      "resoluciones-monterrey"),
    ("LA CAROLINA",    "resoluciones-la-carolina"),
    ("COOTRANSPORCAR", "resoluciones-cootransporcar"),
    ("COOCHOFAL",      "resoluciones-coochofal"),
    ("TRASALFA",       "resoluciones-trasalfa"),
    ("COOLITORAL",     "resoluciones-coolitoral"),
    ("COOTRANTICO",    "resoluciones-cootrantico"),
    ("LOLAYA",         "resoluciones-lolaya"),
    ("COOTRANSCO",     "resoluciones-cootransco"),
    ("COOTRASOL",      "resoluciones-cootrasol"),
    ("SOBUSA",         "resoluciones-sobusa"),
    ("TRANSOLEDAD",    "resoluciones-transoledad"),
    ("TRANSURBAR",     "resoluciones-transurbar"),
    ("SODETRANS",      "resoluciones-sodetrans"),
    ("COOTRANSNORTE",  "resoluciones-cootransnorte"),
    ("TRASALIANCO",    "resoluciones-trasalianco"),
    ("COOASOATLAN",    "resoluciones-cooasoatlan"),
]

# Headers idénticos a Chrome 124 para no ser bloqueados por Cloudflare
CHROME_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Cache-Control": "no-cache",
    "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"macOS"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Upgrade-Insecure-Requests": "1",
}

DATA_DIR = Path("data/ambq")
PDF_DIR  = DATA_DIR / "pdfs"

# ── Web scraping ──────────────────────────────────────────────────────────────

def fetch_html(url: str) -> str | None:
    """Descarga una página con headers de Chrome real."""
    with httpx.Client(headers=CHROME_HEADERS, follow_redirects=True, timeout=30) as client:
        try:
            resp = client.get(url)
            if resp.status_code != 200:
                print(f"    ⚠️  HTTP {resp.status_code} → {url}")
                return None
            return resp.text
        except Exception as e:
            print(f"    ❌  {e}")
            return None


def scrape_company_page(company: str, slug: str) -> list[dict]:
    """
    Extrae las resoluciones (descripción + URL de PDF) de la página de una empresa.
    Estrategia:
      1. Fetch de la página con Chrome UA para obtener table_id y nonce del JS
      2. Llamada GET al endpoint AJAX de Ninja Tables (wp_ajax_ninja_tables_public_action)
      3. Parseo del JSON retornado
    """
    url = f"{BASE_URL}/{slug}/"
    html = fetch_html(url)
    if not html:
        return []

    # Extraer table_id y nonce del JS embebido
    tid_m   = re.search(r'"table_id"\s*:\s*"(\d+)"', html)
    nonce_m = re.search(r'ninja_table_public_nonce["\s:,]+([a-f0-9]{8,})', html)
    if not tid_m or not nonce_m:
        print(f"    ⚠️  No se encontró table_id/nonce para {company}")
        return []

    table_id = tid_m.group(1)
    nonce    = nonce_m.group(1)

    return _fetch_via_ajax_get(company, url, table_id, nonce)


def _fetch_via_ajax_get(company: str, referer: str, table_id: str, nonce: str) -> list[dict]:
    """
    Llama al endpoint AJAX de Ninja Tables como GET (idéntico al browser).
    La acción 'wp_ajax_ninja_tables_public_action' es la expuesta públicamente.
    """
    ajax_url = (
        "https://www.ambq.gov.co/wp-admin/admin-ajax.php"
        "?action=wp_ajax_ninja_tables_public_action"
        f"&table_id={table_id}"
        "&target_action=get-all-data"
        "&default_sorting=old_first"
        "&skip_rows=0&limit_rows=0"
        f"&ninja_table_public_nonce={nonce}"
    )

    ajax_headers = {
        **CHROME_HEADERS,
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": referer,
    }

    try:
        with httpx.Client(headers=ajax_headers, follow_redirects=True, timeout=20) as client:
            resp = client.get(ajax_url)

        if resp.status_code != 200 or resp.text in ("0", "-1", ""):
            print(f"    ⚠️  AJAX {resp.status_code}: {resp.text[:80]}")
            return []

        data = resp.json()
        if not isinstance(data, list):
            print(f"    ⚠️  Respuesta inesperada: {str(data)[:80]}")
            return []

        results = []
        for row in data:
            value = row.get("value", row)   # estructura: {"options":…,"value":{…}}
            # La columna tiene tilde mal codificada: "descripcin"
            desc = (
                value.get("descripcin")
                or value.get("descripcion")
                or value.get("descripción")
                or ""
            )
            link_html = value.get("link", "")
            href_m = re.search(r'href=["\']([^"\']+\.pdf)["\']', link_html, re.IGNORECASE)
            if href_m:
                results.append({
                    "empresa": company,
                    "descripcion": desc,
                    "pdf_url": href_m.group(1),
                })

        return results

    except Exception as e:
        print(f"    ❌  AJAX error: {e}")
        return []


# ── Descarga de PDFs ──────────────────────────────────────────────────────────

def download_pdf(pdf_url: str, dest: Path) -> bool:
    """Descarga un PDF si no existe ya. Retorna True si OK."""
    if dest.exists():
        return True
    try:
        with httpx.Client(headers=CHROME_HEADERS, follow_redirects=True, timeout=60) as client:
            resp = client.get(pdf_url)
            if resp.status_code == 200 and b"%PDF" in resp.content[:10]:
                dest.write_bytes(resp.content)
                return True
            print(f"    ⚠️  PDF no válido ({resp.status_code}): {pdf_url}")
            return False
    except Exception as e:
        print(f"    ❌  {e}")
        return False


# ── Extracción de texto PDF ───────────────────────────────────────────────────

def extract_routes_from_pdf(pdf_path: Path, empresa: str) -> list[dict]:
    """
    Lee un PDF de resolución y extrae la información de cada ruta.

    Estructura de la tabla en las resoluciones AMBQ:
      Ruta Código   | [CÓDIGO, ej. A18-4183]
      Denominación  | [NOMBRE, ej. Barranquillita – Cevillar – Recreo]
      Recorrido     | [Mapa + texto "Saliendo de la Terminal..."]
      Características Técnicas de la Ruta | [Tabla]

    pdfplumber extrae el texto mezclando columnas, por eso usamos
    'Saliendo de' como ancla del recorrido, que es el marcador más confiable.
    """
    routes: list[dict] = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            pages_text = [page.extract_text() or "" for page in pdf.pages]
    except Exception as e:
        print(f"    ❌  Error leyendo {pdf_path.name}: {e}")
        return []

    full_text = "\n".join(pages_text)
    if not full_text.strip():
        print(f"    ⚠️  {pdf_path.name}: PDF sin texto (posiblemente escaneado)")
        return []

    # Necesitamos al menos un "Saliendo de" para considerar que hay recorrido
    if not re.search(r"Saliendo\s+de", full_text, re.IGNORECASE):
        return []

    # ── Códigos de ruta (formato AMBQ: letras + número - 4 dígitos) ───────────
    codes = re.findall(r"\b([A-Z]{1,3}\d{1,2}[–\-]\d{3,4})\b", full_text)
    codes = list(dict.fromkeys(codes))

    # ── Denominación ──────────────────────────────────────────────────────────
    # El PDF mezcla columnas; las líneas del label y del contenido se intercalan:
    #   "Ruta Código C5-4136"
    #   "Manuela Beltrán – Los Puertos –"     ← contenido
    #   "Denominación (Origen por esta hasta"  ← LABEL izquierdo
    #   "Galán – Universidades – Calle 72 –"  ← contenido (dentro del label!)
    #   "Destino)"                             ← fin label izquierdo
    #   "Circular"                             ← contenido
    #   "Recorrido"
    #
    # Estrategia: extraer TODAS las líneas entre "Ruta Código" y "Recorrido",
    # luego DESCARTAR las líneas que son puramente texto de label (no contenido).
    denom = ""
    block_m = re.search(
        r"Ruta\s+C[oó]digo[^\n]*\n(.+?)Recorrido",
        full_text,
        re.IGNORECASE | re.DOTALL,
    )
    if block_m:
        raw_lines = block_m.group(1).splitlines()
        label_patterns = re.compile(
            r"^(?:"
            r"Denominaci[oó]n"      # "Denominación (Origen por esta hasta..."
            r"|Origen\s+por"        # "Origen por esta hasta"
            r"|Destino\)?"          # "Destino)" o "Destino"
            r"|\(Origen"            # "(Origen por esta hasta"
            r"|Ruta\s+C[oó]digo"   # "Ruta Código" (en caso de repetición)
            r")",
            re.IGNORECASE,
        )
        content_lines = []
        for line in raw_lines:
            line = line.strip()
            if not line:
                continue
            # Descartar líneas que son exclusivamente texto de label
            if label_patterns.search(line):
                continue
            # Descartar líneas con formato de label mezclado (ej. "Origen por esta hasta")
            if re.match(r"^\(Origen", line, re.IGNORECASE):
                continue
            content_lines.append(line)
        denom = " ".join(content_lines).strip()
    else:
        # Fallback para PDFs con otra estructura (sin "Ruta Código" visible)
        denom_m2 = re.search(
            r"Denominaci[oó]n[^)]*\)\s*\n?(.+?)\nRecorrido",
            full_text,
            re.IGNORECASE | re.DOTALL,
        )
        if denom_m2:
            denom = re.sub(r"\s+", " ", denom_m2.group(1)).strip()

    # ── Recorrido (desde "Saliendo de" hasta "Características") ─────────────
    rec_m = re.search(
        r"(Saliendo\s+de.+?)(?=Caracter[ií]sticas|PARÁGRAFO|ARTÍCULO\s+SEGUNDO)",
        full_text, re.IGNORECASE | re.DOTALL,
    )
    recorrido = ""
    if rec_m:
        raw = rec_m.group(1)
        # Normalizar espacios (PDFs con OCR tienen espacios pegados, ej. "8por")
        raw = re.sub(r"(\d)([A-Za-z])", r"\1 \2", raw)   # "8por" → "8 por"
        recorrido = re.sub(r"[ \t]+", " ", raw).strip()
        recorrido = re.sub(r"\n{2,}", "\n", recorrido)

    # ── Calles mencionadas en el recorrido (para geocodificación) ─────────────
    # Extraer TODAS las calles/carreras mencionadas, en orden de aparición.
    # Formato: "Calle 48", "Carrera 5C", "Diagonal 138", "Avenida 17"
    calles_raw = re.findall(
        r"(?:Calle|Carrera|Diagonal|Diag\.?|Avenida|Av\.?|Transversal|Tr\.?)\s+[\d]+[A-Z]?",
        recorrido,
        re.IGNORECASE,
    )
    # Normalizar: quitar espacios dobles, capitalizar tipo de vía
    calles_norm = []
    for c in calles_raw:
        c_clean = re.sub(r"\s+", " ", c).strip()
        if c_clean not in calles_norm:
            calles_norm.append(c_clean)

    # ── Intersecciones explícitas (Calle X con Carrera Y) ─────────────────────
    intersecciones = re.findall(
        r"(?:Calle|Carrera|Diagonal|Avenida|Av\.?)\s+[\w\dA-Z]+\s+(?:con|Con)\s+"
        r"(?:Calle|Carrera|Diagonal|Avenida|Av\.?)\s+[\w\dA-Z]+",
        recorrido,
        re.IGNORECASE,
    )
    intersecciones = list(dict.fromkeys(intersecciones))

    routes.append({
        "empresa": empresa,
        "pdf": pdf_path.name,
        "codigos": codes[:10],
        "denominacion": denom[:300],
        "recorrido": recorrido[:4000],
        "calles": calles_norm[:80],
        "intersecciones": intersecciones[:60],
    })

    return routes


# ── Pipeline principal ────────────────────────────────────────────────────────

def run_scrape_index():
    """Fase 1: scrapear páginas → obtener índice de PDFs."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    all_entries: list[dict] = []

    print(f"\n{'='*60}")
    print(f"FASE 1 — Scraping de páginas ({len(COMPANIES)} empresas)")
    print(f"{'='*60}")

    for company, slug in COMPANIES:
        print(f"\n→ {company}")
        entries = scrape_company_page(company, slug)
        print(f"  {len(entries)} resoluciones")
        all_entries.extend(entries)
        time.sleep(1.5)   # cortesía con el servidor

    index_path = DATA_DIR / "resoluciones_index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(all_entries, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Índice guardado: {index_path}")
    print(f"   Total resoluciones: {len(all_entries)}")
    return all_entries


def run_download_pdfs(entries: list[dict]):
    """Fase 2: descargar cada PDF."""
    PDF_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"FASE 2 — Descarga de PDFs ({len(entries)} documentos)")
    print(f"{'='*60}")

    ok = 0
    for entry in entries:
        url = entry["pdf_url"]
        # Nombre seguro para el archivo
        filename = re.sub(r"[^\w.\-]", "_", url.split("/")[-1])
        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"
        dest = PDF_DIR / filename
        entry["local_pdf"] = str(dest)

        print(f"  ⬇  {filename[:60]}")
        if download_pdf(url, dest):
            ok += 1
        time.sleep(0.5)

    print(f"\n✅ Descargados: {ok}/{len(entries)}")


def run_parse_pdfs(entries: list[dict]):
    """Fase 3: extraer rutas y paradas de cada PDF."""
    print(f"\n{'='*60}")
    print(f"FASE 3 — Extracción de texto de PDFs")
    print(f"{'='*60}")

    all_routes: list[dict] = []
    for entry in entries:
        # Derivar la ruta local si no está en el índice
        local = entry.get("local_pdf")
        if not local:
            filename = re.sub(r"[^\w.\-]", "_", entry["pdf_url"].split("/")[-1])
            if not filename.lower().endswith(".pdf"):
                filename += ".pdf"
            local = str(PDF_DIR / filename)

        if not Path(local).exists():
            continue
        print(f"  📄 {Path(local).name[:60]}")
        routes = extract_routes_from_pdf(Path(local), entry["empresa"])
        for r in routes:
            r["descripcion"] = entry["descripcion"]
        all_routes.extend(routes)

    out_path = DATA_DIR / "rutas_ambq.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_routes, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Rutas extraídas: {len(all_routes)}")
    print(f"   Guardado en: {out_path}")
    return all_routes


# ── Entrada ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scraper AMBQ Barranquilla")
    parser.add_argument("--only-index",  action="store_true", help="Solo scrape de páginas")
    parser.add_argument("--only-parse",  action="store_true", help="Solo parseo de PDFs ya descargados")
    args = parser.parse_args()

    if args.only_parse:
        index_path = DATA_DIR / "resoluciones_index.json"
        if not index_path.exists():
            print("❌  Primero corre sin --only-parse para obtener el índice")
        else:
            entries = json.loads(index_path.read_text())
            run_parse_pdfs(entries)
    elif args.only_index:
        run_scrape_index()
    else:
        entries = run_scrape_index()
        run_download_pdfs(entries)
        run_parse_pdfs(entries)
