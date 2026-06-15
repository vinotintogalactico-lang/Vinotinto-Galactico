"""Extractor para meridiano.com.ve y otras fuentes venezolanas.
Usa la lógica genérica de escaneo de links del GenericExtractor.
"""
from playwright.async_api import Page
from extractores.generic import GenericExtractor


class MeridianoExtractor(GenericExtractor):

    async def _extract_article(self, context, url: str) -> dict | None:
        page = await context.new_page()
        try:
            from core.article_parser import parse_article
            from bs4 import BeautifulSoup

            await page.goto(url, timeout=25_000, wait_until="domcontentloaded")
            await page.wait_for_timeout(1500)
            html = await page.content()

            soup = BeautifulSoup(html, "html.parser")

            title = soup.find("h1")
            title_text = title.get_text(strip=True) if title else ""

            subtitle = soup.select_one("h2.subtitle, h2.bajada, h2.resumen")
            subtitle_text = subtitle.get_text(strip=True) if subtitle else ""

            author = soup.select_one(".author, .autor, .post-author")
            author_text = author.get_text(strip=True) if author else ""

            date_el = soup.select_one("time, .date, .fecha")
            date_text = date_el.get_text(strip=True) if date_el else ""

            art = parse_article(html, url, title=title_text, subtitle=subtitle_text,
                                author=author_text, date=date_text)
            return art if art.get("title") else None
        except Exception:
            return None
        finally:
            await page.close()
