"""
Lector de Excels adaptado al formato específico de Vinotinto Galáctico
"""
import re
from pathlib import Path
from urllib.parse import urlparse
import pandas as pd

BASE_DIR = Path(__file__).parent.parent.resolve()
DATA_DIR = BASE_DIR / "data"


def _nombre_desde_url(url: str) -> str:
    """Extrae un nombre legible desde una URL (dominio sin www)"""
    try:
        netloc = urlparse(url).netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc.split(".")[0].capitalize()
    except Exception:
        return url


def load_sources_vinotinto() -> dict:
    """
    Lee 'data/Prensa Deportiva.xlsx'
    Formato: celdas con 'CATEGORIA:' y debajo URLs.
    Retorna: {categoria: [(nombre, url), ...]}
    """
    excel_path = DATA_DIR / "Prensa Deportiva.xlsx"
    if not excel_path.exists():
        raise FileNotFoundError(f"No existe: {excel_path}")

    df = pd.read_excel(excel_path, header=None)
    # Aplanar todas las celdas en una sola lista
    celdas = []
    for col in df.columns:
        for val in df[col].dropna().astype(str):
            celdas.append(val.strip())

    sources = {}
    categoria_actual = None
    urls_vistas = set()

    for celda in celdas:
        if not celda:
            continue

        # ¿Es una categoría? (termina en ":" y no es URL)
        if celda.endswith(":") and not celda.startswith("http"):
            nombre_cat = celda[:-1].strip()
            # Mapear nombres del Excel a los del sistema
            mapping = {
                "REAL MADRID": "Real Madrid Masculino",
                "REAL MADRID FEMENINO": "Real Madrid Femenino",
                "LALIGA": "LaLiga",
                "SELECCIÓN ESPAÑOLA": "Selección Española Masculina",
                "SELECCIÓN ESPAÑOLA FEMENINO": "Selección Española Femenina",
                "SELECCION ESPAÑOLA": "Selección Española Masculina",
                "SELECCION ESPAÑOLA FEMENINO": "Selección Española Femenina",
                "LIGA FUTVE": "Liga FUTVE",
                "VINOTINTO": "Vinotinto Masculina",
                "VENEZUELA": None,  # Sección padre, se ignora
                "VENEZUELA FEMENINO": "Vinotinto Femenina",
            }
            categoria_actual = mapping.get(nombre_cat.upper(), nombre_cat)
            if categoria_actual and categoria_actual not in sources:
                sources[categoria_actual] = []
            continue

        # ¿Es una URL?
        if celda.startswith("http"):
            if celda in urls_vistas:
                continue  # Evitar duplicados
            urls_vistas.add(celda)
            if categoria_actual:
                nombre = _nombre_desde_url(celda)
                # Evitar duplicados de nombre dentro de la misma categoría
                nombres_existentes = [n for n, _ in sources[categoria_actual]]
                if nombre in nombres_existentes:
                    nombre = f"{nombre} ({len(nombres_existentes)+1})"
                sources[categoria_actual].append((nombre, celda))

    # Eliminar categorías vacías
    sources = {k: v for k, v in sources.items() if v}
    return sources


def load_sources_mundial() -> dict:
    """
    Lee 'data/Prensa_Mundial_2026_ListaEnlaces.xlsx'
    Formato: una columna 'Enlaces' con URLs.
    Retorna: {"Mundial Global": [(nombre, url), ...]}
    """
    excel_path = DATA_DIR / "Prensa_Mundial_2026_ListaEnlaces.xlsx"
    if not excel_path.exists():
        raise FileNotFoundError(f"No existe: {excel_path}")

    df = pd.read_excel(excel_path)
    # Buscar la columna de enlaces (puede llamarse "Enlaces" o ser la primera)
    col_enlaces = None
    for col in df.columns:
        if "enlace" in str(col).lower():
            col_enlaces = col
            break
    if col_enlaces is None:
        col_enlaces = df.columns[0]

    sources = {"Mundial Global": []}
    urls_vistas = set()

    for url in df[col_enlaces].dropna().astype(str):
        url = url.strip()
        if not url.startswith("http"):
            continue
        if url in urls_vistas:
            continue
        urls_vistas.add(url)
        nombre = _nombre_desde_url(url)
        # Evitar duplicados de nombre
        nombres_existentes = [n for n, _ in sources["Mundial Global"]]
        if nombre in nombres_existentes:
            nombre = f"{nombre} ({len(nombres_existentes)+1})"
        sources["Mundial Global"].append((nombre, url))

    return sources