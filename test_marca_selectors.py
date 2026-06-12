import asyncio
from playwright.async_api import async_playwright

async def test_marca():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://www.marca.com/futbol/mundial/")
        await page.wait_for_timeout(2000)
        print("Page title:", await page.title())
        print("Page URL:", page.url)
        
        selectors = [
            ".ue-c-cover-content__headline-group a[href]",
            ".titular a[href]",
            "main h2 a[href]",
            "main h3 a[href]",
            "main article a[href]",
            "article a[href]",
            ".ue-c-cover-content__link",
        ]
        
        for sel in selectors:
            elements = await page.query_selector_all(sel)
            print(f"Selector '{sel}': {len(elements)} elements")
            if elements:
                href = await elements[0].get_attribute("href")
                print(f"  First href: {href}")
                
        await browser.close()

asyncio.run(test_marca())
