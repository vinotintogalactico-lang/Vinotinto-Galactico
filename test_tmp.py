import asyncio
import logging
from extractores.factory import get_extractor

logging.basicConfig(level=logging.INFO)

async def main():
    cat = 'Real Madrid Masculino'
    sources = [
        ('As', 'https://as.com/futbol/real_madrid/'),
        ('Marca', 'https://www.marca.com/futbol/real-madrid.html?intcmp=MENUESCU&s_kw=realmadrid'),
        ('Defensa Central', 'https://www.defensacentral.com/real_madrid')
    ]
    for nombre, url in sources:
        print(f"Probando {nombre}...")
        ex = get_extractor(nombre, url, cat)
        nots, log = await ex.extract()
        print(f'--- {nombre} ---')
        print(f'Noticias Extraidas: {len(nots)} | Estado: {log.get("estado")} | Error: {log.get("error")}')
        for n in nots:
            print(n.get('title'), "->", n.get('date'))

if __name__ == "__main__":
    asyncio.run(main())

if __name__ == "__main__":
    asyncio.run(main())
