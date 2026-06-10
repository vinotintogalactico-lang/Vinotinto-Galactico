"""
Diagnóstico rápido para ver qué links encuentra cada extractor
y por qué falla el filtro de fecha/contenido.
"""
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse

def check_links(name, url, section_prefix=""):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36")
        try:
            page.goto(url, timeout=25000, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)
            # Accept cookies
            for sel in ["#didomi-notice-agree-button", ".cmplz-accept", "#onetrust-accept-btn-handler", ".btn-gdpr-accept"]:
                try:
                    btn = page.locator(sel).first
                    if btn.is_visible(timeout=1500):
                        btn.click()
                        page.wait_for_timeout(1500)
                        break
                except: pass
            
            all_links = page.eval_on_selector_all("a[href]", "els => els.map(e => ({href: e.href, text: e.innerText.trim().slice(0,60)}))")
            print(f"\n{'='*60}")
            print(f"SITE: {name}")
            print(f"URL:  {url}")
            print(f"TOTAL links on page: {len(all_links)}")
            
            domain = urlparse(url).netloc.replace("www.","")
            count = 0
            for l in all_links:
                href = l["href"]
                txt = l["text"]
                if not href.startswith("http") or len(txt) < 8: continue
                if domain not in href: continue
                if "javascript" in href or "#" in href: continue
                link_path = urlparse(href).path
                prefix_match = "OK" if not section_prefix or link_path.startswith(section_prefix) else f"NO(need:{section_prefix})"
                print(f"  [{prefix_match}] {txt[:50]} -> {link_path}")
                count += 1
                if count >= 8: break
        except Exception as e:
            print(f"ERROR: {e}")
        finally:
            browser.close()

# Test the failing ones
check_links("As - Real Madrid", "https://as.com/noticias/real-madrid/?omnil=mod_esc", "/noticias/real-madrid")
check_links("Marca - Real Madrid", "https://www.marca.com/futbol/real-madrid.html?intcmp=MENUESCU&s_kw=realmadrid")
check_links("Madridistareal", "https://madridistareal.com/real-madrid/")
check_links("Sport - Real Madrid", "https://www.sport.es/es/real-madrid/")
