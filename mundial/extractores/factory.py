from urllib.parse import urlparse
from mundial.extractores.generic_mundial import GenericExtractor
from mundial.extractores.as_ import AsExtractor
from mundial.extractores.marca import MarcaExtractor
from mundial.extractores.mundodeportivo import MundoDeportivoExtractor
from mundial.extractores.meridiano import MeridianoExtractor
from mundial.extractores.sport import SportExtractor
from mundial.extractores.ole import OleExtractor
from mundial.extractores.tycsports import TycSportsExtractor
from mundial.extractores.espndeportes import EspnDeportesExtractor
from mundial.extractores.infobae import InfobaeExtractor
from mundial.extractores.depor import DeporExtractor
from mundial.extractores.relevo import ReleVoExtractor

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
