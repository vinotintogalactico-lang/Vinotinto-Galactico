import requests
from concurrent.futures import ThreadPoolExecutor

links = [
    'https://www.telemundodeportes.com/copa-mundial-fifa-2026', 'https://www.tudn.com/mundial-2026', 
    'https://www.tvazteca.com/aztecadeportes/futbol', 'https://televen.com/elnoticiero/copa-mundial-de-la-fifa-2026/', 
    'https://noticias.caracoltv.com/golcaracol/mundial-2026', 'https://www.noticiasrcn.com/deportes', 
    'https://www.tycsports.com/mundial', 'https://mitelefe.com/deportes/', 'https://www.directvgo.com/deportes', 
    'https://elcanaldelfutbol.com/', 'https://www.chilevision.cl/deportes', 'https://www.13.cl/deportes', 
    'https://www.latina.pe/deportes', 'https://www.rtve.es/play/deportes/', 
    'https://www.liderendeportes.com/noticias/futbol/mundial-2026/', 'https://meridiano.net/futbol/futbol-internacional/', 
    'https://www.winsports.co/futbol-internacional/', 'https://www.futbolred.com/futbol-internacional', 
    'https://www.record.com.mx/futbol', 'https://www.mediotiempo.com/futbol', 'https://www.foxsports.com.mx/futbol/', 
    'https://www.ole.com.ar/mundial/mundial-2026', 'https://www.elgrafico.com.ar/', 'https://redgol.cl/mundial/', 
    'https://www.alairelibre.cl/noticias/deportes/futbol/mundial/', 'https://depor.com/futbol-internacional/', 
    'https://libero.pe/futbol-internacional/', 'https://www.elpais.com.uy/ovacion/futbol', 
    'https://studiofutbol.com.ec/category/internacional/', 'https://www.diez.hn/futbolinternacional/', 
    'https://www.marca.com/futbol/mundial.html', 'https://as.com/futbol/mundial/', 
    'https://www.mundodeportivo.com/futbol/mundial', 'https://www.sport.es/es/mundial.html', 
    'https://www.relevo.com/futbol/mundial-futbol/', 'https://espndeportes.espn.com/futbol/copa-mundial/', 
    'https://www.infobae.com/deportes/', 'https://www.clarosports.com/futbol/mundial/', 
    'https://www.eltiempo.com/deportes/futbol-internacional', 'https://www.latercera.com/canal/el-deportivo/', 
    'https://www.eluniversal.com.mx/deportes/'
]

def check_url(url):
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        return f"[{res.status_code}] {url}"
    except Exception as e:
        return f"[ERR] {url}: {e}"

with ThreadPoolExecutor(max_workers=10) as executor:
    results = executor.map(check_url, links)
    for r in results:
        print(r)
