"""
Extractor genérico.
Funciona para la mayoría de fuentes; los extractores específicos
sobrescriben métodos cuando la estructura del sitio lo requiere.

Estrategia de enlaces: escanea TODOS los <a> de la página y filtra
por patrón de artículo en lugar de depender de selectores CSS frágiles.
"""

"""
Extractor genérico optimizado para Streamlit Cloud (Ahorro extremo de RAM).
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
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

class GenericExtractor:
    def __init__(self, fuente: str, url: str, categoria: str):
        self.fuente = fuente
        self.url = url
        self.categoria = categoria

    async def extract(self) -> tuple[list[dict], dict]:
        # Limpieza manual de memoria antes de cada diario
        gc.collect()
        
        noticias: list[dict] = []
        log = {"fuente": self.fuente, "encontradas": 0, "extraidas": 0, "estado": "Iniciando", "error": ""}

        try:
            async with async_playwright() as pw:
                # 1. Lanzamiento ultra-ligero
                browser = await pw.chromium.launch(
                    headless=True,
                    args=["--disable-dev-shm-usage", "--no-sandbox", "--disable-gpu", "--no-zygote"]
                )
                
                # 2. DESACTIVAR JAVASCRIPT: Es la única forma de que Mundo Deportivo no crashee
                # Los links y el texto están en el HTML estático, no necesitamos JS.
                context = await browser.new_context(
                    user_agent=USER_AGENT,
                    viewport={"width": 800, "height": 600},
                    java_script_enabled=False, 
                    ignore_https_errors=True
                )

                # 3. Bloquear imágenes y estilos para ahorrar RAM al máximo
                async def intercept(route):
                    if route.request.resource_type in ["image", "media", "font", "stylesheet"]:
                        await route.abort()
                    else:
                        await route.continue_()
                await context.route("**/*", intercept)

                # 4. Obtener enlaces (Página principal del diario)
                page = await context.new_page()
                try:
                    await page.goto(self.url, timeout=TIMEOUT_MS, wait_until="commit")
                    links = await self._get_article_links(page)
                    log["encontradas"] = len(links)
                finally:
                    await page.close() # Cierre inmediato para liberar memoria

                # 5. Procesar cada noticia
                for link in links:
                    if len(noticias) >= MAX_NEWS: break
                    try:
                        articulo = await self._extract_article(context, link)
                        if articulo:
                            if not is_valid_content(articulo.get("title", ""), self.categoria, articulo.get("body", "")):
                                continue
                            
                            # Tu función is_today devuelve (bool, string)
                            ok_date, _ = is_today(articulo.get("date", ""))
                            if ok_date:
                                articulo["fuente"] = self.fuente
                                articulo["categoria"] = self.categoria
                                noticias.append(articulo)
                    except Exception:
                        continue

                await browser.close()

        except Exception as exc:
            log["error"] = str(exc)
            log["estado"] = "Error"
            return noticias, log

        log["extraidas"] = len(noticias)
        log["estado"] = "Correcto" if noticias else "Sin noticias del día"
        return noticias, log

    async def _get_article_links(self, page: Page) -> list[str]:
        """Extrae links del HTML estático (sin necesidad de JS)"""
        bad_segments = ("#", "javascript:", "mailto:", ".pdf", "/autor/", "/tags/", "/resultados/")
        seen, batch = set(), []
        
        all_links = await page.locator("a[href]").all()
        for el in all_links:
            href = await el.get_attribute("href")
            if not href: continue
            href = self._absolute(href)
            if not self._is_same_domain(href): continue
            if any(b in href.lower() for b in bad_segments): continue
            if href in seen: continue

            from urllib.parse import urlparse
            path = urlparse(href).path
            if len(path.split("/")) < 2: continue

            seen.add(href)
            batch.append(href)
            if len(batch) >= 15: break
        return batch

    async def _extract_article(self, context: BrowserContext, url: str) -> dict | None:
        """Abre la noticia individual y extrae el texto"""
        page = await context.new_page()
        try:
            await page.goto(url, timeout=TIMEOUT_MS, wait_until="commit")
            html = await page.content()
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            
            # Intento de capturar fecha de meta-tags (funciona sin JS)
            date_text = ""
            time_el = soup.select_one("time[datetime]")
            if time_el and time_el.get("datetime"):
                date_text = time_el["datetime"]

            return parse_article(html, url, date=date_text)
        except Exception:
            return None
        finally:
            if not page.is_closed(): await page.close()

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