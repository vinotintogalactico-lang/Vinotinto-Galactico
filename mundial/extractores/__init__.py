"""Extractores para el Mundial 2026."""

from mundial.extractores.generic import GenericExtractor
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

__all__ = [
    "GenericExtractor",
    "AsExtractor",
    "MarcaExtractor",
    "MundoDeportivoExtractor",
    "MeridianoExtractor",
    "SportExtractor",
    "OleExtractor",
    "TycSportsExtractor",
    "EspnDeportesExtractor",
    "InfobaeExtractor",
    "DeporExtractor",
    "ReleVoExtractor",
]
