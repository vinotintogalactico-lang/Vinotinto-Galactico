"""Extractor para sport.es
Sport es un diario barcelonista - su sección /real-madrid/ existe pero
la navegación del sitio mezcla contenido de Barça.
Filtramos links para que solo incluyan /real-madrid/ (u otra sección del Excel) en el path.
"""
from urllib.parse import urlparse
from playwright.async_api import Page
from extractores.generic import GenericExtractor


class SportExtractor(GenericExtractor):

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

            subtitle = soup.select_one("h2.ft-c-article__subtitle, h2.subtitle, h2")
            subtitle_text = subtitle.get_text(strip=True) if subtitle else ""

            author = soup.select_one(".ft-c-article__author-name, .author, [rel='author']")
            author_text = author.get_text(strip=True) if author else ""

            date_text = ""
            time_el = soup.select_one("time[datetime]")
            if time_el and time_el.get("datetime"):
                date_text = time_el["datetime"]
            else:
                date_fallback = soup.select_one("time, .ft-c-article__date")
                date_text = date_fallback.get_text(strip=True) if date_fallback else ""

            art = parse_article(html, url, title=title_text, subtitle=subtitle_text,
                                author=author_text, date=date_text)
            return art if art.get("title") else None
        except Exception:
            return None

    async def _get_article_links_soup(self, soup) -> list[str]:
        seen: set[str] = set()
        links: list[str] = []

        path_parts = [p for p in urlparse(self.url).path.split("/") if p]
        section_kw = path_parts[-1] if path_parts else ""

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
            elements = soup.select(sel)
            for el in elements:
                href = el.get("href")
                if not href:
                    continue
                href = self._absolute(href)
                if "sport.es" not in href:
                    continue

                link_path = urlparse(href).path

                if section_kw in ["laliga", "primera"]:
                    pass
                elif section_kw and section_kw not in link_path and section_kw != "mundial":
                    continue

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
