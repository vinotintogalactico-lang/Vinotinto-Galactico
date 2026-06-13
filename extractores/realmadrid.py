"""Extractor para realmadrid.com"""
from playwright.async_api import Page
from extractores.generic import GenericExtractor

class RealMadridExtractor(GenericExtractor):

    async def _get_article_links(self, page: Page) -> list[str]:
        seen: set[str] = set()
        links: list[str] = []
        
        # Obtenemos TODOS los enlaces de la página
        elements = await page.locator("a[href]").all()
        
        for el in elements:
            href = await el.get_attribute("href")
            if not href:
                continue
                
            href = self._absolute(href)
            href_lower = href.lower()
            
            # REGLA 1: Solo miramos lo que esté en la sección de noticias
            if "/noticias/" not in href_lower:
                continue
                
            # REGLA 2: Extraer el final del enlace (el título de la noticia)
            clean_href = href.split("?")[0].strip("/")
            slug = clean_href.split("/")[-1]
            
            # REGLA 3: Las noticias de verdad son largas y tienen palabras separadas por guiones.
            # Si tiene menos de 2 guiones, es un menú (ej: "futbol" o "el-club"). Lo ignoramos.
            if slug.count("-") < 2:
                continue
                
            # REGLA 4: Bloqueo explícito. Prohibido entrar a estas secciones.
            basura = [
                "/baloncesto", "/el-club", "/castilla", "/entradas", 
                "/tour", "/inicio", "/plantilla", "/clasificacion"
            ]
            if any(b in href_lower for b in basura):
                continue
            
            # Bloqueo adicional para las portadas de los primeros equipos
            if slug in ["primer-equipo-masculino", "primer-equipo-femenino", "primer-equipo"]:
                continue
                
            # Si sobrevive a todo lo anterior, ES UNA NOTICIA REAL.
            if href not in seen and self._is_article_url(href):
                seen.add(href)
                links.append(href)
                
            if len(links) >= 3:
                break
                
        return links

    async def _extract_article(self, context, url: str) -> dict | None:
        page = await context.new_page()
        try:
            from core.article_parser import parse_article
            from bs4 import BeautifulSoup
            
            await page.goto(url, timeout=20_000, wait_until="domcontentloaded")
            await page.wait_for_timeout(1500)
            html = await page.content()
            
            soup = BeautifulSoup(html, "html.parser")
            
            title = soup.find("h1")
            title_text = title.get_text(strip=True) if title else ""
            
            subtitle = soup.select_one(".article-subtitle, .intro, p.lead")
            subtitle_text = subtitle.get_text(strip=True) if subtitle else ""
            
            author = soup.select_one(".author, .article-author")
            author_text = author.get_text(strip=True) if author else "Real Madrid"
            
            date_el = soup.select_one("time, .date, .article-date")
            date_text = date_el.get_text(strip=True) if date_el else ""
            
            art = parse_article(html, url, title=title_text, subtitle=subtitle_text, author=author_text, date=date_text)
            return art if art.get("title") else None
        except Exception as e:
            print("ERROR IN EXTRACT_ARTICLE:", repr(e))
            return None
        finally:
            await page.close()