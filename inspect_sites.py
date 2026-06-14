from playwright.sync_api import sync_playwright
import re

def accept_cookies(page):
    selectors = [
        '#didomi-notice-agree-button',
        '.cmplz-accept',
        '.btn-gdpr-accept',
        '#onetrust-accept-btn-handler',
        '.gdpr-accept',
    ]
    for sel in selectors:
        try:
            btn = page.locator(sel).first
            if btn.is_visible(timeout=1500):
                btn.click()
                page.wait_for_timeout(1500)
                return True
        except:
            pass
    # Try text-based buttons
    for text in ["Aceptar todo", "Aceptar y continuar", "Aceptar", "Acepto", "ACEPTO", "Accept"]:
        try:
            btn = page.get_by_role("button", name=text, exact=True).first
            if btn.is_visible(timeout=500):
                btn.click()
                page.wait_for_timeout(1500)
                return True
        except:
            pass
    return False

def inspect_site(browser, name, url, url_must_contain=None):
    page = browser.new_page()
    try:
        page.goto(url, timeout=25000, wait_until='domcontentloaded')
        page.wait_for_timeout(2500)
        accept_cookies(page)
        page.wait_for_timeout(1500)

        all_links = page.eval_on_selector_all('a[href]', """els => els.map(e => ({
            href: e.href,
            text: e.innerText.trim().slice(0,70),
            cls: e.className.slice(0,100),
            parent: e.parentElement ? e.parentElement.tagName + '.' + e.parentElement.className.slice(0,60) : ''
        }))""")

        print(f'=== {name} ===')
        count = 0
        for l in all_links:
            href = l['href']
            if not href.startswith('http') or len(l['text']) < 10 or 'javascript' in href:
                continue
            if url_must_contain and url_must_contain not in href:
                continue
            print(f"  HREF: {href}")
            print(f"  TEXT: {l['text']}")
            print(f"  CLS:  {l['cls']}")
            print(f"  PAR:  {l['parent']}")
            print()
            count += 1
            if count >= 5:
                break
    except Exception as e:
        print(f'{name} ERROR: {e}')
    finally:
        page.close()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    inspect_site(browser, 'Defensacentral', 'https://defensacentral.com/real_madrid', '/actualidad/')
    inspect_site(browser, 'Sport', 'https://www.sport.es/es/real-madrid/', 'sport.es/es/')
    inspect_site(browser, 'Madridistareal', 'https://madridistareal.com/real-madrid/', 'madridistareal.com')
    inspect_site(browser, 'Estadiodeportivo', 'https://www.estadiodeportivo.com/futbol/real-madrid/', 'estadiodeportivo.com')
    browser.close()
