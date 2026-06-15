"""Extractor para marca.com
Usa estrategia híbrida: primero intenta selectores específicos, 
si falla usa escaneo genérico de links.
"""
from urllib.parse import urlparse
from playwright.async_api import Page
from extractores.generic import GenericExtractor


class MarcaExtractor(GenericExtractor):

    async def _get_article_links(self, page: Page) -> list[str]:
        # Aceptar cookies
        try:
            btn = page.locator("#didomi-notice-agree-button")
            if await btn.is_visible(timeout=2000):
                await btn.click()
                await page.wait_for_timeout(1500)
        except Exception:
            pass

        await page.wait_for_timeout(1500)

        # Intentar con selectores específicos de Marca (más ordenados)
        specific_selectors = [
            ".ue-c-cover-content__headline-group a[href]",
            ".titular a[href]",
            "main h2 a[href]",
            "main article a[href]",
        ]

        section_kw = ""
        path = urlparse(self.url).path
        segment = path.rstrip("/").split("/")[-1]
        segment = segment.replace(".html", "").split("?")[0]
        if segment:
            section_kw = segment

        for sel in specific_selectors:
            seen: set[str] = set()
            batch: list[str] = []
            elements = await page.query_selector_all(sel)
            for el in elements:
                href = await el.get_attribute("href")
                if not href:
                    continue
                href = self._absolute(href)
                if "marca.com" not in href:
                    continue
                link_path = urlparse(href).path
                if section_kw and section_kw not in link_path:
                    continue
                if any(b in href for b in ["-directo.html", "/directo/", "/resultados/"]):
                    continue
                if href not in seen:
                    seen.add(href)
                    batch.append(href)
                if len(batch) >= 15:
                    break
            if len(batch) >= 3:
                return batch

        # Fallback: usar escaneo genérico
        return await super()._get_article_links(page)
