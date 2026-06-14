import asyncio
import sys
sys.path.insert(0, ".")
from extractores.marca import MarcaExtractor
from playwright.async_api import async_playwright

async def debug_marca():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 900})
        ext = MarcaExtractor("Marca", "https://www.marca.com/futbol/primera-division.html", "La Liga")
        page = await context.new_page()
        await page.goto("https://www.marca.com/futbol/primera-division.html", timeout=30000)
        
        selectors = [
            ".ue-c-cover-content__headline-group a[href]",
            ".titular a[href]",
            "main h2 a[href]",
            "main h3 a[href]",
            "main article a[href]",
        ]
        
        for sel in selectors:
            elements = await page.query_selector_all(sel)
            print(f"Selector {sel} encontró {len(elements)} elementos.")
            for el in elements:
                href = await el.get_attribute("href")
                if "marca.com" in href:
                    print(f"Encontrado: {href}")
            if elements:
                break
        
        await browser.close()

asyncio.run(debug_marca())
