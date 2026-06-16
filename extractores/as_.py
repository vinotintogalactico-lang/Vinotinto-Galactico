from urllib.parse import urlparse
from playwright.async_api import Page
from extractores.generic import GenericExtractor

class AsExtractor(GenericExtractor):
    async def _get_article_links(self, page: Page) -> list[str]:
        # Sacamos la palabra clave del link del Excel (ej: 'real-madrid')
        keyword = [p for p in urlparse(self.url).path.split("/") if p][-1]
        
        seen, batch = set(), []
        # Buscamos solo en el área de noticias, no en el menú
        container = page.locator("main, .cnt-noticia, #sumario").first
        if await container.count() == 0: container = page

        all_links = await container.locator("a[href]").all()
        for el in all_links:
            href = await el.get_attribute("href")
            if not href: continue
            href = self._absolute(href)
            
            # FILTRO DE OBEDIENCIA: Si no es del dominio AS o no contiene la palabra clave, FUERA.
            if "as.com" not in href or keyword not in href.lower(): continue
            if any(b in href.lower() for b in ["/autor/", "/tags/", "/video/"]): continue
            
            if href not in seen:
                seen.add(href); batch.append(href)
            if len(batch) >= 15: break
        return batch