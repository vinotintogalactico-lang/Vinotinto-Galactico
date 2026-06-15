import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36")
        page = await context.new_page()
        await page.goto("https://madridistareal.com/real-madrid/", timeout=25000, wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        
        links = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a[href]'))
                .map(a => a.href)
                .filter(h => h.includes('madridistareal.com') && !h.includes('category') && h.length > 40)
                .slice(0, 15);
        }''')
        print("LINKS encontrados:")
        for l in links: print(l)
        
        h2s = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('h2 a, h3 a, .entry-title a, article a'))
                .map(a => a.href)
                .slice(0, 10);
        }''')
        print("\nH2/H3/ARTICLE LINKS:")
        for h in h2s: print(h)

        await browser.close()

asyncio.run(main())
