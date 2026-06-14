"""Extractor para meridiano.com.ve y otras fuentes venezolanas"""
from playwright.async_api import Page
from mundial.extractores.generic_mundial import GenericExtractor


class MeridianoExtractor(GenericExtractor):

    async def _get_article_links(self, page: Page) -> list[str]:
        selectors = [
            ".article-list__item a[href]",
            ".post-title a[href]",
            "h2 a[href]",
            "h3 a[href]",
            "article a[href]",
            ".entry-title a[href]",
        ]
        seen: set[str] = set()
        links: list[str] = []
        for sel in selectors:
            elements = await page.query_selector_all(sel)
            for el in elements:
                href = await el.get_attribute("href")
                if href:
                    href = self._absolute(href)
                    if href not in seen and self._is_article_url(href):
                        seen.add(href)
                        links.append(href)
            if len(links) >= 9:
                break
        return links
    async def _extract_article(self, context, url: str) -> dict | None:
        page = await context.new_page()
        try:
            from mundial.core.article_parser import parse_article
            from bs4 import BeautifulSoup
            
            await page.goto(url, timeout=20_000, wait_until="domcontentloaded")
            await page.wait_for_timeout(1500)
            html = await page.content()
            
            soup = BeautifulSoup(html, "html.parser")
            
            title = soup.find("h1")
            title_text = title.get_text(strip=True) if title else ""
            
            subtitle = soup.select_one("h2.subtitle, h2.bajada, h2.resumen")
            subtitle_text = subtitle.get_text(strip=True) if subtitle else ""
            
            author = soup.select_one(".author, .autor, .post-author")
            author_text = author.get_text(strip=True) if author else ""
            
            date_el = soup.select_one("time, .date, .fecha")
            date_text = date_el.get_text(strip=True) if date_el else ""
            
            art = parse_article(html, url, title=title_text, subtitle=subtitle_text, author=author_text, date=date_text)
            return art if art.get("title") else None
        except Exception:
            return None
        finally:
            await page.close()
