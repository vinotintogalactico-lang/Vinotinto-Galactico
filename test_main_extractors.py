import asyncio
import sys
sys.path.insert(0, ".")
from extractores.as_ import AsExtractor
from extractores.meridiano import MeridianoExtractor
from extractores.defensacentral import DefensacentralExtractor

async def test():
    tests = [
        ("AS Real Madrid", "https://as.com/noticias/real-madrid/?omnil=mod_esc", "Real Madrid Masculino"),
        ("AS Femenino",    "https://as.com/noticias/real-madrid-femenino/?omnil=mod_esc", "Real Madrid Femenino"),
        ("Meridiano Español", "https://meridiano.net/futbol/espanol", "La Liga"),
        ("DefensaCentral", "https://www.defensacentral.com", "Real Madrid Masculino"),
    ]
    for nombre, url, cat in tests:
        print(f"\n=== Probando: {nombre} ===")
        ext = AsExtractor(nombre, url, cat) if "as.com" in url else \
              MeridianoExtractor(nombre, url, cat) if "meridiano" in url else \
              DefensacentralExtractor(nombre, url, cat)
        noticias, log = await ext.extract()
        print(f"Estado: {log['estado']} | Encontradas: {log['encontradas']} | Extraídas: {log['extraidas']}")
        if log.get("error"):
            print(f"Error: {log['error'][:200]}")
        for n in noticias:
            print(f"  - [{n.get('date','')}] {n.get('title','')[:80]}")

asyncio.run(test())
