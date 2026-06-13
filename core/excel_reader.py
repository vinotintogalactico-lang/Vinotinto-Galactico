"""
Excel Reader - Soporta AMBOS Excel (Vinotinto + Mundial)
Lee configuración de dos archivos separados y las mantiene independientes
"""
import pandas as pd
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

EXCEL_VINOTINTO = "data/Prensa Deportiva.xlsx"
EXCEL_MUNDIAL = "data/Prensa_Mundial_2026_ListaEnlaces.xlsx"


def load_sources_vinotinto() -> dict[str, list[tuple[str, str]]]:
    """
    Carga el Excel de Vinotinto Galáctico.
    Retorna: {categoria: [(nombre_fuente, url), ...]}
    """
    sources = {}
    
    if not Path(EXCEL_VINOTINTO).exists():
        logger.warning(f"Excel no encontrado: {EXCEL_VINOTINTO}")
        return sources
    
    try:
        df = pd.read_excel(EXCEL_VINOTINTO, header=None)
        col = df.iloc[:, 0]
        
        current_category = None
        
        for val in col:
            if pd.isna(val):
                continue
            
            val_str = str(val).strip()
            if not val_str:
                continue
            
            # Detectar categoría (termina con ":")
            if val_str.endswith(":"):
                current_category = val_str.rstrip(":")
                sources[current_category] = []
            
            # Detectar URL (comienza con http)
            elif val_str.startswith("http") and current_category:
                # Extraer nombre de fuente del URL
                from urllib.parse import urlparse
                domain = urlparse(val_str).netloc.replace("www.", "")
                nombre_fuente = domain.split(".")[0].upper()
                
                sources[current_category].append((nombre_fuente, val_str))
        
        logger.info(f"✅ Vinotinto: {len(sources)} categorías cargadas")
        return sources
    
    except Exception as e:
        logger.error(f"Error leyendo {EXCEL_VINOTINTO}: {e}")
        return sources


def load_sources_mundial() -> dict[str, list[tuple[str, str]]]:
    """
    Carga el Excel del Mundial 2026.
    Retorna: {"Mundial Global": [(nombre_fuente, url), ...]}
    
    Como el Excel no tiene categorías, todos los links van bajo "Mundial Global"
    y se auto-detecta el nombre de la fuente por dominio.
    """
    sources = {}
    
    if not Path(EXCEL_MUNDIAL).exists():
        logger.warning(f"Excel no encontrado: {EXCEL_MUNDIAL}")
        return sources
    
    try:
        df = pd.read_excel(EXCEL_MUNDIAL, header=None)
        col = df.iloc[:, 0]
        
        fuentes_mundial = []
        
        for val in col:
            if pd.isna(val):
                continue
            
            val_str = str(val).strip()
            if not val_str or not val_str.startswith("http"):
                continue
            
            # Auto-detectar nombre de fuente
            from urllib.parse import urlparse
            domain = urlparse(val_str).netloc.replace("www.", "")
            
            # Nombres amigables para dominios conocidos
            friendly_names = {
                "telemundodeportes": "TELEMUNDO",
                "tudn": "TUDN",
                "tvazteca": "TV AZTECA",
                "televen": "TELEVEN",
                "caracoltv": "CARACOL TV",
                "noticiasrcn": "RCN",
                "tycsports": "TYC SPORTS",
                "mitelefe": "TELEFE",
                "directvgo": "DIRECTV",
                "elcanaldelfutbol": "CANAL FUTBOL",
                "chilevision": "CHILEVISIÓN",
                "13": "CANAL 13 CHILE",
                "latina": "LATINA",
                "rtve": "RTVE",
                "liderendeportes": "LÍDER",
                "meridiano": "MERIDIANO",
                "winsports": "WIN SPORTS",
                "futbolred": "FUTBOL RED",
                "record": "RECORD",
                "mediotiempo": "MEDIOTIEMPO",
            }
            
            nombre_base = domain.split(".")[0].lower()
            nombre_fuente = friendly_names.get(nombre_base, nombre_base.upper())
            
            fuentes_mundial.append((nombre_fuente, val_str))
        
        sources["Mundial Global"] = fuentes_mundial
        logger.info(f"✅ Mundial: {len(fuentes_mundial)} fuentes cargadas")
        return sources
    
    except Exception as e:
        logger.error(f"Error leyendo {EXCEL_MUNDIAL}: {e}")
        return sources


def load_all_sources() -> tuple[dict, dict]:
    """
    Carga AMBOS Excel y retorna como tupla separada.
    
    Retorna:
        (sources_vinotinto, sources_mundial)
        
    Cada uno es: {categoria: [(nombre_fuente, url), ...]}
    """
    vinotinto = load_sources_vinotinto()
    mundial = load_sources_mundial()
    
    return vinotinto, mundial


# Para compatibilidad con código antiguo
def load_sources():
    """Retorna solo Vinotinto (compatibilidad hacia atrás)"""
    return load_sources_vinotinto()
