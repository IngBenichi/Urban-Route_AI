"""Geocodificación de texto a coordenadas usando Nominatim (OpenStreetMap)."""
import re
import httpx
from typing import Optional

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
# Bounding box de Barranquilla y Soledad
BARRANQUILLA_VIEWBOX = "-75.1,10.7,-74.5,11.2"

HEADERS = {
    "User-Agent": "UrbanRouteAI/1.0 (barranquilla-bus-routes; contact: urbanroute@localhost)"
}

# Abreviaturas de tipo de vía comunes en Colombia
_CALLE_RE  = r"(?:Calle|Cl|Cll?)\s*\.?"
_CARRERA_RE = r"(?:Carrera|Cra?|Carr?)\s*\.?"
_DIAGONAL_RE = r"(?:Diagonal|Diag?)\s*\.?"
_TRANSVERSAL_RE = r"(?:Transversal|Transv?|Tv)\s*\.?"
_VIA_RE = f"(?:{_CALLE_RE}|{_CARRERA_RE}|{_DIAGONAL_RE}|{_TRANSVERSAL_RE})"

# Patrón: "Tipo NumPrincipal # NumCruce[-detalle]"
# Ejemplos: "Calle 92 # 35", "Cra 18 # 63-10", "Cl 56 #16C-16"
_COL_ADDR = re.compile(
    rf"({_VIA_RE})\s*(\d+[A-Za-z]?)\s*#\s*(\d+[A-Za-z]?)(?:-\d+)?",
    re.IGNORECASE,
)


def _normalize_colombian_address(query: str) -> str:
    """
    Convierte la notación colombiana de direcciones a un formato que Nominatim entiende.

    Ejemplos:
      "Calle 92 # 35"     → "Calle 92 & Carrera 35"
      "Cra 18 # 63-10"    → "Carrera 18 & Calle 63"
      "Cl 56 #16C-16"     → "Calle 56 & Carrera 16C"
    """
    m = _COL_ADDR.search(query)
    if not m:
        return query  # No es una dirección colombiana estándar

    tipo_raw, num_principal, num_cruce = m.group(1).strip(), m.group(2), m.group(3)

    # Normalizar el tipo de vía principal
    t = tipo_raw.lower().rstrip(".")
    if re.match(r"c(?:arrera|arr?|ra?)", t, re.I):  # Carrera, Cra, Carr — verificar ANTES que Calle
        via_principal = f"Carrera {num_principal}"
        via_cruce     = f"Calle {num_cruce}"
    elif re.match(r"c(?:alle|ll?)?$", t, re.I):      # Calle, Cl, Cll
        via_principal = f"Calle {num_principal}"
        via_cruce     = f"Carrera {num_cruce}"
    elif re.match(r"diag", t, re.I):
        via_principal = f"Diagonal {num_principal}"
        via_cruce     = f"Carrera {num_cruce}"
    elif re.match(r"transv|tv", t, re.I):
        via_principal = f"Transversal {num_principal}"
        via_cruce     = f"Calle {num_cruce}"
    else:
        return query

    # Detectar si la query menciona Soledad para agregar el municipio correcto
    ciudad = "Soledad, Atlántico" if "soledad" in query.lower() else "Barranquilla"
    return f"{via_principal} & {via_cruce}, {ciudad}, Colombia"


async def geocode(query: str) -> Optional[dict]:
    """
    Geocodifica un texto y retorna {"lat": float, "lon": float, "display_name": str}.
    Prioriza resultados dentro del área de Barranquilla / Soledad.
    """
    # Normalizar direcciones colombianas con "#"
    normalized = _normalize_colombian_address(query)

    # Agrega contexto de ciudad si la query no lo menciona
    search_query = normalized
    if not any(w in normalized.lower() for w in ("barranquilla", "atlántico", "atlantico", "soledad", "colombia")):
        search_query = f"{normalized}, Barranquilla, Colombia"

    params = {
        "q": search_query,
        "format": "json",
        "limit": 5,
        "viewbox": BARRANQUILLA_VIEWBOX,
        "bounded": 0,  # No estricto, pero prioriza el viewbox
        "countrycodes": "co",
    }

    async with httpx.AsyncClient(headers=HEADERS, timeout=10.0) as client:
        resp = await client.get(NOMINATIM_URL, params=params)
        resp.raise_for_status()
        results = resp.json()

    if not results:
        return None

    # Tomar el primer resultado
    best = results[0]
    return {
        "lat": float(best["lat"]),
        "lon": float(best["lon"]),
        "display_name": best.get("display_name", query),
    }
