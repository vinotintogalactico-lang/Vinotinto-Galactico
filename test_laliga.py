import asyncio
import sys
sys.path.insert(0, ".")
from extractores.factory import get_extractor

async def test():
    tests = [
        ("Marca LaLiga", "https://www.marca.com/futbol/primera-division.html?intcmp=MENUMIGA&s_kw=laliga-ea-sports", "La Liga"),
        ("Sport LaLiga", "https://www.sport.es/es/laliga/", "La Liga"),
        ("MundoDeportivo LaLiga", "https://www.mundodeportivo.com/futbol/laliga", "La Liga"),
    ]
    for nombre, url, cat in tests:
        print(f"\n=== Probando: {nombre} ({cat}) ===")
        try:
            ext = get_extractor(nombre, url, cat)
            noticias, log = await ext.extract()
            print(f"Estado: {log['estado']} | Encontradas: {log['encontradas']} | Extraídas: {log['extraidas']}")
            if log.get("error"):
                print(f"Error: {log['error'][:200]}")
            for n in noticias:
                print(f"  - [{n.get('date','')}] {n.get('title','')[:80]}")
        except Exception as e:
            print(f"Exception: {e}")

asyncio.run(test())
