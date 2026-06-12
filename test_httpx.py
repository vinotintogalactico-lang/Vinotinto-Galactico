import asyncio
import requests
from bs4 import BeautifulSoup

async def test_requests():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "es-ES,es;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    
    urls = [
        "https://as.com/futbol/primera/viene-otro-mourinho-f202606-n/",
        "https://meridiano.net/futbol/espanol/real-madrid-anuncia-su-primer-fichaje-para-la-temporada-2024-2025-202661214150"
    ]
    
    for url in urls:
        try:
            print(f"Testing {url}...")
            resp = await asyncio.to_thread(requests.get, url, headers=headers, timeout=15.0)
            html = resp.text
            print(f"Status: {resp.status_code}, Length: {len(html)}")
            soup = BeautifulSoup(html, "html.parser")
            title = soup.find("h1")
            print("Title:", title.text if title else "NO TITLE")
        except Exception as e:
            print("Error:", e)

asyncio.run(test_requests())
