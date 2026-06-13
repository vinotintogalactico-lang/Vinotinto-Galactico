"""Extractor para estadiodeportivo.com"""
from playwright.async_api import Page
from urllib.parse import urlparse
from extractores.generic import GenericExtractor


class EstadioDeportivoExtractor(GenericExtractor):

    async def _get_article_links_soup(self, soup) -> list[str]:
        seen: set[str] = set()
        links: list[str] = []

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

        base_path = urlparse(self.url).path
        path_parts = [p for p in base_path.split("/") if p]
        section_keyword = path_parts[-1] if path_parts else ""

        for sel in selectors:
            elements = soup.select(sel)
            for el in elements:
                href = el.get("href")
                if not href:
                    continue
                href = self._absolute(href)
                if "estadiodeportivo.com" not in href:
                    continue
                if section_keyword and section_keyword not in href:
                    continue
                if href not in seen and self._is_article_url(href):
                    seen.add(href)
                    links.append(href)
            if len(links) >= 9:
                break

        return links
