"""Extractor para as.com
Navega a la sección exacta del Excel y recoge links del área principal de noticias.
NO filtra por prefijo de URL ya que los artículos de As tienen paths distintos a la sección.
"""
from playwright.async_api import Page
from extractores.generic import GenericExtractor


class AsExtractor(GenericExtractor):

    async def _get_article_links_soup(self, soup) -> list[str]:
        selectors = [
            ".a-article-snapshot a[href]",
            ".a-article-list__item a[href]",
            ".h-list__item a[href]",
            "article.a-article a[href]",
            ".content-list a[href]",
            "main h2 a[href]",
            "main h3 a[href]",
            "main a[href]",
        ]

        bad_segments = ["/resultados/", "/ficha/", "-directo", "/clasificacion/",
                        "/plantilla/", "/calendario/"]

        for sel in selectors:
            seen: set[str] = set()
            batch: list[str] = []
            elements = soup.select(sel)
            for el in elements:
                href = el.get("href")
                if not href:
                    continue
                href = self._absolute(href)
                if "as.com" not in href:
                    continue
                if any(b in href for b in bad_segments):
                    continue
                if href not in seen and self._is_article_url(href):
                    seen.add(href)
                    batch.append(href)
                if len(batch) >= 15:
                    break

            if len(batch) >= 3:
                return batch

        return []

    async def _extract_article(self, context, url: str) -> dict | None:
        try:
            from core.article_parser import parse_article
            import requests
            import asyncio
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept-Language": "es-ES,es;q=0.9",
            }
            resp = await asyncio.to_thread(requests.get, url, headers=headers, timeout=15.0)
            if resp.status_code != 200:
                return None
                
            html = resp.text
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")

            title = soup.find("h1")
            title_text = title.get_text(strip=True) if title else ""

            subtitle = soup.select_one("h2.article-body__subtitle, h2.s-entradilla, .subtitle")
            subtitle_text = subtitle.get_text(strip=True) if subtitle else ""

            author = soup.select_one(".article-author__name, .s-autor-name, .author")
            author_text = author.get_text(strip=True) if author else ""

            date_text = ""
            time_el = soup.select_one("time[datetime]")
            if time_el and time_el.get("datetime"):
                date_text = time_el["datetime"]
            else:
                date_fallback = soup.select_one("time, .article-date")
                date_text = date_fallback.get_text(strip=True) if date_fallback else ""

            art = parse_article(html, url, title=title_text, subtitle=subtitle_text,
                                author=author_text, date=date_text)
            return art if art.get("title") else None
        except Exception:
            return None
