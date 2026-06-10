import asyncio
import logging
from extractores.factory import get_extractor

logging.basicConfig(level=logging.INFO)

async def test():
    print("Testeando Defensacentral...")
    ext = get_extractor("Defensacentral", "https://www.defensacentral.com/real_madrid", "Real Madrid Masculino")
    noticias, log = await ext.extract()
    print("--- LOG DC ---")
    print(log)
    for n in noticias:
        print(f"[{n['date']}] {n['title']}")
        
    print("\nTesteando Sport...")
    ext_sport = get_extractor("Sport", "https://www.sport.es/es/real-madrid/", "Real Madrid Masculino")
    noticias_sp, log_sp = await ext_sport.extract()
    print("--- LOG SPORT ---")
    print(log_sp)
    for n in noticias_sp:
        print(f"[{n['date']}] {n['title']}")

if __name__ == "__main__":
    asyncio.run(test())
