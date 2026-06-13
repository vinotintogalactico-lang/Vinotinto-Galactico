"""Extractor para laliga.com"""
from playwright.async_api import Page
from extractores.generic import GenericExtractor


class LaLigaExtractor(GenericExtractor):

    async def _get_article_links(self, page: Page) -> list[str]:
        seen: set[str] = set()
        links: list[str] = []

        # Aceptar cookies de laliga.com
        for sel in [
            "#didomi-notice-agree-button",
            ".didomi-continue-without-agreeing",
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

        for text in ["Aceptar todo", "Aceptar", "Accept all"]:
            try:
                btn = page.get_by_role("button", name=text)
                if await btn.first.is_visible(timeout=500):
                    await btn.first.click()
                    await page.wait_for_timeout(1500)
                    break
            except Exception:
                pass

        await page.wait_for_timeout(2000)

        selectors = [
            ".news-card a[href]",
            ".article-card a[href]",
            ".content-card a[href]",
            "article a[href]",
            ".news-list a[href]",
            "h2 a[href]",
            "h3 a[href]",
            "main a[href]",
        ]

        for sel in selectors:
            elements = await page.query_selector_all(sel)
            for el in elements:
                href = await el.get_attribute("href")
                if not href:
                    continue
                href = self._absolute(href)
                if "laliga.com" not in href:
                    continue
                if href not in seen and self._is_article_url(href):
                    seen.add(href)
                    links.append(href)
            if len(links) >= 15:
                break

        return links
