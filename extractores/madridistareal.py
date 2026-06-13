"""Extractor para madridistareal.com (WordPress)
Los artículos están en la raíz del dominio con slugs descriptivos.
Ejemplo: /real-madrid-ofrece-150-millones-julian-alvarez/
"""
from playwright.async_api import Page
from extractores.generic import GenericExtractor


class MadridistarealExtractor(GenericExtractor):

    async def _get_article_links(self, page: Page) -> list[str]:
        seen: set[str] = set()
        links: list[str] = []

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
                    await page.wait_for_timeout(2000)
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
                        await page.wait_for_timeout(2000)
                        cookie_accepted = True
                        break
                except Exception:
                    pass

        # Esperar a que la página cargue el contenido real
        await page.wait_for_timeout(2000)

        # Páginas de menú a excluir (path exacto)
        nav_paths = {
            "/real-madrid/", "/real-madrid-baloncesto/", "/real-madrid-femenino/",
            "/la-fabrica/real-madrid-castilla/", "/entrevista/", "/suscripcion/",
            "/", "/formulario-de-suscripcion-para-penas/",
        }

        # WordPress: artículos tipicamente en títulos h2/h3
        selectors = [
            ".entry-title a[href]",
            "h2.entry-title a[href]",
            "h3.entry-title a[href]",
            ".td-module-title a[href]",
            "article a[href]",
            "a[href]",  # Fallback a todos los links si no hay contenedor claro
        ]

        for sel in selectors:
            seen: set[str] = set()
            batch: list[str] = []
            elements = await page.query_selector_all(sel)
            for el in elements:
                href = await el.get_attribute("href")
                if not href:
                    continue
                href = self._absolute(href)
                if "madridistareal.com" not in href:
                    continue

                from urllib.parse import urlparse
                link_path = urlparse(href).path

                # Excluir páginas de menú y categorías
                if link_path in nav_paths:
                    continue
                if any(s in link_path for s in ["/tag/", "/category/", "/categoria/",
                                                "/autor/", "/author/", "/page/"]):
                    continue
                if len(link_path) < 15:
                    continue  # Demasiado corto para ser noticia

                if href not in seen and self._is_article_url(href):
                    seen.add(href)
                    batch.append(href)
                if len(batch) >= 15:
                    break

            if len(batch) >= 3:
                return batch

        return []
