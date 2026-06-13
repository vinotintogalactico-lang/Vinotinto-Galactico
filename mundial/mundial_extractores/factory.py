from urllib.parse import urlparse
from mundial.mundial_extractores.generic import GenericExtractor
from mundial.mundial_extractores.as_ import AsExtractor
from mundial.mundial_extractores.marca import MarcaExtractor
from mundial.mundial_extractores.mundodeportivo import MundoDeportivoExtractor
from mundial.mundial_extractores.meridiano import MeridianoExtractor
from mundial.mundial_extractores.sport import SportExtractor
from mundial.mundial_extractores.ole import OleExtractor
from mundial.mundial_extractores.tycsports import TycSportsExtractor
from mundial.mundial_extractores.espndeportes import EspnDeportesExtractor
from mundial.mundial_extractores.infobae import InfobaeExtractor
from mundial.mundial_extractores.depor import DeporExtractor
from mundial.mundial_extractores.relevo import ReleVoExtractor

_DOMAIN_MAP = {
    # Reutilizados de VG
    "as.com":             AsExtractor,
    "marca.com":          MarcaExtractor,
    "mundodeportivo.com": MundoDeportivoExtractor,
    "meridiano.net":      MeridianoExtractor,
    "sport.es":           SportExtractor,
    # Nuevos
    "ole.com.ar":         OleExtractor,
    "tycsports.com":      TycSportsExtractor,
    "espndeportes.espn.com": EspnDeportesExtractor,
    "espn.com":           EspnDeportesExtractor,
    "infobae.com":        InfobaeExtractor,
    "depor.com":          DeporExtractor,
    "relevo.com":         ReleVoExtractor,
}


def get_extractor(fuente: str, url: str, categoria: str):
    domain = urlparse(url).netloc.lower().removeprefix("www.")
    for key, cls in _DOMAIN_MAP.items():
        if key in domain:
            return cls(fuente, url, categoria)
    return GenericExtractor(fuente, url, categoria)
