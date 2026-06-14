"""Extractor para sport.es
Sport es un diario barcelonista - su sección /real-madrid/ existe pero
la navegación del sitio mezcla contenido de Barça.
Filtramos links para que solo incluyan /real-madrid/ (u otra sección del Excel) en el path.
"""
from urllib.parse import urlparse
from playwright.async_api import Page
from mundial.extractores.generic_mundial import GenericExtractor


class SportExtractor(GenericExtractor):

    async def _get_article_links(self, page: Page) -> list[str]:
        seen: set[str] = set()
        links: list[str] = []

        # Aceptar cookies de Sport.es — usa sistema propio (ft-consent) o didomi
        cookie_accepted = False
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
                    cookie_accepted = True
                    break
            except Exception:
                pass

        if not cookie_accepted:
            for text in ["Aceptar todo", "Aceptar", "Accept all", "ACEPTAR"]:
                try:
                    btn = page.get_by_role("button", name=text)
                    if await btn.first.is_visible(timeout=800):
                        await btn.first.click()
                        await page.wait_for_timeout(1500)
                        cookie_accepted = True
                        break
                except Exception:
                    pass

        await page.wait_for_timeout(1000)

        # Keyword de sección del URL del Excel
        # Ej: /es/real-madrid/ -> "real-madrid"
        #     /es/laliga/ -> "laliga"
        path_parts = [p for p in urlparse(self.url).path.split("/") if p]
        section_kw = path_parts[-1] if path_parts else ""  # "real-madrid"

        selectors = [
            ".ft-c-content-list__item a[href]",
            ".ft-c-article__title a[href]",
            ".ft-c-card__title a[href]",
            ".ft-c-card a[href]",
            "article a[href]",
            "h2 a[href]",
            "h3 a[href]",
            "main a[href]",
        ]

        for sel in selectors:
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

                # El link debe contener la keyword de la sección del Excel
                if section_kw and section_kw not in link_path:
                    continue

                # Excluir páginas de sección/home exactas
                if link_path.rstrip("/") in [f"/es/{section_kw}", f"/es/{section_kw}/"]:
                    continue

                if href not in seen and self._is_article_url(href):
                    seen.add(href)
                    batch.append(href)
                if len(batch) >= 15 * 3:
                    break

            if len(batch) >= 3:
                return batch

        return []
