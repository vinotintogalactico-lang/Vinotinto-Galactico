"""Extractor para estadiodeportivo.com"""
from playwright.async_api import Page
from urllib.parse import urlparse
from extractores.generic import GenericExtractor


class EstadioDeportivoExtractor(GenericExtractor):

    async def _get_article_links(self, page: Page) -> list[str]:
        seen: set[str] = set()
        links: list[str] = []

        # Aceptar cookies (usan sistema propio gdpr)
        for sel in [
            ".btn-gdpr-accept",
            "#btn-gdpr-accept",
            "button.gdpr-accept",
            "#didomi-notice-agree-button",
            "#onetrust-accept-btn-handler",
        ]:
            try:
                btn = page.locator(sel).first
                if await btn.is_visible(timeout=2000):
                    await btn.click()
                    await page.wait_for_timeout(1500)
                    break
            except Exception:
                pass

        for text in ["Aceptar todo", "Aceptar", "Accept"]:
            try:
                btn = page.get_by_role("button", name=text)
                if await btn.first.is_visible(timeout=500):
                    await btn.first.click()
                    await page.wait_for_timeout(1500)
                    break
            except Exception:
                pass

        # Esperar un poco más para que cargue el contenido
        await page.wait_for_timeout(2000)

        # Selectores específicos de Estadio Deportivo
        selectors = [
            ".news-title a[href]",
            ".article-title a[href]",
            "h2.title a[href]",
            "h3.title a[href]",
            ".post-title a[href]",
            "article h2 a[href]",
            "article h3 a[href]",
            ".entry-title a[href]",
            "main a[href]",
            "h2 a[href]",
            "h3 a[href]",
        ]

        # Extraer la "sección" de la URL base del Excel para filtrar links
        # Ej: /futbol/real-madrid/ → solo queremos links que contengan /real-madrid/
        base_path = urlparse(self.url).path  # e.g. /futbol/real-madrid/
        # Tomar el último segmento no vacío como keyword de sección
        path_parts = [p for p in base_path.split("/") if p]
        section_keyword = path_parts[-1] if path_parts else ""  # "real-madrid"

        for sel in selectors:
            elements = await page.query_selector_all(sel)
            for el in elements:
                href = await el.get_attribute("href")
                if not href:
                    continue
                href = self._absolute(href)
                if "estadiodeportivo.com" not in href:
                    continue
                # Si hay keyword de sección, filtrar por ella
                if section_keyword and section_keyword not in href:
                    continue
                if href not in seen and self._is_article_url(href):
                    seen.add(href)
                    links.append(href)
            if len(links) >= 9:
                break

        return links
