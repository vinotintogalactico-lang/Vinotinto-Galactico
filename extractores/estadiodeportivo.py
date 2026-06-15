"""Extractor para estadiodeportivo.com
Los artículos suelen tener estructura: /futbol/real-madrid/titular-con-guiones.html
o a veces rutas más cortas. Usa lógica adaptada.
"""
from urllib.parse import urlparse
from playwright.async_api import Page
from extractores.generic import GenericExtractor


class EstadioDeportivoExtractor(GenericExtractor):

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

        # Keyword de sección desde la URL
        path_parts = [p for p in urlparse(self.url).path.split("/") if p]
        section_kws = [p for p in path_parts if p not in ("futbol", "deportes")]

        seen: set[str] = set()
        batch: list[str] = []

        all_links = await page.locator("a[href]").all()
        for el in all_links:
            href = await el.get_attribute("href")
            if not href:
                continue
            href = self._absolute(href)

            if "estadiodeportivo.com" not in href:
                continue

            path = urlparse(href).path
            segments = [p for p in path.split("/") if p]

            # Mínimo 2 segmentos: /seccion/articulo.html
            if len(segments) < 2:
                continue

            last_slug = segments[-1].replace(".html", "").replace(".htm", "")
            if last_slug.count("-") < 2:
                continue

            # Excluir páginas de listado
            if last_slug in ["portada", "real-madrid", "futbol", "opinion", "multimedia"]:
                continue
            if any(b in href for b in [
                "/category/", "/categoria/", "/tag/", "/autor/",
                "#", "javascript:", "facebook.com", "twitter.com",
            ]):
                continue

            # Si hay keyword de sección, debe aparecer en el path
            if section_kws:
                if not any(kw in path for kw in section_kws):
                    continue

            if href in seen:
                continue
            seen.add(href)
            batch.append(href)
            if len(batch) >= 15:
                break

        return batch
