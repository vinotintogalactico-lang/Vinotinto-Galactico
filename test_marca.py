import asyncio
import logging
from extractores.marca import MarcaExtractor
from extractores.sport import SportExtractor
from extractores.as_ import AsExtractor

logging.basicConfig(level=logging.DEBUG)

async def test():
    print("Testing Marca...")
    m = MarcaExtractor("Marca", "https://www.marca.com/futbol/mundial/", "Mundial Global")
    noticias, log = await m.extract()
    print("Marca:", log)

    print("Testing Sport...")
    s = SportExtractor("Sport", "https://www.sport.es/es/mundial/", "Mundial Global")
    noticias, log = await s.extract()
    print("Sport:", log)

asyncio.run(test())
