"""Extractor para as.com
Navega a la sección exacta del Excel y recoge links del área principal de noticias.
AS.com tiene protección Cloudflare, necesita Playwright para la portada.
Los artículos individuales se leen con requests (más ligero).
"""
from playwright.async_api import Page, BrowserContext
from extractores.generic import GenericExtractor

BAD_SEGMENTS = ["/resultados/", "/ficha/", "-directo", "/clasificacion/",
                "/plantilla/", "/calendario/"]

SELECTORS = [
    ".a-article-snapshot a[href]",
    ".a-article-list__item a[href]",
    ".h-list__item a[href]",
    "article.a-article a[href]",
    ".content-list a[href]",
    "main h2 a[href]",
    "main h3 a[href]",
    "main a[href]",
]


class AsExtractor(GenericExtractor):
    # Usa Playwright para la portada (AS bloquea requests con 403)
    use_requests = False

    async def _get_article_links(self, page: Page) -> list[str]:
        # Aceptar cookies si aparecen
        try:
            btn = page.locator("#didomi-notice-agree-button")
            if await btn.is_visible(timeout=2000):
                await btn.click()
                await page.wait_for_timeout(1000)
        except Exception:
            pass

        for sel in SELECTORS:
            seen: set[str] = set()
            batch: list[str] = []
            elements = await page.query_selector_all(sel)
            for el in elements:
                href = await el.get_attribute("href")
                if not href:
                    continue
                href = self._absolute(href)
                if "as.com" not in href:
                    continue
                if any(b in href for b in BAD_SEGMENTS):
                    continue
                if href not in seen and self._is_article_url(href):
                    seen.add(href)
                    batch.append(href)
                if len(batch) >= 15:
                    break

            if len(batch) >= 3:
                return batch

        return []

    async def _extract_article(self, context: BrowserContext, url: str) -> dict | None:
        """Abre el artículo con requests (mucho más ligero que Playwright)."""
        try:
            from core.article_parser import parse_article
            import requests
            import asyncio
            from bs4 import BeautifulSoup

            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "es-ES,es;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Referer": "https://as.com/",
            }
            resp = await asyncio.to_thread(
                requests.get, url, headers=headers, timeout=15.0
            )
            if resp.status_code != 200:
                return None

            html = resp.text
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
