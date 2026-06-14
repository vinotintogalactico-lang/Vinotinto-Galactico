"""Extractor para mundodeportivo.com"""
from urllib.parse import urlparse
from extractores.generic import GenericExtractor

class MundoDeportivoExtractor(GenericExtractor):

    async def _get_article_links_soup(self, soup) -> list[str]:
        selectors = [
            ".js-noticia a[href]",
            ".noticia__titular a[href]",
            "h2 a[href]",
            "h3 a[href]",
            "article a[href]",
        ]

        for sel in selectors:
            seen: set[str] = set()
            batch: list[str] = []
            elements = soup.select(sel)
            for el in elements:
                href = el.get("href")
                if href:
                    href = self._absolute(href)
                    if href not in seen and self._is_article_url(href):
                        seen.add(href)
                        batch.append(href)
                if len(batch) >= 15 * 3:
                    break

            if len(batch) >= 3:
                return batch

        return []

    async def _extract_article_requests(self, url: str) -> dict | None:
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
            soup_article = BeautifulSoup(html, "html.parser")

            title = soup_article.find("h1")
            title_text = title.get_text(strip=True) if title else ""

            subtitle = soup_article.select_one("h2.epigraph, .article-subtitle, .subtitle")
            subtitle_text = subtitle.get_text(strip=True) if subtitle else ""

            author = soup_article.select_one(".author-name, .article-author, .author")
            author_text = author.get_text(strip=True) if author else ""

            date_text = ""
            time_el = soup_article.select_one("time[datetime]")
            if time_el and time_el.get("datetime"):
                date_text = time_el["datetime"]
            else:
                date_fallback = soup_article.select_one("time, .article-date")
                date_text = date_fallback.get_text(strip=True) if date_fallback else ""

            art = parse_article(html, url, title=title_text, subtitle=subtitle_text,
                                author=author_text, date=date_text)
            return art if art.get("title") else None
        except Exception:
            return None
