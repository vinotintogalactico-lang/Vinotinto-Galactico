from playwright.async_api import Page
from extractores.generic import GenericExtractor

class RealMadridExtractor(GenericExtractor):
    async def _get_article_links(self, page: Page) -> list[str]:
        seen, links = set(), []
        elements = await page.locator("a[href]").all()
        for el in elements:
            href = await el.get_attribute("href")
            if not href: continue
            href = self._absolute(href)
            if "/noticias/" in href.lower() and href.count("-") > 3:
                if href not in seen:
                    seen.add(href); links.append(href)
            if len(links) >= 3: break
        return links

    async def _extract_article(self, context, url: str) -> dict | None:
        page = await context.new_page()
        try:
            from bs4 import BeautifulSoup
            await page.goto(url, timeout=20_000, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            
            title = soup.find("h1").get_text(strip=True)
            # Captura manual de párrafos para Comunicados Oficiales
            body = "\n\n".join([p.get_text(strip=True) for p in soup.select(".article-body p, .article-content p, .news-detail__content p") if len(p.get_text()) > 20])
            
            return {"title": title, "body": body, "url": url, "date": "15/06/2026", "fuente": "Real Madrid Oficial"}
        except: return None
        finally: await page.close()