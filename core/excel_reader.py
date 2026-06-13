from openpyxl import load_workbook
from pathlib import Path
from urllib.parse import urlparse

EXCEL_PATH = Path(__file__).parent.parent / "data" / "Prensa Deportiva.xlsx"

# Tu mapa de categorías original
_CAT_MAP = {
    "REAL MADRID":                  "Real Madrid Masculino",
    "REAL MADRID FEMENINO":         "Real Madrid Femenino",
    "LALIGA":                       "LaLiga",
    "SELECCIÓN ESPAÑOLA":           "Selección Española Masculina",
    "SELECCIÓN ESPAÑOLA FEMENINO":  "Selección Española Femenina",
    "LIGA FUTVE":                   "Liga FUTVE",
    "VINOTINTO":                    "Vinotinto Masculina",
    "VENEZUELA FEMENINO":           "Vinotinto Femenina",
    "VENEZUELA":                    "General",
}

def _friendly_name(url: str) -> str:
    domain = urlparse(url).netloc.lower().removeprefix("www.")
    parts = domain.split(".")
    if len(parts) >= 2:
        return parts[-2].capitalize()
    return parts[0].capitalize()

def load_sources() -> dict[str, list[dict]]:
    if not EXCEL_PATH.exists():
        raise FileNotFoundError(f"No se encontró el Excel en: {EXCEL_PATH}")

    wb = load_workbook(EXCEL_PATH, data_only=True) # data_only=True es más seguro
    ws = wb.active
    sources = {}
    current_cat = "General" # Por defecto

    for row in ws.iter_rows(values_only=True):
        cell = row[0]
        if not cell: continue
        value = str(cell).strip()
        
        # Detectar bloque (Título en mayúsculas terminado en :)
        if value.endswith(":") and value == value.upper():
            title = value.rstrip(":").strip()
            current_cat = _CAT_MAP.get(title, title) # Usa el mapa o el título mismo
            continue
            
        # Detectar URL
        if value.startswith("http"):
            sources.setdefault(current_cat, []).append(
                {"nombre": _friendly_name(value), "url": value}
            )

    wb.close()
    return sources