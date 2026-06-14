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
TIMEOUT_MS = 20_000
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


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
        """
        Devuelve (lista_noticias, log_entry).
        """
        noticias: list[dict] = []
        log: dict = {
            "fuente": self.fuente,
            "encontradas": 0,
            "extraidas": 0,
            "estado": "",
            "error": "",
        }

        browser = None
        try:
            async with async_playwright() as pw:
                # OPTIMIZACIÓN CLAVE: Argumentos para no saturar la RAM en Streamlit Cloud
                browser = await pw.chromium.launch(
                    headless=True,
                    args=[
                        "--disable-dev-shm-usage",
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-gpu",
                        "--single-process"
                    ]
                )
                
                try:
                    context: BrowserContext = await browser.new_context(
                        user_agent=USER_AGENT,
                        viewport={"width": 1280, "height": 900},
                        ignore_https_errors=True,
                    )
                    page: Page = await context.new_page()
                    
                    try:
                        await page.goto(self.url, timeout=TIMEOUT_MS, wait_until="domcontentloaded")
                        await page.wait_for_timeout(2000)  # breve espera para JS
                    except Exception as goto_exc:
                        raise Exception(f"No se pudo cargar la página principal (Timeout o Bloqueo): {goto_exc}")

                    links = await self._get_article_links(page)
                    log["encontradas"] = len(links)

                    for link in links:
                        if len(noticias) >= MAX_NEWS:
                            break
                        try:
                            articulo = await self._extract_article(context, link)
                            if articulo:
                                # 1. Filtro estricto por palabras clave y cuerpo
                                if not is_valid_content(articulo.get("title", ""), self.categoria, articulo.get("body", "")):
                                    continue
                                
                                # 2. Filtro estricto de fecha
                                valid_date, _log = is_today(articulo.get("date", ""))
                                if valid_date:
                                    articulo["fuente"] = self.fuente
                                    articulo["categoria"] = self.categoria
                                    noticias.append(articulo)
                        except Exception as exc:
                            logger.warning("Error en artículo %s: %s", link, exc)

                finally:
                    # BLOQUEO DE SEGURIDAD: Garantiza que la RAM se limpie sin importar el error
                    if browser:
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
    async def _extract_article(self, context: BrowserContext, url: str) -> dict | None:
        page: Page = await context.new_page()
        try:
            await page.goto(url, timeout=TIMEOUT_MS, wait_until="domcontentloaded")
            await page.wait_for_timeout(1500)

            # Intentar aceptar cookies si hay un popup bloqueando
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

            # Intentar extraer fecha del atributo datetime antes de pasar el HTML
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

    def _is_article_url(self, url: str) -> bool:
        """Filtrar URLs que parecen artículos y no secciones/índices/autores."""
        bad = (
            "#", "javascript:", "mailto:", ".pdf", ".jpg", ".png", ".gif", ".mp4",
            "/autor/", "/author/", "/firmas/", "/tags/", "/etiquetas/", 
            "/resultados/", "/clasificacion/", "/calendario/",
            "/page/", "/category/", "/categoria/", "/seccion/"
        )
        for b in bad:
            if b in url.lower():
                return False
        # Debe pertenecer al mismo dominio
        from urllib.parse import urlparse
        base_domain = urlparse(self.url).netloc.replace("www.", "")
        url_domain = urlparse(url).netloc.replace("www.", "")
        return base_domain in url_domain or url_domain in base_domain