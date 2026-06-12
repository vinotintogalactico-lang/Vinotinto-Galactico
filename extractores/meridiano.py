"""Extractor para meridiano.net"""
from playwright.async_api import Page, BrowserContext
from extractores.generic import GenericExtractor


class MeridianoExtractor(GenericExtractor):

    async def _get_article_links_soup(self, soup) -> list[str]:
        selectors = [
            ".article-list__item a[href]",
            ".post-title a[href]",
            "h2 a[href]",
            "h3 a[href]",
            "article a[href]",
            ".entry-title a[href]",
        ]
        seen: set[str] = set()
        links: list[str] = []
        for sel in selectors:
            elements = soup.select(sel)
            for el in elements:
                href = el.get("href")
                if href:
                    href = self._absolute(href)
                    if href not in seen and self._is_meridiano_article(href):
                        seen.add(href)
                        links.append(href)
            if len(links) >= 9:
                break
        return links

    def _is_meridiano_article(self, url: str) -> bool:
        """Filtro específico para Meridiano — acepta su estructura de URLs."""
        bad = ("#", "javascript:", "mailto:", ".pdf", ".jpg", ".png", ".gif",
               "/autor/", "/tags/", "/page/")
        for b in bad:
            if b in url.lower():
                return False
        return "meridiano.net" in url

    async def _extract_article(self, context: BrowserContext, url: str) -> dict | None:
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

            subtitle = soup.select_one("h2.subtitle, h2.bajada, h2.resumen")
            subtitle_text = subtitle.get_text(strip=True) if subtitle else ""

            author = soup.select_one(".author, .autor, .post-author")
            author_text = author.get_text(strip=True) if author else ""

            # Priorizar el atributo datetime
            date_el = soup.select_one("time[datetime]")
            if date_el and date_el.get("datetime"):
                date_text = date_el["datetime"]
            else:
                date_el = soup.select_one("time, .date, .fecha")
                date_text = date_el.get_text(strip=True) if date_el else ""

            art = parse_article(html, url, title=title_text, subtitle=subtitle_text, author=author_text, date=date_text)
            return art if art.get("title") else None
        except Exception:
            return None
