"""Extractor para sport.es
Usa estrategia híbrida: selectores específicos primero, fallback genérico.
Sport mezcla contenido de Barça; debemos filtrar por keyword de sección.
"""
from urllib.parse import urlparse
from playwright.async_api import Page
from extractores.generic import GenericExtractor


class SportExtractor(GenericExtractor):

    async def _get_article_links(self, page: Page) -> list[str]:
        # Aceptar cookies
        for sel in [
            "#didomi-notice-agree-button",
            "button.ft-btn--primary",
            "#onetrust-accept-btn-handler",
            ".ft-c-consent-wall__btn",
        ]:
            try:
                btn = page.locator(sel).first
                if await btn.is_visible(timeout=2000):
                    await btn.click()
                    await page.wait_for_timeout(1500)
                    break
            except Exception:
                pass

        await page.wait_for_timeout(1500)

        # Keyword de sección
        path_parts = [p for p in urlparse(self.url).path.split("/") if p]
        section_kw = path_parts[-1] if path_parts else ""

        # Intentar selectores específicos
        specific = [
            ".ft-c-content-list__item a[href]",
            ".ft-c-article__title a[href]",
            ".ft-c-card__title a[href]",
            "article a[href]",
        ]

        for sel in specific:
            seen: set[str] = set()
            batch: list[str] = []
            elements = await page.query_selector_all(sel)
            for el in elements:
                href = await el.get_attribute("href")
                if not href:
                    continue
                href = self._absolute(href)
                if "sport.es" not in href:
                    continue
                link_path = urlparse(href).path
                if section_kw and section_kw not in link_path:
                    continue
                if link_path.rstrip("/") in [f"/es/{section_kw}", f"/es/{section_kw}/"]:
                    continue
                if href not in seen:
                    seen.add(href)
                    batch.append(href)
                if len(batch) >= 15:
                    break
            if len(batch) >= 3:
                return batch

        # Fallback: escaneo genérico (hereda de GenericExtractor)
        return await super()._get_article_links(page)
