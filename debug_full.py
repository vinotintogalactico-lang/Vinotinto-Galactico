import asyncio
import logging
from extractores.factory import get_extractor
from core.date_validator import is_today
from core.content_filter import is_valid_content

logging.basicConfig(level=logging.INFO)

async def debug_site(name, url, category):
    print(f"\n{'='*50}\nDEBUGGING {name}\n{'='*50}")
    extractor = get_extractor(name, url, category)
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36")
        page = await context.new_page()
        
        # 1. Obtener links crudos
        try:
            await page.goto(url, timeout=25000, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)
            links = await extractor._get_article_links(page)
            print(f"[{name}] Encontró {len(links)} links iniciales")
            
            # Imprimir los primeros 8 links
            for i, link in enumerate(links[:8]):
                print(f"  {i+1}. {link}")
        except Exception as e:
            print(f"Error obteniendo links: {e}")
            return
            
        # 2. Extraer y validar los primeros 5 links (para ver qué falla)
        for i, link in enumerate(links[:5]):
            print(f"\n--- Probando Link {i+1}: {link}")
            art = await extractor._extract_article(context, link)
            if not art:
                print("  ❌ Falló la extracción (HTML parse retornó None)")
                continue
                
            print(f"  Título: {art.get('title')[:80]}...")
            date_str = art.get('date', '')
            print(f"  Fecha extraída: '{date_str}'")
            
            valid_date, log_d = is_today(date_str)
            print(f"  Validación Fecha: {valid_date} ({log_d})")
            
            valid_cont, log_c = is_valid_content(art.get('title', ''), art.get('subtitle', ''), art.get('body', ''), category)
            print(f"  Validación Contenido: {valid_cont} ({log_c})")

if __name__ == "__main__":
    async def main():
        await debug_site("As", "https://as.com/noticias/real-madrid/?omnil=mod_esc", "Real Madrid Masculino")
        await debug_site("Marca", "https://www.marca.com/futbol/real-madrid.html?intcmp=MENUESCU&s_kw=realmadrid", "Real Madrid Masculino")
        await debug_site("Madridistareal", "https://madridistareal.com/real-madrid/", "Real Madrid Masculino")
        await debug_site("Sport", "https://www.sport.es/es/real-madrid/", "Real Madrid Masculino")
        await debug_site("Defensa Central", "https://www.defensacentral.com/real_madrid", "Real Madrid Masculino")

    asyncio.run(main())
