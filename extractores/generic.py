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
import gc
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from core.article_parser import parse_article
from core.date_validator import is_today
from core.content_filter import is_valid_content

logger = logging.getLogger(__name__)

MAX_NEWS = 3
TIMEOUT_MS = 25_000
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

class GenericExtractor:
    def __init__(self, fuente: str, url: str, categoria: str):
        self.fuente = fuente
        self.url = url
        self.categoria = categoria

    async def extract(self) -> tuple[list[dict], dict]:
        # TRUCO 1: Limpiamos la basura de la RAM antes de empezar
        gc.collect() 
        
        noticias: list[dict] = []
        log: dict = {"fuente": self.fuente, "encontradas": 0, "extraidas": 0, "estado": "", "error": ""}

        try:
            async with async_playwright() as pw:
                browser: Browser = await pw.chromium.launch(
                    headless=True,
                    args=[
                        "--disable-dev-shm-usage",
                        "--no-sandbox",
                        "--disable-gpu",
                        "--disable-setuid-sandbox"
                    ]
                )
                context: BrowserContext = await browser.new_context(
                    user_agent=USER_AGENT,
                    viewport={"width": 1280, "height": 900},
                    ignore_https_errors=True,
                )

                # TRUCO 2: BLOQUEAR VIDEOS E IMÁGENES (¡Esto salva a AS de colapsar!)
                async def interceptar(route):
                    if route.request.resource_type in ["image", "media", "font"]:
                        await route.abort()
                    else:
                        await route.continue_()
                await context.route("**/*", interceptar)

                page: Page = await context.new_page()
                await page.goto(self.url, timeout=TIMEOUT_MS, wait_until="domcontentloaded")
                await page.wait_for_timeout(3000)

                links = await self._get_article_links(page)
                log["encontradas"] = len(links)

                # TRUCO 3: Cerramos la página inicial antes de seguir
                await page.close()

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

                await browser.close()

        except Exception as exc:
            log["error"] = str(exc)
            log["estado"] = "Error"
            return noticias, log

        log["extraidas"] = len(noticias)
        log["estado"] = "Correcto" if noticias else "Sin noticias del día"
        return noticias, log

    async def _get_article_links(self, page: Page) -> list[str]:
        # Extraemos palabras clave de la URL del Excel para filtrar
        path_original = urlparse(self.url).path.lower()
        # Si la ruta es muy corta (ej: /), buscamos por dominio
        keyword = path_original.strip('/').split('/')[0] if len(path_original) > 1 else ""

        seen: set[str] = set()
        batch: list[str] = []

        # Priorizar enlaces dentro del área de contenido principal para evitar footers
        # Intentamos buscar en contenedores comunes de noticias
        container = page.locator("main, #content, .site-content, #main, .main-content").first
        if await container.count() == 0:
            container = page # Si no hay main, usamos toda la página

        all_links = await container.locator("a[href]").all()
        
        for el in all_links:
            href = await el.get_attribute("href")
            if not href: continue
            href = self._absolute(href)

            if not self._is_same_domain(href): continue
            
            # FILTRO CRÍTICO: Si la URL del Excel tiene una sección (ej: /real-madrid/), 
            # la noticia debe tener esa palabra en su URL.
            if keyword and keyword not in href.lower():
                continue

            # Excluir bad segments
            if any(b in href.lower() for b in ["/autor/", "/tags/", "/seccion/", "/category/", "/page/", "#"]):
                continue

            if href in seen: continue

            # Lógica de slug con guiones
            path = urlparse(href).path
            segments = [p for p in path.split("/") if p]
            if not segments: continue
            
            last_slug = segments[-1].replace(".html", "")
            if last_slug.count("-") < 2: continue

            seen.add(href)
            batch.append(href)
            if len(batch) >= 15: break

        return batch

    async def _extract_article(self, context: BrowserContext, url: str) -> dict | None:
        page: Page = await context.new_page()
        try:
            await page.goto(url, timeout=TIMEOUT_MS, wait_until="domcontentloaded")
            await page.wait_for_timeout(1500)

            try:
                btn = page.locator("#didomi-notice-agree-button, .didomi-continue-without-agreeing, .cmplz-accept, #onetrust-accept-btn-handler")
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
            return None
        finally:
            await page.close()

    def _absolute(self, href: str) -> str:
        if href.startswith("http"): return href
        from urllib.parse import urljoin
        return urljoin(self.url, href)

    def _is_same_domain(self, url: str) -> bool:
        from urllib.parse import urlparse
        base_domain = urlparse(self.url).netloc.replace("www.", "")
        url_domain = urlparse(url).netloc.replace("www.", "")
        return base_domain in url_domain or url_domain in base_domain

    def _is_article_url(self, url: str) -> bool:
        return self._is_same_domain(url)