import asyncio
import sys
sys.path.insert(0, ".")
from extractores.sport import SportExtractor
from playwright.async_api import async_playwright

async def debug_sport():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 900})
        ext = SportExtractor("Sport", "https://www.sport.es/es/laliga/", "La Liga")
        page = await context.new_page()
        await page.goto("https://www.sport.es/es/laliga/", timeout=30000)
        
        selectors = [
            ".ft-c-content-list__item a[href]",
            ".ft-c-article__title a[href]",
            ".ft-c-card__title a[href]",
            ".ft-c-card a[href]",
            "article a[href]",
            "h2 a[href]",
            "h3 a[href]",
            "main a[href]",
        ]
        
        for sel in selectors:
            elements = await page.query_selector_all(sel)
            print(f"Selector {sel} encontró {len(elements)} elementos.")
            for el in elements:
                href = await el.get_attribute("href")
                if "sport.es" in href:
                    print(f"Encontrado: {href}")
            if elements:
                break
        
        await browser.close()

asyncio.run(debug_sport())
