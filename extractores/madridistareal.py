"""Extractor para madridistareal.com (WordPress)
Los artículos están en la raíz del dominio con slugs descriptivos.
Ejemplo: /real-madrid-ofrece-150-millones-julian-alvarez/
"""
import asyncio
import requests as req_lib
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from playwright.async_api import Page, BrowserContext
from extractores.generic import GenericExtractor
from core.article_parser import parse_article

# Páginas de menú a excluir (path exacto)
NAV_PATHS = {
    "/real-madrid/", "/real-madrid-baloncesto/", "/real-madrid-femenino/",
    "/la-fabrica/real-madrid-castilla/", "/entrevista/", "/suscripcion/",
    "/", "/formulario-de-suscripcion-para-penas/",
}

SELECTORS = [
    ".entry-title a[href]",
    "h2.entry-title a[href]",
    "h3.entry-title a[href]",
    ".td-module-title a[href]",
    "article a[href]",
    "a[href]",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class MadridistarealExtractor(GenericExtractor):
    # Playwright solo para la portada (evita bloqueos)
    use_requests = False

    async def _get_article_links(self, page: Page) -> list[str]:
        seen: set[str] = set()

        # Aceptar cookies del sistema Complianz (cmplz)
        cookie_accepted = False
        for sel in [
            ".cmplz-btn.cmplz-accept",
            "button.cmplz-accept",
            ".cmplz-accept-all",
            "#cmplz-accept",
            "a.cmplz-accept",
        ]:
            try:
                btn = page.locator(sel).first
                if await btn.is_visible(timeout=2500):
                    await btn.click()
                    await page.wait_for_timeout(1500)
                    cookie_accepted = True
                    break
            except Exception:
                pass

        if not cookie_accepted:
            for text in ["Aceptar todo", "Accept all", "Aceptar", "Acepto"]:
                try:
                    btn = page.get_by_role("button", name=text, exact=False)
                    if await btn.first.is_visible(timeout=800):
                        await btn.first.click()
                        await page.wait_for_timeout(1500)
                        cookie_accepted = True
                        break
                except Exception:
                    pass

        await page.wait_for_timeout(1500)

        for sel in SELECTORS:
            seen_batch: set[str] = set()
            batch: list[str] = []
            elements = await page.query_selector_all(sel)
            for el in elements:
                href = await el.get_attribute("href")
                if not href:
                    continue
                href = self._absolute(href)
                if "madridistareal.com" not in href:
                    continue

                link_path = urlparse(href).path

                if link_path in NAV_PATHS:
                    continue
                if any(s in link_path for s in ["/tag/", "/category/", "/categoria/",
                                                "/autor/", "/author/", "/page/"]):
                    continue
                if len(link_path) < 15:
                    continue

                if href not in seen_batch and self._is_article_url(href):
                    seen_batch.add(href)
                    batch.append(href)
                if len(batch) >= 15:
                    break

            if len(batch) >= 3:
                return batch

        return []

    async def _extract_article(self, context: BrowserContext, url: str) -> dict | None:
        """Lee artículos con requests — mucho más ligero."""
        try:
            resp = await asyncio.to_thread(
                req_lib.get, url, headers=HEADERS, timeout=15.0
            )
            if resp.status_code != 200:
                return None

            html = resp.text
            soup = BeautifulSoup(html, "html.parser")

            title = soup.find("h1")
            title_text = title.get_text(strip=True) if title else ""

            subtitle = soup.select_one(".entry-subtitle, .td-post-sub-title, h2.sub-title")
            subtitle_text = subtitle.get_text(strip=True) if subtitle else ""

            author = soup.select_one(".td-post-author-name a, .author.vcard a, [rel='author']")
            author_text = author.get_text(strip=True) if author else ""

            # WordPress suele tener <time class="entry-date" datetime="...">
            date_text = ""
            time_el = soup.select_one("time[datetime]")
            if time_el and time_el.get("datetime"):
                date_text = time_el["datetime"]
            else:
                # Buscar el schema JSON-LD como fallback
                import json, re
                for script in soup.find_all("script", type="application/ld+json"):
                    try:
                        data = json.loads(script.string or "")
                        if isinstance(data, list):
                            data = data[0]
                        dt = data.get("datePublished") or data.get("dateModified", "")
                        if dt:
                            date_text = dt
                            break
                    except Exception:
                        pass

                if not date_text:
                    fallback = soup.select_one(".entry-date, .post-date, .td-post-date")
                    date_text = fallback.get_text(strip=True) if fallback else ""

            art = parse_article(html, url, title=title_text, subtitle=subtitle_text,
                                author=author_text, date=date_text)
            return art if art.get("title") else None
        except Exception:
            return None
