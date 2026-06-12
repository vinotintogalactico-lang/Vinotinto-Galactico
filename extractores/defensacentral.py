"""Extractor para defensacentral.com"""
from playwright.async_api import Page
from extractores.generic import GenericExtractor


class DefensacentralExtractor(GenericExtractor):

    async def _get_article_links(self, page: Page) -> list[str]:
        # Selectores específicos de Defensa Central
        selectors = [
            "li.c-highlight__item a[href]",
            "div.c-breaking-news__wrapper a[href]",
            ".c-news-list a[href]",
            ".c-article-list a[href]",
            "article a[href]",
            "h2 a[href]",
            "h3 a[href]",
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
                # Aceptar cualquier artículo del dominio (no solo /actualidad/)
                if href not in seen and self._is_article_url(href) and "defensacentral.com" in href:
                    seen.add(href)
                    batch.append(href)
                if len(batch) >= 15:
                    break

            if len(batch) >= 3:
                return batch

        return []
