from urllib.parse import urlparse
from extractores.generic import GenericExtractor
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

_DOMAIN_MAP = {
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
}

def get_extractor(fuente, url, categoria):
    domain = urlparse(url).netloc.lower().removeprefix("www.")
    for key, cls in _DOMAIN_MAP.items():
        if key in domain:
            return cls(fuente, url, categoria)
    return GenericExtractor(fuente, url, categoria)