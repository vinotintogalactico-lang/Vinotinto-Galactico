"""Extractor para marca.com
Filtra los links para que correspondan a la sección del Excel.
Ej: si el Excel da /futbol/real-madrid.html → solo acepta links con /real-madrid/ en su path.
"""
from urllib.parse import urlparse
from playwright.async_api import Page
from extractores.generic import GenericExtractor


def _section_keyword_from_url(url: str) -> str:
    """
    Extrae la palabra clave de sección del URL del Excel.
    Ej: /futbol/real-madrid.html -> "real-madrid"
         /futbol/futbol-femenino.html -> "futbol-femenino"
         /futbol/seleccion.html -> "seleccion"
    """
    path = urlparse(url).path
    # Tomar el último segmento y quitar la extensión
    segment = path.rstrip("/").split("/")[-1]
    segment = segment.replace(".html", "").split("?")[0]
    return segment  # e.g. "real-madrid", "seleccion", "primera-division"


class MarcaExtractor(GenericExtractor):

    async def _get_article_links_soup(self, soup) -> list[str]:
        seen: set[str] = set()
        links: list[str] = []

        section_kw = _section_keyword_from_url(self.url)

        selectors = [
            ".ue-c-cover-content__headline-group a[href]",
            ".titular a[href]",
            "main h2 a[href]",
            "main h3 a[href]",
            "main article a[href]",
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
                if "marca.com" not in href:
                    continue
                link_path = urlparse(href).path
                # Si la sección es primera-division o laliga, aceptamos todas las noticias de futbol
                if section_kw in ["primera-division", "laliga"]:
                    if "/futbol/" not in link_path:
                        continue
                elif section_kw and section_kw not in link_path and section_kw != "mundial":
                    continue
                if any(b in href for b in ["-directo.html", "/directo/", "/resultados/"]):
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

            subtitle = soup.select_one(".ue-c-article__standfirst, .subtitle")
            subtitle_text = subtitle.get_text(strip=True) if subtitle else ""

            author = soup.select_one(".ue-c-article__byline-name, .author")
            author_text = author.get_text(strip=True) if author else ""

            # Priorizar el atributo datetime del <time>
            date_text = ""
            time_el = soup.select_one("time[datetime]")
            if time_el and time_el.get("datetime"):
                date_text = time_el["datetime"]
            else:
                date_fallback = soup.select_one("time, .ue-c-article__publishdate")
                date_text = date_fallback.get_text(strip=True) if date_fallback else ""

            art = parse_article(html, url, title=title_text, subtitle=subtitle_text,
                                author=author_text, date=date_text)
            return art if art.get("title") else None
        except Exception:
            return None
