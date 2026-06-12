import asyncio
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

def test_as_links():
    url = "https://as.com/noticias/real-madrid/?omnil=mod_esc"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "es-ES,es;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    
    print(f"Testing {url}...")
    resp = requests.get(url, headers=headers, timeout=15.0)
    html = resp.text
    print(f"Status: {resp.status_code}, Length: {len(html)}")
    
    soup = BeautifulSoup(html, "html.parser")
    selectors = [
        ".a-article-snapshot a[href]",
        ".a-article-list__item a[href]",
        ".h-list__item a[href]",
        "article.a-article a[href]",
        ".content-list a[href]",
        "main h2 a[href]",
        "main h3 a[href]",
        "main a[href]",
    ]
    
    bad_segments = ["/resultados/", "/ficha/", "-directo", "/clasificacion/", "/plantilla/", "/calendario/"]
    
    for sel in selectors:
        batch = []
        seen = set()
        for a in soup.select(sel):
            href = a.get("href")
            if not href: continue
            if not href.startswith("http"):
                href = urljoin(url, href)
            if "as.com" not in href: continue
            if any(b in href for b in bad_segments): continue
            
            # simulate _is_article_url
            bad2 = ["#", "javascript:", "mailto:", ".pdf", ".jpg", ".png", ".gif", ".mp4", "/autor/", "/author/", "/firmas/", "/tags/", "/etiquetas/", "/page/", "/category/", "/categoria/"]
            if any(b in href.lower() for b in bad2): continue
            
            if href not in seen:
                seen.add(href)
                batch.append(href)
                
        if len(batch) >= 3:
            print(f"Selector {sel} found {len(batch)} links:")
            for b in batch[:3]:
                print(b)
            return

test_as_links()
