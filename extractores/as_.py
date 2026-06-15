"""Extractor para as.com
Usa estrategia robusta: agarrar TODOS los links, filtrar por patrón de URL de artículo.
"""
from urllib.parse import urlparse
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

        # Esperar a que React termine de renderizar
        await page.wait_for_timeout(2000)

        bad_segments = [
            "/resultados/", "/ficha/", "-directo", "/clasificacion/",
            "/plantilla/", "/calendario/", "/autor/", "/tags/",
            "/seccion/", "/foto/", "/video/", "/encuesta/",
        ]

        seen: set[str] = set()
        batch: list[str] = []

        # Agarrar TODOS los links y filtrar por patrón de artículo
        all_links = await page.locator("a[href]").all()
        for el in all_links:
            href = await el.get_attribute("href")
            if not href:
                continue
            href = self._absolute(href)
            if "as.com" not in href:
                continue
            if any(b in href for b in bad_segments):
                continue
            if href in seen:
                continue
            if not self._is_article_url(href):
                continue

            # AS artículos típicos: /futbol/20250614/xxxx-xxx.html o /futbol/articulo/xxxx
            path = urlparse(href).path
            # Un artículo real tiene al menos 3 segmentos de profundidad
            segments = [p for p in path.split("/") if p]
            if len(segments) < 3:
                continue
            # Si tiene una fecha numérica (YYYYMMDD) en algún segmento, es artículo
            has_date_segment = any(s.isdigit() and len(s) == 8 for s in segments)
            # O tiene un slug con guiones (noticia real)
            last_slug = segments[-1].replace(".html", "")
            has_long_slug = last_slug.count("-") >= 2

            if not (has_date_segment or has_long_slug):
                continue

            seen.add(href)
            batch.append(href)
            if len(batch) >= 15:
                break

        return batch

    async def _extract_article(self, context, url: str) -> dict | None:
        page = await context.new_page()
        try:
            from core.article_parser import parse_article
            from bs4 import BeautifulSoup

            await page.goto(url, timeout=20_000, wait_until="domcontentloaded")
            await page.wait_for_timeout(1500)

            # Aceptar cookies si aparecen
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
