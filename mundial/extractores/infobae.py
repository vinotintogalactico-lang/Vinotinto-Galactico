"""Extractor para infobae.com"""
from playwright.async_api import Page
from mundial.extractores.generic_mundial import GenericExtractor


class InfobaeExtractor(GenericExtractor):

    async def _get_article_links(self, page: Page) -> list[str]:
        bad = ["/video/", "/foto/", "/galeria/", "/tag/", "/autor/"]
        selectors = [
            ".article-card a[href]",
            ".feed-list-card a[href]",
            "h2 a[href]",
            "h3 a[href]",
            "main a[href]",
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
                if "infobae.com" not in href:
                    continue
                if any(b in href for b in bad):
                    continue
                if href not in seen and self._is_article_url(href):
                    seen.add(href)
                    batch.append(href)
                if len(batch) >= 15:
                    break
            if len(batch) >= 3:
                return batch
        return []

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

            subtitle = soup.select_one(".summary-lead, .article-subheading, h2.summary")
            subtitle_text = subtitle.get_text(strip=True) if subtitle else ""

            author = soup.select_one(".byline-author, .article-author__name, .author-name")
            author_text = author.get_text(strip=True) if author else ""

            date_text = ""
            time_el = soup.select_one("time[datetime]")
            if time_el and time_el.get("datetime"):
                date_text = time_el["datetime"]
            else:
                d = soup.select_one("time, .publish-date, .fecha")
                date_text = d.get_text(strip=True) if d else ""

            art = parse_article(html, url, title=title_text, subtitle=subtitle_text,
                                author=author_text, date=date_text)
            return art if art.get("title") else None
        except Exception:
            return None
        finally:
            await page.close()
