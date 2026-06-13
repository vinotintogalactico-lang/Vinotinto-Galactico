"""
Extractores para dominios del Mundial 2026
Cada uno hereda de GenericExtractor y puede sobrescribir métodos si es necesario
"""

# ============================================================================
# TELEMUNDO DEPORTES
# ============================================================================
class TelemundoExtractor:
    """telemundodeportes.com"""
    use_requests = True
    
    async def _get_article_links_soup(self, soup) -> list[str]:
        seen = set()
        links = []
        
        for sel in ["a[href*='mundial']", "a[href*='futbol']", "h2 a[href]", "h3 a[href]"]:
            for el in soup.select(sel):
                href = el.get("href")
                if href and "telemundodeportes" in href and href not in seen:
                    seen.add(href)
                    links.append(self._absolute(href))
                if len(links) >= 15:
                    break
            if len(links) >= 3:
                break
        
        return links


# ============================================================================
# TUDN
# ============================================================================
class TudnExtractor:
    """tudn.com"""
    use_requests = True
    
    async def _get_article_links_soup(self, soup) -> list[str]:
        seen = set()
        links = []
        
        for sel in ["a[href*='mundial']", "article a[href]", "h2 a[href]"]:
            for el in soup.select(sel):
                href = el.get("href")
                if href and "tudn.com" in href and href not in seen:
                    seen.add(href)
                    links.append(self._absolute(href))
                if len(links) >= 15:
                    break
            if len(links) >= 3:
                break
        
        return links


# ============================================================================
# TV AZTECA
# ============================================================================
class TvaztecaExtractor:
    """tvazteca.com"""
    use_requests = True
    
    async def _get_article_links_soup(self, soup) -> list[str]:
        seen = set()
        links = []
        
        for sel in ["a[href*='futbol']", ".article a[href]", "h2 a[href]"]:
            for el in soup.select(sel):
                href = el.get("href")
                if href and "tvazteca.com" in href and href not in seen:
                    seen.add(href)
                    links.append(self._absolute(href))
                if len(links) >= 15:
                    break
            if len(links) >= 3:
                break
        
        return links


# ============================================================================
# TYC SPORTS
# ============================================================================
class TycsportsExtractor:
    """tycsports.com"""
    use_requests = True
    
    async def _get_article_links_soup(self, soup) -> list[str]:
        seen = set()
        links = []
        
        for sel in ["a[href*='mundial']", ".nota a[href]", "article a[href]", "h2 a[href]"]:
            for el in soup.select(sel):
                href = el.get("href")
                if href and "tycsports.com" in href and href not in seen:
                    seen.add(href)
                    links.append(self._absolute(href))
                if len(links) >= 15:
                    break
            if len(links) >= 3:
                break
        
        return links


# ============================================================================
# FUTBOL RED
# ============================================================================
class FutbolredExtractor:
    """futbolred.com"""
    use_requests = True
    
    async def _get_article_links_soup(self, soup) -> list[str]:
        seen = set()
        links = []
        
        for sel in ["a[href*='internacional']", ".article a[href]", "h2 a[href]", "article a[href]"]:
            for el in soup.select(sel):
                href = el.get("href")
                if href and "futbolred.com" in href and href not in seen:
                    seen.add(href)
                    links.append(self._absolute(href))
                if len(links) >= 15:
                    break
            if len(links) >= 3:
                break
        
        return links


# ============================================================================
# WINSPORTS
# ============================================================================
class WinsportsExtractor:
    """winsports.co"""
    use_requests = True
    
    async def _get_article_links_soup(self, soup) -> list[str]:
        seen = set()
        links = []
        
        for sel in ["a[href*='internacional']", ".article a[href]", "article a[href]", "h2 a[href]"]:
            for el in soup.select(sel):
                href = el.get("href")
                if href and "winsports.co" in href and href not in seen:
                    seen.add(href)
                    links.append(self._absolute(href))
                if len(links) >= 15:
                    break
            if len(links) >= 3:
                break
        
        return links


# ============================================================================
# RECORD (México)
# ============================================================================
class RecordExtractor:
    """record.com.mx"""
    use_requests = True
    
    async def _get_article_links_soup(self, soup) -> list[str]:
        seen = set()
        links = []
        
        for sel in ["a[href*='futbol']", ".article a[href]", "article a[href]", "h2 a[href]"]:
            for el in soup.select(sel):
                href = el.get("href")
                if href and "record.com.mx" in href and href not in seen:
                    seen.add(href)
                    links.append(self._absolute(href))
                if len(links) >= 15:
                    break
            if len(links) >= 3:
                break
        
        return links


# ============================================================================
# MEDIOTIEMPO (México)
# ============================================================================
class MediatiempoExtractor:
    """mediotiempo.com"""
    use_requests = True
    
    async def _get_article_links_soup(self, soup) -> list[str]:
        seen = set()
        links = []
        
        for sel in ["a[href*='futbol']", ".article a[href]", "article a[href]", "h2 a[href]"]:
            for el in soup.select(sel):
                href = el.get("href")
                if href and "mediotiempo.com" in href and href not in seen:
                    seen.add(href)
                    links.append(self._absolute(href))
                if len(links) >= 15:
                    break
            if len(links) >= 3:
                break
        
        return links


# ============================================================================
# RTVE (España)
# ============================================================================
class RtveExtractor:
    """rtve.es"""
    use_requests = True
    
    async def _get_article_links_soup(self, soup) -> list[str]:
        seen = set()
        links = []
        
        for sel in ["a[href*='deportes']", "article a[href]", "h2 a[href]"]:
            for el in soup.select(sel):
                href = el.get("href")
                if href and "rtve.es" in href and href not in seen:
                    seen.add(href)
                    links.append(self._absolute(href))
                if len(links) >= 15:
                    break
            if len(links) >= 3:
                break
        
        return links


# Los demás (Televen, Caracol, RCN, Telefe, DirectV, elcanaldelfutbol, 
# ChileVision, 13, Latina, Líder) usan GenericExtractor
# que ya está optimizado para sitios genéricos
