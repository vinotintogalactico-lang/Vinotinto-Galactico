"""Extractor para mundodeportivo.com
Usa estrategia híbrida: selectores específicos primero, fallback genérico.
"""
from playwright.async_api import Page
from extractores.generic import GenericExtractor


class MundoDeportivoExtractor(GenericExtractor):

    async def _get_article_links(self, page: Page) -> list[str]:
        # Intentar selectores específicos
        specific = [
            ".js-noticia a[href]",
            ".noticia__titular a[href]",
            "h2 a[href]",
        ]
        for sel in specific:
            seen: set[str] = set()
            batch: list[str] = []
            elements = await page.query_selector_all(sel)
            for el in elements:
                href = await el.get_attribute("href")
                if href:
                    href = self._absolute(href)
                    if href not in seen and "mundodeportivo" in href:
                        seen.add(href)
                        batch.append(href)
                if len(batch) >= 15:
                    break
            if len(batch) >= 3:
                return batch

        # Fallback genérico
        return await super()._get_article_links(page)

    async def _extract_article(self, context, url: str) -> dict | None:
        page = await context.new_page()
        try:
            from core.article_parser import parse_article
            from bs4 import BeautifulSoup

            await page.goto(url, timeout=25_000, wait_until="domcontentloaded")
            await page.wait_for_timeout(1500)

            try:
                btn = page.locator("#didomi-notice-agree-button")
                if await btn.is_visible(timeout=1000):
                    await btn.click()
                    await page.wait_for_timeout(1000)
            except Exception:
                pass

            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")

            title = soup.find("h1")
            title_text = title.get_text(strip=True) if title else ""

            subtitle = soup.select_one("h2.epigraph, .article-subtitle, .subtitle")
            subtitle_text = subtitle.get_text(strip=True) if subtitle else ""

            author = soup.select_one(".author-name, .article-author, .author")
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
        finally:
            await page.close()
