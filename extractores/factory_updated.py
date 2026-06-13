"""
Factory de Extractores - Soporta Vinotinto + Mundial
Selecciona el extractor correcto según el dominio de la URL
"""
from urllib.parse import urlparse
from extractores.generic import GenericExtractor

# Importar extractores de Vinotinto
from extractores.realmadrid import RealMadridExtractor
from extractores.as_ import AsExtractor
from extractores.marca import MarcaExtractor
from extractores.mundodeportivo import MundoDeportivoExtractor
from extractores.meridiano import MeridianoExtractor
from extractores.defensacentral import DefensacentralExtractor
from extractores.sport import SportExtractor
from extractores.madridistareal import MadridistarealExtractor
from extractores.estadiodeportivo import EstadioDeportivoExtractor
from extractores.laliga import LaLigaExtractor

# Importar extractores del Mundial
try:
    from mundial_extractores import (
        TelemundoExtractor, TudnExtractor, TvaztecaExtractor,
        TycsportsExtractor, FutbolredExtractor, WinsportsExtractor,
        RecordExtractor, MediatiempoExtractor, RtveExtractor
    )
except ImportError:
    # Si no existen aún, usar GenericExtractor como fallback
    TelemundoExtractor = GenericExtractor
    TudnExtractor = GenericExtractor
    TvaztecaExtractor = GenericExtractor
    TycsportsExtractor = GenericExtractor
    FutbolredExtractor = GenericExtractor
    WinsportsExtractor = GenericExtractor
    RecordExtractor = GenericExtractor
    MediatiempoExtractor = GenericExtractor
    RtveExtractor = GenericExtractor

# Mapeo de dominios -> Clase Extractor
_DOMAIN_MAP = {
    # ────────────────────────────────────────────────────────────
    # VINOTINTO GALÁCTICO
    # ────────────────────────────────────────────────────────────
    "realmadrid.com": RealMadridExtractor,
    "as.com": AsExtractor,
    "marca.com": MarcaExtractor,
    "mundodeportivo.com": MundoDeportivoExtractor,
    "meridiano.net": MeridianoExtractor,
    "defensacentral.com": DefensacentralExtractor,
    "sport.es": SportExtractor,
    "madridistareal.com": MadridistarealExtractor,
    "estadiodeportivo.com": EstadioDeportivoExtractor,
    "laliga.com": LaLigaExtractor,
    
    # ────────────────────────────────────────────────────────────
    # MUNDIAL 2026
    # ────────────────────────────────────────────────────────────
    "telemundodeportes.com": TelemundoExtractor,
    "tudn.com": TudnExtractor,
    "tvazteca.com": TvaztecaExtractor,
    "tycsports.com": TycsportsExtractor,
    "futbolred.com": FutbolredExtractor,
    "winsports.co": WinsportsExtractor,
    "record.com.mx": RecordExtractor,
    "mediotiempo.com": MediatiempoExtractor,
    "rtve.es": RtveExtractor,
    
    # Los demás (Televen, Caracol, RCN, Telefe, DirectV, etc.)
    # se manejan con GenericExtractor por defecto
}


def get_extractor(fuente: str, url: str, categoria: str):
    """
    Retorna la clase Extractor apropiada para una URL.
    
    Args:
        fuente: Nombre amigable de la fuente (ej: "MARCA")
        url: URL a extraer
        categoria: Categoría (ej: "Real Madrid Masculino" o "Mundial Global")
    
    Returns:
        Instancia de GenericExtractor o subclase específica
    """
    domain = urlparse(url).netloc.lower().removeprefix("www.")
    
    # Buscar en el mapeo
    for key, cls in _DOMAIN_MAP.items():
        if key in domain:
            return cls(fuente, url, categoria)
    
    # Si no encuentra, usar GenericExtractor
    return GenericExtractor(fuente, url, categoria)
