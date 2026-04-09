import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
import os
import time
from dataclasses import dataclass, field
from typing import Optional
from abc import ABC, abstractmethod
import re
from urllib.parse import urlparse, urljoin

# ==========================================
# MODELOS DE DATOS
# ==========================================

@dataclass
class Block:
    name: str
    urls: list[str]

@dataclass
class NewsItem:
    titulo: str
    subtitulos: list[str]
    fecha: str
    contenido: str
    autor: str
    fuente: str
    link: str

# ==========================================
# JERARQUÍA DE EXCEPCIONES
# ==========================================

class VGScraperError(Exception): pass
class ExcelReadError(VGScraperError): pass
class AdapterError(VGScraperError): pass
class ExtractionError(VGScraperError): pass
class DateParseError(VGScraperError): pass

# ==========================================
# EXCEL READER
# ==========================================

class ExcelReader:
    def __init__(self, filepath: str):
        self.filepath = filepath

    def read(self) -> list[Block]:
        """
        Returns list of Block in Excel order.
        Ignores empty rows or 'nan' values.
        Raises ExcelReadError if file not found.
        """
        if not os.path.exists(self.filepath):
            raise ExcelReadError(f"No se encontró el archivo: {self.filepath}")

        df = pd.read_excel(self.filepath, header=None)

        blocks: list[Block] = []
        current_block: Optional[Block] = None

        for _, row in df.iterrows():
            cell = str(row[0]).strip()

            if not cell or cell == 'nan':
                continue

            if cell.endswith(':'):
                current_block = Block(name=cell[:-1], urls=[])
                blocks.append(current_block)
            elif cell.startswith('http') and current_block is not None:
                current_block.urls.append(cell)

        return blocks


# ==========================================
# ADAPTADORES
# ==========================================

class BaseAdapter(ABC):
    @abstractmethod
    def fetch_page(self, url: str) -> str:
        """Retorna el HTML de la página. Lanza AdapterError si falla."""


class StaticAdapter(BaseAdapter):
    HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    TIMEOUT = 10

    def fetch_page(self, url: str) -> str:
        try:
            response = requests.get(url, headers=self.HEADERS, timeout=self.TIMEOUT)
            response.raise_for_status()
            return response.text
        except requests.exceptions.Timeout:
            raise AdapterError(f"Timeout al acceder a: {url}")
        except requests.exceptions.HTTPError as e:
            raise AdapterError(f"Error HTTP {e.response.status_code} en: {url}")
        except requests.exceptions.RequestException as e:
            raise AdapterError(f"Error de red en: {url}: {e}")


class PlaywrightAdapter(BaseAdapter):
    def fetch_page(self, url: str) -> str:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise AdapterError(
                "Playwright no está instalado. Instálalo con: pip install playwright && playwright install chromium"
            )
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until="networkidle", timeout=30000)
                html = page.content()
                browser.close()
                return html
        except Exception as e:
            raise AdapterError(f"Error de Playwright en {url}: {e}")


JS_DOMAINS = {"realmadrid.com", "laliga.com"}


class AdapterFactory:
    def get_adapter(self, url: str) -> BaseAdapter:
        domain = urlparse(url).netloc.replace("www.", "")
        if domain in JS_DOMAINS:
            return PlaywrightAdapter()
        return StaticAdapter()


# ==========================================
# PORTADA PARSER
# ==========================================

class PortadaParser:
    ARTICLE_PATTERNS = [
        r'/articulo/', r'/noticias/', r'\.html$',
        r'/\d{4}/', r'/noticia-', r'/news/', r'/futbol/'
    ]
    EXCLUDE_PATTERNS = [
        r'#', r'javascript:', r'mailto:', r'/tag/', r'/autor/',
        r'twitter\.com', r'facebook\.com', r'instagram\.com'
    ]

    def extract_article_links(self, html: str, base_url: str) -> list[str]:
        """
        Returns up to 3 article URLs found in the page.
        Resolves relative URLs using base_url.
        """
        soup = BeautifulSoup(html, 'html.parser')
        found = []
        seen = set()

        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href'].strip()
            if not href:
                continue

            # Resolve relative URLs
            full_url = urljoin(base_url, href)

            # Skip if already seen
            if full_url in seen:
                continue

            # Check exclude patterns
            if any(re.search(pat, full_url) for pat in self.EXCLUDE_PATTERNS):
                continue

            # Check article patterns
            if any(re.search(pat, full_url) for pat in self.ARTICLE_PATTERNS):
                found.append(full_url)
                seen.add(full_url)
                if len(found) >= 3:
                    break

        return found


# ==========================================
# ARTICLE EXTRACTOR
# ==========================================

class ArticleExtractor:
    def extract(self, html: str, url: str, source_name: str) -> 'NewsItem | None':
        """
        Extracts all fields. Returns None if content < 200 chars.
        """
        soup = BeautifulSoup(html, 'html.parser')

        # Title: h1 → og:title → title tag
        titulo = ""
        h1 = soup.find('h1')
        if h1:
            titulo = h1.get_text(strip=True)
        if not titulo:
            og_title = soup.find('meta', property='og:title')
            if og_title:
                titulo = og_title.get('content', '').strip()
        if not titulo:
            title_tag = soup.find('title')
            if title_tag:
                titulo = title_tag.get_text(strip=True)

        # Subtitles: h2 inside article → h3 → empty list
        subtitulos = []
        article_tag = soup.find('article')
        container = article_tag if article_tag else soup
        h2_tags = container.find_all('h2')
        if h2_tags:
            subtitulos = [h.get_text(strip=True) for h in h2_tags if h.get_text(strip=True)]
        if not subtitulos:
            h3_tags = container.find_all('h3')
            subtitulos = [h.get_text(strip=True) for h in h3_tags if h.get_text(strip=True)]

        # Date: <time datetime=""> → article:published_time → regex in text
        fecha = ""
        time_tag = soup.find('time', attrs={'datetime': True})
        if time_tag:
            fecha = time_tag.get('datetime', '').strip() or time_tag.get_text(strip=True)
        if not fecha:
            pub_time = soup.find('meta', property='article:published_time')
            if pub_time:
                fecha = pub_time.get('content', '').strip()
        if not fecha:
            text = soup.get_text()
            date_patterns = [
                r'\d{2}/\d{2}/\d{4}',
                r'\d{4}-\d{2}-\d{2}',
                r'\d{1,2}\s+de\s+\w+\s+de\s+\d{4}',
            ]
            for pat in date_patterns:
                m = re.search(pat, text)
                if m:
                    fecha = m.group(0)
                    break

        # Author: [rel="author"] → .author/.byline → article:author meta → "No disponible"
        autor = ""
        author_tag = soup.find(attrs={'rel': 'author'})
        if author_tag:
            autor = author_tag.get_text(strip=True)
        if not autor:
            for cls in ['author', 'byline']:
                tag = soup.find(class_=cls)
                if tag:
                    autor = tag.get_text(strip=True)
                    break
        if not autor:
            author_meta = soup.find('meta', property='article:author')
            if author_meta:
                autor = author_meta.get('content', '').strip()
        if not autor:
            autor = "No disponible"

        # Content: <article> → .article-body → all <p> > 70 chars; no truncation
        contenido = ""
        if article_tag:
            paragraphs = article_tag.find_all('p')
            contenido = "\n\n".join(
                p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 70
            )
        if not contenido:
            article_body = soup.find(class_='article-body')
            if article_body:
                paragraphs = article_body.find_all('p')
                contenido = "\n\n".join(
                    p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 70
                )
        if not contenido:
            paragraphs = soup.find_all('p')
            contenido = "\n\n".join(
                p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 70
            )

        # Discard if content < 200 chars
        if len(contenido) < 200:
            return None

        return NewsItem(
            titulo=titulo,
            subtitulos=subtitulos,
            fecha=fecha,
            contenido=contenido,
            autor=autor,
            fuente=source_name,
            link=url,
        )


# ==========================================
# DATE FILTER
# ==========================================

SPANISH_MONTHS = {
    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
    'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
    'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
}


class DateFilter:
    RELATIVE_KEYWORDS = {'hace', 'today', 'hoy'}

    DATE_FORMATS = [
        '%d/%m/%Y',
        '%Y-%m-%d',
        '%d-%m-%Y',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%dT%H:%M:%S%z',
    ]

    def is_today(self, date_str: str, reference_date: date) -> bool:
        """
        Tries to parse date_str with multiple formats.
        Accepts relative dates like "hace 2 horas".
        Returns False if the date cannot be determined.
        """
        if not date_str:
            return False

        normalized = date_str.strip().lower()

        # Relative keywords → today
        if any(kw in normalized for kw in self.RELATIVE_KEYWORDS):
            return True

        # Try standard formats
        for fmt in self.DATE_FORMATS:
            try:
                parsed = datetime.strptime(date_str.strip(), fmt)
                return parsed.date() == reference_date
            except ValueError:
                continue

        # Try Spanish text: "15 de enero de 2025"
        spanish_match = re.search(
            r'(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})',
            normalized
        )
        if spanish_match:
            try:
                day = int(spanish_match.group(1))
                month_name = spanish_match.group(2)
                year = int(spanish_match.group(3))
                month = SPANISH_MONTHS.get(month_name)
                if month:
                    parsed_date = date(year, month, day)
                    return parsed_date == reference_date
            except (ValueError, KeyError):
                pass

        # Cannot determine date
        return False


# ==========================================
# ORCHESTRATOR
# ==========================================

class Orchestrator:
    MAX_NOTICIAS_POR_BLOQUE = 5
    DELAY_BETWEEN_REQUESTS = 1  # seconds

    def __init__(self, adapter_factory: AdapterFactory, portada_parser: PortadaParser,
                 article_extractor: ArticleExtractor, date_filter: DateFilter):
        self.adapter_factory = adapter_factory
        self.portada_parser = portada_parser
        self.article_extractor = article_extractor
        self.date_filter = date_filter

    def process_block(self, block: Block) -> list[NewsItem]:
        """
        Processes a complete block.
        - Respects MAX_NOTICIAS_POR_BLOQUE (5) limit
        - Waits 1 second between HTTP requests
        - Catches AdapterError per URL without interrupting the block
        """
        noticias = []
        today = date.today()

        for url in block.urls:
            if len(noticias) >= self.MAX_NOTICIAS_POR_BLOQUE:
                break

            print(f"   🔗 Analizando: {url[:50]}...")

            try:
                adapter = self.adapter_factory.get_adapter(url)
                html_portada = adapter.fetch_page(url)
                article_urls = self.portada_parser.extract_article_links(html_portada, url)

                for article_url in article_urls:
                    if len(noticias) >= self.MAX_NOTICIAS_POR_BLOQUE:
                        break

                    time.sleep(self.DELAY_BETWEEN_REQUESTS)

                    try:
                        article_adapter = self.adapter_factory.get_adapter(article_url)
                        html_article = article_adapter.fetch_page(article_url)
                        source_name = url.split('/')[2].replace('www.', '')
                        news_item = self.article_extractor.extract(html_article, article_url, source_name)

                        if news_item and self.date_filter.is_today(news_item.fecha, today):
                            noticias.append(news_item)
                            print(f"   ✅ Noticia: {news_item.titulo[:50]}...")
                    except AdapterError as e:
                        print(f"   ⚠️ Error en artículo {article_url[:50]}: {e}")
                        continue

                time.sleep(self.DELAY_BETWEEN_REQUESTS)

            except AdapterError as e:
                print(f"   ❌ Error en fuente {url[:50]}: {e}")
                continue

        return noticias

    def run(self, blocks: list[Block]) -> dict[str, list[NewsItem]]:
        """
        Processes all blocks and returns the results dictionary.
        Preserves block order.
        """
        print("🚀 Iniciando extracción Vinotinto Galáctica...")
        results = {}

        for block in blocks:
            print(f"\n📂 Bloque: {block.name}")
            noticias = self.process_block(block)
            results[block.name] = noticias

        return results


# ==========================================
# TXT WRITER
# ==========================================

class TxtWriter:
    JULL_INSTRUCTIONS = """
================================================================================
INSTRUCCIONES PARA JULL
================================================================================

Eres JULL, una periodista deportiva venezolana con voz cercana, fluida y apasionada.
Tu misión es transformar las noticias anteriores en un NOTICIERO LARGO y 4 SHORTS adicionales.

ESTRUCTURA DEL NOTICIERO LARGO:
- Presenta las noticias en el orden exacto de los bloques indicados arriba
- Usa un tono conversacional, dinámico y emocionante
- Conecta las noticias con transiciones naturales
- Incluye contexto y análisis breve cuando sea relevante

4 SHORTS ADICIONALES:
- Selecciona las 4 noticias más impactantes del día
- Cada Short debe ser conciso (máximo 60 segundos de lectura)
- Usa un gancho inicial poderoso para captar la atención

PROHIBICIONES ABSOLUTAS:
- NO uses cierres temporales como "mañana", "hoy", "esta noche", "en los próximos días"
- NO hagas referencias al tiempo futuro o presente inmediato
- NO uses frases como "veremos qué pasa" o "habrá que esperar"
================================================================================
"""

    def write(self, results: dict, fecha: str, output_path: str) -> None:
        """
        Generates PROMPT_PARA_JULL.txt with structured format.
        Omits blocks with no news.
        """
        lines = []
        lines.append("PROTOCOLO VINOTINTO GALÁCTICO - DATA DE EXTRACCIÓN")
        lines.append(f"FECHA: {fecha}")
        lines.append("")

        for block_name, noticias in results.items():
            if not noticias:
                continue

            lines.append("=" * 80)
            lines.append(f"=== SECCIÓN: {block_name} ===")
            lines.append("=" * 80)
            lines.append("")

            for i, noticia in enumerate(noticias, 1):
                lines.append(f"NOTICIA {i}:")
                lines.append(f"TITULO: {noticia.titulo}")

                if noticia.subtitulos:
                    lines.append(f"SUBTITULOS: {' | '.join(noticia.subtitulos)}")

                lines.append(f"FECHA: {noticia.fecha}")
                lines.append("CONTENIDO:")
                lines.append(noticia.contenido)
                lines.append(f"AUTOR: {noticia.autor}")
                lines.append(f"FUENTE: {noticia.fuente}")
                lines.append(f"LINK: {noticia.link}")
                lines.append("")

        lines.append(self.JULL_INSTRUCTIONS)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))


# ==========================================
# HTML WRITER
# ==========================================

class HtmlWriter:
    CSS = """
        body { font-family: Arial, sans-serif; background: #1a0a0a; color: #f0e0e0; margin: 0; padding: 20px; }
        h1.site-title { color: #800020; text-align: center; font-size: 2.5em; border-bottom: 3px solid #800020; padding-bottom: 10px; }
        .fecha-header { text-align: center; color: #cc9999; margin-bottom: 30px; }
        .bloque { margin-bottom: 40px; border: 1px solid #800020; border-radius: 8px; padding: 20px; background: #2a0a0a; }
        .bloque-titulo { color: #800020; font-size: 1.8em; border-bottom: 2px solid #800020; padding-bottom: 8px; margin-bottom: 20px; }
        .noticia { margin-bottom: 30px; border-bottom: 1px solid #4a1a1a; padding-bottom: 20px; }
        .noticia-titulo { color: #ff6666; font-size: 1.3em; margin-bottom: 8px; }
        .noticia-subtitulo { color: #cc9999; font-style: italic; margin-bottom: 5px; }
        .noticia-fecha { color: #999; font-size: 0.9em; margin-bottom: 8px; }
        .noticia-contenido { text-align: justify; line-height: 1.6; margin-bottom: 10px; }
        .noticia-meta { color: #cc9999; font-size: 0.85em; }
        .noticia-link a { color: #800020; }
    """

    def write(self, results: dict, fecha: str, output_path: str) -> None:
        """
        Generates REVISION_VISUAL.html with sports web style.
        Omits blocks with no news.
        """
        html_parts = []
        html_parts.append(f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vinotinto Galáctico - {fecha}</title>
    <style>{self.CSS}</style>
</head>
<body>
    <h1 class="site-title">⚽ VINOTINTO GALÁCTICO</h1>
    <p class="fecha-header">Edición del {fecha}</p>
""")

        for block_name, noticias in results.items():
            if not noticias:
                continue

            html_parts.append(f'    <div class="bloque">\n')
            html_parts.append(f'        <h2 class="bloque-titulo">{block_name}</h2>\n')

            for i, noticia in enumerate(noticias, 1):
                html_parts.append(f'        <div class="noticia">\n')
                html_parts.append(f'            <h3 class="noticia-titulo">{i}. {noticia.titulo}</h3>\n')

                for subtitulo in noticia.subtitulos:
                    html_parts.append(f'            <p class="noticia-subtitulo">{subtitulo}</p>\n')

                html_parts.append(f'            <p class="noticia-fecha">📅 {noticia.fecha}</p>\n')

                # Content with text-align: justify (applied via CSS class)
                contenido_html = noticia.contenido.replace('\n\n', '</p><p>').replace('\n', '<br>')
                html_parts.append(f'            <div class="noticia-contenido"><p>{contenido_html}</p></div>\n')

                html_parts.append(f'            <p class="noticia-meta">✍️ <strong>Autor:</strong> {noticia.autor} | 📰 <strong>Fuente:</strong> {noticia.fuente}</p>\n')
                html_parts.append(f'            <p class="noticia-link"><a href="{noticia.link}" target="_blank">🔗 Ver artículo original</a></p>\n')
                html_parts.append(f'        </div>\n')

            html_parts.append(f'    </div>\n')

        html_parts.append('</body>\n</html>')

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(''.join(html_parts))


# ==========================================
# CONFIGURACIÓN PROTOCOLO VINOTINTO GALÁCTICO
# ==========================================
MAX_NOTICIAS_POR_BLOQUE = 5
FECHA_HOY = datetime.now().strftime("%d/%m/%Y")
EXCEL_FILE = 'Prensa Deportiva.xlsx'
OUTPUT_TXT = 'PROMPT_PARA_JULL.txt'
OUTPUT_HTML = 'REVISION_VISUAL.html'

def extraer_articulo_real(url):
    """Extrae el contenido de una noticia específica."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        titulo = soup.find('h1').get_text().strip() if soup.find('h1') else "Sin título"
        # Buscamos el cuerpo de la noticia
        parrafos = soup.find_all('p')
        contenido = "\n".join([p.get_text().strip() for p in parrafos if len(p.get_text()) > 70])
        
        return {
            'titulo': titulo,
            'contenido': contenido[:2000], # Suficiente para el guion
            'link': url
        }
    except:
        return None

def buscar_noticias_en_portada(url_portada):
    """Si el link es una sección, busca los links de las noticias dentro."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url_portada, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        links_encontrados = []
        # Buscamos enlaces que parezcan noticias (filtros básicos para AS, Marca, Mundo Deportivo)
        for a in soup.find_all('a', href=True):
            href = a['href']
            # Evitar links basura, quedarnos con los que parecen artículos
            if any(x in href for x in ['/articulo/', '/noticias/', '.html', '/2024/', '/2025/']):
                if href.startswith('/'):
                    # Si el link es relativo, reconstruir con la base del dominio
                    href = urljoin(url_portada, href)
                
                if href not in links_encontrados and href != url_portada:
                    links_encontrados.append(href)
            
            if len(links_encontrados) >= 2: # Tomamos las 2 más frescas de cada fuente
                break
        return links_encontrados
    except:
        return []

def procesar_excel():
    if not os.path.exists(EXCEL_FILE):
        print(f"❌ No se encontró {EXCEL_FILE}")
        return

    # Leer el Excel (asumiendo que los datos están en la primera columna)
    df = pd.read_excel(EXCEL_FILE, header=None)
    
    datos_finales = {}
    categoria_actual = "Sin Categoría"
    
    print("🚀 Iniciando extracción Vinotinto Galáctica...")

    for index, row in df.iterrows():
        linea = str(row[0]).strip()
        
        if not linea or linea == 'nan' or 'Pagina Original' in linea:
            continue

        # Si termina en ":" es una categoría
        if linea.endswith(':'):
            categoria_actual = linea.replace(':', '')
            datos_finales[categoria_actual] = []
            print(f"\n📂 Categoría: {categoria_actual}")
            continue
        
        # Si es un link y no hemos excedido el límite de 5 por bloque
        if linea.startswith('http') and len(datos_finales[categoria_actual]) < MAX_NOTICIAS_POR_BLOQUE:
            print(f"   🔗 Analizando fuente: {linea[:50]}...")
            
            # Paso 1: Ir a la portada y buscar links de noticias
            links_noticias = buscar_noticias_en_portada(linea)
            
            # Paso 2: Extraer el contenido de esas noticias
            for lnk in links_noticias:
                if len(datos_finales[categoria_actual]) >= MAX_NOTICIAS_POR_BLOQUE:
                    break
                
                noticia = extraer_articulo_real(lnk)
                if noticia and len(noticia['contenido']) > 200:
                    datos_finales[categoria_actual].append(noticia)
                    print(f"      ✅ Noticia extraída: {noticia['titulo'][:50]}...")
            
            time.sleep(1) # Respeto a los servidores

    return datos_finales

def guardar_resultados(datos):
    # Generar TXT para JULL
    with open(OUTPUT_TXT, 'w', encoding='utf-8') as f:
        f.write(f"PROTOCOLO VINOTINTO GALÁCTICO - DATA DE EXTRACCIÓN\nFECHA: {FECHA_HOY}\n\n")
        for cat, noticias in datos.items():
            if not noticias: continue
            f.write(f"=== SECCIÓN: {cat.upper()} ===\n")
            for i, n in enumerate(noticias):
                f.write(f"NOTICIA {i+1}:\nTITULO: {n['titulo']}\nCONTENIDO: {n['contenido']}\nLINK: {n['link']}\n\n")

    # Generar HTML Visual
    html = f"<html><head><meta charset='utf-8'><style>body{{font-family:sans-serif; background:#f0f0f0;}} .box{{background:white; margin:20px auto; padding:20px; max-width:800px; border-top:8px solid #800020; shadow: 2px 2px 5px #ccc;}} h1{{color:#800020;}} .cat{{background:#800020; color:white; padding:10px; margin-top:30px;}}</style></head><body><h1 style='text-align:center;'>REVISIÓN VINOTINTO GALÁCTICO</h1>"
    for cat, noticias in datos.items():
        if not noticias: continue
        html += f"<div class='cat'>{cat}</div>"
        for n in noticias:
            html += f"<div class='box'><h3>{n['titulo']}</h3><p>{n['contenido'][:400]}...</p><a href='{n['link']}'>Leer Original</a></div>"
    html += "</body></html>"
    
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html)

if __name__ == "__main__":
    resultados = procesar_excel()
    if resultados:
        guardar_resultados(resultados)
        print(f"\n✅ PROCESO COMPLETADO")
        print(f"📝 Archivo para Prompt: {OUTPUT_TXT}")
        print(f"🖼️ Archivo para Revisión: {OUTPUT_HTML}")