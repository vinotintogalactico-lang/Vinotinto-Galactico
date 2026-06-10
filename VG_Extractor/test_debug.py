import asyncio
from playwright.async_api import async_playwright
from core.date_validator import is_today
from core.content_filter import is_valid_content
from core.article_parser import parse_article

async def debug_site(nombre, url, cat, sels):
    print(f"--- DEBUG: {nombre} ---")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(url)
        await page.wait_for_timeout(2000)
        
        links = []
        for sel in sels:
            elements = await page.query_selector_all(sel)
            for el in elements:
                href = await el.get_attribute("href")
                if href and 'http' in href and not '/tags/' in href and not '/author/' in href and not 'resultados' in href:
                    if href not in links:
                        links.append(href)
            if len(links) > 3:
                break
                
        print(f"Links encontrados: {len(links)}")
        for link in links[:3]:
            print(f"-> Probando {link}")
            p2 = await context.new_page()
            try:
                await p2.goto(link)
                await p2.wait_for_timeout(1000)
                html = await p2.content()
                from bs4 import BeautifulSoup as _BS
                _soup = _BS(html, "html.parser")
                date_text = ""
                _time = _soup.select_one("time[datetime]")
                if _time and _time.get("datetime"):
                    date_text = _time["datetime"]
                
                art = parse_article(html, link, date=date_text)
                t = art.get('title','')
                d = art.get('date', '')
                
                print(f"   Tit: {t}")
                print(f"   Fec: {d}")
                
                valid_content = is_valid_content(t, cat)
                valid_date, log_d = is_today(d)
                print(f"   Filtro C: {valid_content} | Filtro D: {valid_date} ({log_d})")
            except Exception as e:
                print(f"   Error: {e}")
            finally:
                await p2.close()
        await browser.close()

async def main():
    cat = "Real Madrid Masculino"
    await debug_site("As", "https://as.com/futbol/real_madrid/", cat, [".a-article-snapshot a[href]", ".a-article-list__item a[href]", "main a[href]"])
    await debug_site("Defensa Central", "https://www.defensacentral.com/real_madrid", cat, [".article a[href]", "article a[href]", "h2 a[href]", "main a[href]"])

if __name__ == "__main__":
    asyncio.run(main())
