"""Extractor para as.com
Navega a la sección exacta del Excel y recoge links del área principal de noticias.
NO filtra por prefijo de URL ya que los artículos de As tienen paths distintos a la sección.
"""
from playwright.async_api import Page
from extractores.generic import GenericExtractor


class AsExtractor(GenericExtractor):

    async def _get_article_links(self, page: Page) -> list[str]:
        # Aceptar cookies
        try:
            btn = page.locator("#didomi-notice-agree-button")
            if await btn.is_visible(timeout=2000):
                await btn.click()
                await page.wait_for_timeout(1500)
        except Exception:
            pass

        # Selectores ordenados: el primero que devuelva >= 3 links en orden de página gana
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
            elements = await page.query_selector_all(sel)
            for el in elements:
                href = await el.get_attribute("href")
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
        page = await context.new_page()
        try:
            from core.article_parser import parse_article
            from bs4 import BeautifulSoup

            await page.goto(url, timeout=20_000, wait_until="domcontentloaded")
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

            subtitle = soup.select_one("h2.article-body__subtitle, h2.s-entradilla, .subtitle")
            subtitle_text = subtitle.get_text(strip=True) if subtitle else ""

            author = soup.select_one(".article-author__name, .s-autor-name, .author")
            author_text = author.get_text(strip=True) if author else ""

            # Priorizar el atributo datetime del <time>
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
