"""Extractor para defensacentral.com
Los artículos tienen estructura: /actualidad/titular-con-guiones_339426_102.html
Solo 2 segmentos de path, pero slugs largos con guiones.
"""
from urllib.parse import urlparse
from playwright.async_api import Page
from extractores.generic import GenericExtractor


class DefensacentralExtractor(GenericExtractor):

    async def _get_article_links(self, page: Page) -> list[str]:
        # Aceptar cookies
        for sel in [
            "#didomi-notice-agree-button",
            ".cmplz-accept",
            "#onetrust-accept-btn-handler",
        ]:
            try:
                btn = page.locator(sel).first
                if await btn.is_visible(timeout=2000):
                    await btn.click()
                    await page.wait_for_timeout(1500)
                    break
            except Exception:
                pass

        await page.wait_for_timeout(1500)

        seen: set[str] = set()
        batch: list[str] = []

        all_links = await page.locator("a[href]").all()
        for el in all_links:
            href = await el.get_attribute("href")
            if not href:
                continue
            href = self._absolute(href)

            if "defensacentral.com" not in href:
                continue

            # Excluir secciones no-artículo
            path = urlparse(href).path
            segments = [p for p in path.split("/") if p]

            # DefensaCentral: /actualidad/titular.html  (2 segmentos)
            if len(segments) < 2:
                continue

            # El último segmento debe tener un slug con guiones (artículo real)
            last_slug = segments[-1].replace(".html", "").replace(".htm", "")
            if last_slug.count("-") < 2:
                continue

            # Excluir páginas de listado
            if last_slug in ["actualidad", "real_madrid", "portada", "opinion", "ocio"]:
                continue
            if any(b in href for b in [
                "/category/", "/categoria/", "/tag/", "/autor/", "/page/",
                "#", "javascript:", "facebook.com", "twitter.com",
            ]):
                continue

            if href in seen:
                continue
            seen.add(href)
            batch.append(href)
            if len(batch) >= 15:
                break

        return batch
