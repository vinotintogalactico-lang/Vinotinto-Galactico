"""
Extractor genérico.
Funciona para la mayoría de fuentes; los extractores específicos
sobrescriben métodos cuando la estructura del sitio lo requiere.
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

# Args SEGUROS para Streamlit Cloud — SIN --single-process que revienta todo
CHROMIUM_ARGS = [
    "--disable-dev-shm-usage",
    "--no-sandbox",
    "--disable-gpu",
    "--disable-setuid-sandbox",
    "--disable-software-rasterizer",
    "--js-flags=--max-old-space-size=256"
]


class GenericExtractor:
    """
    Flujo:
      1. Abre la URL de sección.
      2. Recoge enlaces de artículos (evitando sidebars).
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

        # -------------------------------------------------------------
        # NUEVO MODO LIGERO (Cero consumo de RAM)
        # -------------------------------------------------------------
        if getattr(self, "use_requests", True):
            try:
                import requests
                import asyncio
                from bs4 import BeautifulSoup
                
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept-Language": "es-ES,es;q=0.9",
                }
                
                resp = await asyncio.to_thread(requests.get, self.url, headers=headers, timeout=20.0)
                if resp.status_code != 200:
                    raise Exception(f"HTTP Error {resp.status_code}")
                    
                html = resp.text
                soup = BeautifulSoup(html, "html.parser")
                
                links = await self._get_article_links_soup(soup)
                log["encontradas"] = len(links)
                
                for link in links:
                    if len(noticias) >= MAX_NEWS:
                        break
                    try:
                        articulo = await self._extract_article_requests(link)
                        if articulo:
                            if not is_valid_content(articulo.get("title", ""), self.categoria, articulo.get("body", "")):
                                continue

                            es_mundial = (self.categoria == "Mundial Global")
                            valid_date, _log = is_today(
                                articulo.get("date", ""),
                                allow_empty=es_mundial,
                                allow_yesterday=es_mundial
                            )
                            if valid_date:
                                articulo["fuente"] = self.fuente
                                articulo["categoria"] = self.categoria
                                noticias.append(articulo)
                    except Exception as exc:
                        logger.warning("Error en artículo %s: %s", link, exc)

            except Exception as exc:
                log["error"] = str(exc)
                log["estado"] = "Error"
                logger.error("Error en fuente %s: %s", self.fuente, exc)
                return noticias, log

            log["extraidas"] = len(noticias)
            log["estado"] = "Correcto" if noticias else "Sin noticias del día"
            return noticias, log

        # -------------------------------------------------------------
        # MODO PLAYWRIGHT (Antiguo, solo para apps React/SPA)
        # -------------------------------------------------------------
        try:
            async with async_playwright() as pw:
                browser: Browser = await pw.chromium.launch(headless=True, args=CHROMIUM_ARGS)
                context: BrowserContext = await browser.new_context(
                    user_agent=USER_AGENT,
                    viewport={"width": 1280, "height": 900},
                    ignore_https_errors=True,
                )

                async def route_intercept(route):
                    req = route.request
                    if req.resource_type == "media":
                        await route.abort()
                    elif any(ad in req.url for ad in ["googleads", "doubleclick", "taboola", "outbrain", "criteo", "teads"]):
                        await route.abort()
                    else:
                        await route.continue_()
                await context.route("**/*", route_intercept)

                page: Page = await context.new_page()
                await page.goto(self.url, timeout=TIMEOUT_MS, wait_until="domcontentloaded")
                await page.wait_for_timeout(2000)

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
                            es_mundial = (self.categoria == "Mundial Global")
                            valid_date, _log = is_today(
                                articulo.get("date", ""),
                                allow_empty=es_mundial,
                                allow_yesterday=es_mundial
                            )
                            if valid_date:
                                articulo["fuente"] = self.fuente
                                articulo["categoria"] = self.categoria
                                noticias.append(articulo)
                    except Exception as exc:
                        logger.warning("Error en artículo %s: %s", link, exc)
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
        Estrategia: probar selectores de contenedor principal de uno en uno.
        En cuanto el primero devuelva >= 3 links válidos, usamos SOLO esos.
        Así los links quedan en el orden exacto de la página (más reciente primero)
        y no se "mezclan" con links de sidebars/footers de otros selectores.
        """
        # Selectores ordenados de más específico (contenedor principal) a más genérico
        selectors = [
            "main a[href]",
            "#main a[href]",
            ".main-content a[href]",
            ".site-main a[href]",
            "article a[href]",
            "h2 a[href]",
            "h3 a[href]",
        ]

        for sel in selectors:
            seen: set[str] = set()
            batch: list[str] = []
            elements = await page.query_selector_all(sel)
            for el in elements:
                href = await el.get_attribute("href")
                if href:
                    href = self._absolute(href)
                    if href and href not in seen and self._is_article_url(href):
                        seen.add(href)
                        batch.append(href)
                # Recogemos hasta MAX_NEWS*3 candidatos en orden de página
                if len(batch) >= 15:
                    break

            # En cuanto un selector nos dé al menos 3 candidatos, lo usamos solo
            if len(batch) >= 3:
                return batch

        return []

    # ── Extracción de artículo individual ───────────────────────────────────
    async def _get_article_links_soup(self, soup) -> list[str]:
        return []

    async def _extract_article_requests(self, url: str) -> dict | None:
        try:
            from core.article_parser import parse_article
            import requests
            import asyncio
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "es-ES,es;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            }
            
            resp = await asyncio.to_thread(requests.get, url, headers=headers, timeout=15.0)
            if resp.status_code != 200:
                return None
            
            html = resp.text
            from bs4 import BeautifulSoup
            soup_article = BeautifulSoup(html, "html.parser")

            title = soup_article.find("h1")
            title_text = title.get_text(strip=True) if title else ""

            subtitle = soup_article.select_one("h2, .subtitle, .standfirst")
            subtitle_text = subtitle.get_text(strip=True) if subtitle else ""

            author = soup_article.select_one(".author, [rel='author']")
            author_text = author.get_text(strip=True) if author else ""

            date_text = ""
            time_el = soup_article.select_one("time[datetime]")
            if time_el and time_el.get("datetime"):
                date_text = time_el["datetime"]
            else:
                date_fallback = soup_article.select_one("time, .date")
                date_text = date_fallback.get_text(strip=True) if date_fallback else ""

            art = parse_article(html, url, title=title_text, subtitle=subtitle_text,
                                author=author_text, date=date_text)
            return art if art.get("title") else None
        except Exception:
            return None


    # ── Utilidades ───────────────────────────────────────────────────────────
    def _absolute(self, href: str) -> str:
        if href.startswith("http"):
            return href
        from urllib.parse import urlparse, urljoin
        return urljoin(self.url, href)

    def _is_article_url(self, url: str) -> bool:
        """Filtrar URLs que parecen artículos y no secciones/índices/autores."""
        bad = (
            "#", "javascript:", "mailto:", ".pdf", ".jpg", ".png", ".gif", ".mp4",
            "/autor/", "/author/", "/firmas/", "/tags/", "/etiquetas/",
            "/resultados/", "/clasificacion/", "/calendario/",
            "/page/", "/category/", "/categoria/"
        )
        for b in bad:
            if b in url.lower():
                return False
        # Debe pertenecer al mismo dominio
        from urllib.parse import urlparse
        base_domain = urlparse(self.url).netloc.replace("www.", "")
        url_domain = urlparse(url).netloc.replace("www.", "")
        return base_domain in url_domain or url_domain in base_domain
