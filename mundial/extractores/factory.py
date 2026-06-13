from urllib.parse import urlparse
from extractores.generic import GenericExtractor
from extractores.as_ import AsExtractor
from extractores.marca import MarcaExtractor
from extractores.mundodeportivo import MundoDeportivoExtractor
from extractores.meridiano import MeridianoExtractor
from extractores.sport import SportExtractor
from extractores.ole import OleExtractor
from extractores.tycsports import TycSportsExtractor
from extractores.espndeportes import EspnDeportesExtractor
from extractores.infobae import InfobaeExtractor
from extractores.depor import DeporExtractor
from extractores.relevo import ReleVoExtractor

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
