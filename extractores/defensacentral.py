"""Extractor para defensacentral.com
Los artículos tienen estructura: /actualidad/titular-con-guiones_339426_102.html
Solo 2 segmentos de path, pero slugs largos con guiones.
"""
from urllib.parse import urlparse
from playwright.async_api import Page
from extractores.generic import GenericExtractor


class DefensacentralExtractor(GenericExtractor):

    async def _get_article_links(self, page: Page) -> list[str]:
        await page.wait_for_timeout(2000)
        seen: set[str] = set()
        batch: list[str] = []

        # Defensa Central suele tener las noticias principales arriba en un div de clase 'home-noticias' o similar
        # Si no, buscamos los primeros artículos del <main>
        container = page.locator("main, .td-main-content, .home-noticias").first
        
        all_links = await container.locator("a[href]").all()
        for el in all_links:
            href = await el.get_attribute("href")
            if not href: continue
            href = self._absolute(href)

            if "defensacentral.com" not in href: continue

            path = urlparse(href).path
            segments = [p for p in path.split("/") if p]
            if len(segments) < 2: continue

            last_slug = segments[-1].replace(".html", "")
            # Los artículos de DC tienen un ID numérico al final: noticia_12345.html
            if last_slug.count("-") < 2 and "_" not in last_slug: continue

            if href in seen: continue
            seen.add(href)
            batch.append(href)
            if len(batch) >= 15: break

        return batch
