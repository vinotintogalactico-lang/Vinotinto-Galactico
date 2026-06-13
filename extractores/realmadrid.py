"""Extractor para realmadrid.com"""
from extractores.generic import GenericExtractor

class RealMadridExtractor(GenericExtractor):

    async def _get_article_links_soup(self, soup) -> list[str]:
        seen: set[str] = set()
        links: list[str] = []
        
        elements = soup.select("a[href]")
        
        for el in elements:
            href = el.get("href")
            if not href:
                continue
                
            href = self._absolute(href)
            href_lower = href.lower()
            
            if "/noticias/" not in href_lower:
                continue
                
            clean_href = href.split("?")[0].strip("/")
            slug = clean_href.split("/")[-1]
            
            if slug.count("-") < 2:
                continue
                
            basura = [
                "/baloncesto", "/el-club", "/castilla", "/entradas", 
                "/tour", "/inicio", "/plantilla", "/clasificacion"
            ]
            if any(b in href_lower for b in basura):
                continue
            
            if slug in ["primer-equipo-masculino", "primer-equipo-femenino", "primer-equipo"]:
                continue
                
            if href not in seen and self._is_article_url(href):
                seen.add(href)
                links.append(href)
                
            if len(links) >= 3:
                break
                
        return links

    async def _extract_article_requests(self, url: str) -> dict | None:
        try:
            from core.article_parser import parse_article
            import requests
            import asyncio
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept-Language": "es-ES,es;q=0.9",
            }
            resp = await asyncio.to_thread(requests.get, url, headers=headers, timeout=15.0)
            if resp.status_code != 200:
                return None
                
            html = resp.text
            from bs4 import BeautifulSoup
            soup_article = BeautifulSoup(html, "html.parser")
            
            title = soup_article.find("h1")
            title_text = title.get_text(strip=True) if title else ""
            
            subtitle = soup_article.select_one(".article-subtitle, .intro, p.lead")
            subtitle_text = subtitle.get_text(strip=True) if subtitle else ""
            
            author = soup_article.select_one(".author, .article-author")
            author_text = author.get_text(strip=True) if author else "Real Madrid"
            
            date_el = soup_article.select_one("time, .date, .article-date")
            date_text = date_el.get_text(strip=True) if date_el else ""
            
            art = parse_article(html, url, title=title_text, subtitle=subtitle_text, author=author_text, date=date_text)
            return art if art.get("title") else None
        except Exception as e:
            print("ERROR IN EXTRACT_ARTICLE:", repr(e))
            return None