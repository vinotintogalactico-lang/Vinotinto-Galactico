import asyncio
import sys
sys.path.insert(0, ".")
from extractores.factory import get_extractor
import logging

# logging.basicConfig(level=logging.DEBUG)

async def test():
    tests = [
        ("AS Real Madrid", "https://as.com/noticias/real-madrid/?omnil=mod_esc", "Real Madrid Masculino"),
        ("AS Femenino", "https://as.com/noticias/real-madrid-femenino/?omnil=mod_esc", "Real Madrid Femenino"),
        ("AS LaLiga", "https://as.com/futbol/primera/", "La Liga"),
        ("Marca LaLiga", "https://www.marca.com/futbol/primera-division.html?intcmp=MENUMIGA&s_kw=laliga-ea-sports", "La Liga"),
        ("Sport LaLiga", "https://www.sport.es/es/laliga/", "La Liga"),
        ("MundoDeportivo LaLiga", "https://www.mundodeportivo.com/futbol/laliga", "La Liga"),
        ("Meridiano Español", "https://meridiano.net/futbol/espanol", "La Liga"),
        ("AS Seleccion", "https://as.com/futbol/seleccion/", "Mundial Global"), # Assuming Seleccion is under Mundial
        ("AS Futbol Femenino", "https://as.com/futbol/femenino/", "Femenino Global"), # Assuming category
        ("Meridiano FutVe", "https://meridiano.net/futbol/futbol-venezolano", "FUTVE"),
        ("Lider FutVe", "https://www.liderendeportes.com/seccion/futbol/futve/", "FUTVE"),
        ("Defensa Central", "https://defensacentral.com/", "Real Madrid Masculino")
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
