"""
Extractor genérico.
Funciona para la mayoría de fuentes; los extractores específicos
sobrescriben métodos cuando la estructura del sitio lo requiere.

Estrategia de enlaces: escanea TODOS los <a> de la página y filtra
por patrón de artículo en lugar de depender de selectores CSS frágiles.
"""
from __future__ import annotations
import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from core.article_parser import parse_article
from core.date_validator import is_today
from core.content_filter import is_valid_content

logger = logging.getLogger(__name__)

MAX_NEWS = 3
TIMEOUT_MS = 25_000
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


class GenericExtractor:
    """
    Flujo:
      1. Abre la URL de sección.
      2. Recoge enlaces de artículos.
      3. Abre cada artículo, extrae su contenido.
      4. Valida palabras clave según categoría.
      5. Valida fecha.
    """

    def __init__(self, fuente: str, url: str, categoria: str):
        self.fuente = fuente
        self.url = url
        self.categoria = categoria

    # ── Punto de entrada ────────────────────────────────────────────────────
    async def extract(self) -> tuple[list[dict], dict]:
        noticias: list[dict] = []
        log: dict = {
            "fuente": self.fuente,
            "encontradas": 0,
            "extraidas": 0,
            "estado": "",
            "error": "",
        }

        try:
            async with async_playwright() as pw:
                browser: Browser = await pw.chromium.launch(headless=True)
                context: BrowserContext = await browser.new_context(
                    user_agent=USER_AGENT,
                    viewport={"width": 1280, "height": 900},
                    ignore_https_errors=True,
                )
                page: Page = await context.new_page()
                await page.goto(self.url, timeout=TIMEOUT_MS, wait_until="domcontentloaded")
                await page.wait_for_timeout(3000)

                links = await self._get_article_links(page)
                log["encontradas"] = len(links)

                for link in links:
                    if len(noticias) >= MAX_NEWS:
                        break
                    try:
                        articulo = await self._extract_article(context, link)
                        if articulo:
                            if not is_valid_content(articulo.get("title", ""), self.categoria, articulo.get("body", "")):
                                continue
                            valid_date, date_log = is_today(articulo.get("date", ""))
                            if valid_date:
                                articulo["fuente"] = self.fuente
                                articulo["categoria"] = self.categoria
                                noticias.append(articulo)
                    except Exception as exc:
                        logger.error("Error en artículo %s: %s", link, exc)
                        import traceback
                        logger.error(traceback.format_exc())

                await browser.close()

        except Exception as exc:
            log["error"] = str(exc)
            log["estado"] = "Error"
            logger.error("Error en fuente %s: %s", self.fuente, exc)
            return noticias, log

        log["extraidas"] = len(noticias)
        log["estado"] = "Correcto" if noticias else "Sin noticias del día"
        return noticias, log

    # ── Recolección de enlaces ───────────────────────────────────────────────
    async def _get_article_links(self, page: Page) -> list[str]:
        """
        Estrategia robusta: agarra TODOS los <a> de la página y filtra
        por patrón de URL de artículo. No depende de selectores CSS frágiles.
        """
        # Bad segments globales que nunca son artículos
        bad_segments = (
            "#", "javascript:", "mailto:", ".pdf", ".jpg", ".png", ".gif", ".mp4",
            "/autor/", "/author/", "/firmas/", "/tags/", "/etiquetas/",
            "/resultados/", "/clasificacion/", "/calendario/",
            "/page/", "/category/", "/categoria/", "/seccion/",
            "/foto/", "/video/", "/galeria/", "/encuesta/",
            "-directo", "/directo/",
        )

        seen: set[str] = set()
        batch: list[str] = []

        all_links = await page.locator("a[href]").all()
        for el in all_links:
            href = await el.get_attribute("href")
            if not href:
                continue
            href = self._absolute(href)

            # Debe pertenecer al mismo dominio base
            if not self._is_same_domain(href):
                continue

            # Excluir bad segments
            href_lower = href.lower()
            if any(b in href_lower for b in bad_segments):
                continue

            if href in seen:
                continue

            # Un artículo real tiene una ruta con al menos 3 segmentos
            from urllib.parse import urlparse
            path = urlparse(href).path
            segments = [p for p in path.split("/") if p]
            if len(segments) < 3:
                continue

            # El último slug debe tener al menos 2 guiones (noticia con título descriptivo)
            # o contener una fecha numérica
            last_slug = segments[-1].replace(".html", "").replace(".htm", "")
            has_long_slug = last_slug.count("-") >= 2
            has_date = any(s.isdigit() and len(s) == 8 for s in segments)

            if not (has_long_slug or has_date):
                continue

            seen.add(href)
            batch.append(href)
            if len(batch) >= 15:
                break

        return batch

    # ── Extracción de artículo individual ───────────────────────────────────
    async def _extract_article(self, context: BrowserContext, url: str) -> dict | None:
        page: Page = await context.new_page()
        try:
            await page.goto(url, timeout=TIMEOUT_MS, wait_until="domcontentloaded")
            await page.wait_for_timeout(1500)

            try:
                btn = page.locator(
                    "#didomi-notice-agree-button, .didomi-continue-without-agreeing, "
                    ".cmplz-accept, #onetrust-accept-btn-handler"
                )
                if await btn.first.is_visible(timeout=800):
                    await btn.first.click()
                    await page.wait_for_timeout(1000)
            except Exception:
                pass

            html = await page.content()

            from bs4 import BeautifulSoup as _BS
            _soup = _BS(html, "html.parser")
            date_text = ""
            _time = _soup.select_one("time[datetime]")
            if _time and _time.get("datetime"):
                date_text = _time["datetime"]

            art = parse_article(html, url, date=date_text)
            return art if art.get("title") else None
        except Exception as exc:
            logger.warning("No se pudo abrir %s: %s", url, exc)
            return None
        finally:
            await page.close()

    # ── Utilidades ───────────────────────────────────────────────────────────
    def _absolute(self, href: str) -> str:
        if href.startswith("http"):
            return href
        from urllib.parse import urlparse, urljoin
        return urljoin(self.url, href)

    def _is_same_domain(self, url: str) -> bool:
        from urllib.parse import urlparse
        base_domain = urlparse(self.url).netloc.replace("www.", "")
        url_domain = urlparse(url).netloc.replace("www.", "")
        return base_domain in url_domain or url_domain in base_domain

    def _is_article_url(self, url: str) -> bool:
        """Método legacy mantenido por compatibilidad con extractores hijos."""
        return self._is_same_domain(url)
