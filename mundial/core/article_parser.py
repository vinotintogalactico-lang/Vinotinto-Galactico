from __future__ import annotations
import re
from bs4 import BeautifulSoup
from readability import Document

def parse_article(html: str, url: str, **kwargs) -> dict:
    """
    Extrae los datos de un artículo usando Readability para limpiar la basura (ads, menus, etc.)
    Los extractores específicos pueden pasar kwargs (title, subtitle, author, date, body_override)
    si ya extrajeron estos datos con mayor precisión.
    """
    doc = Document(html)
    
    # 1. Título
    title = kwargs.get("title")
    if not title:
        title = doc.title()
        if not title:
            soup = BeautifulSoup(html, "html.parser")
            h1 = soup.find("h1")
            title = h1.get_text(strip=True) if h1 else "Sin título"
            
    # 2. Cuerpo limpio
    body = kwargs.get("body_override")
    if not body:
        # Extraemos el HTML limpio del artículo
        clean_html = doc.summary()
        clean_soup = BeautifulSoup(clean_html, "html.parser")
        
        # Eliminar enlaces y etiquetas innecesarias que Readability no haya quitado
        for a in clean_soup.find_all("a"):
            a.unwrap() # Deja el texto, quita el link
            
        paragraphs = []
        for tag in clean_soup.find_all(["p", "h2", "h3", "h4", "li"]):
            text = tag.get_text(separator=" ", strip=True)
            # Filtro adicional anti-basura
            if len(text) > 15 and not any(x in text.lower() for x in [
                "iniciar sesión", "suscríbete", "menú", "leer más", "te puede interesar", "newsletter", "publicidad"
            ]):
                paragraphs.append(text)
                
        body = "\n\n".join(paragraphs)

    date_val = kwargs.get("date")
    if not date_val:
        # 1. Intentar con meta etiquetas
        meta_tags = [
            {"property": "article:published_time"},
            {"property": "og:pubdate"},
            {"name": "pubdate"},
            {"name": "datePublished"}
        ]
        soup = BeautifulSoup(html, "html.parser")
        for tag in meta_tags:
            meta = soup.find("meta", attrs=tag)
            if meta and meta.get("content"):
                date_val = meta["content"]
                break
                
        # 2. Intentar con JSON-LD
        if not date_val:
            import json
            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(script.string)
                    nodes = data if isinstance(data, list) else [data]
                    for node in nodes:
                        subnodes = node.get("@graph", [node]) if isinstance(node, dict) else []
                        for sn in subnodes:
                            if isinstance(sn, dict) and sn.get("datePublished"):
                                date_val = sn["datePublished"]
                                break
                except:
                    pass
                if date_val: break

    return {
        "title": title.strip(),
        "subtitle": kwargs.get("subtitle", "").strip(),
        "author": kwargs.get("author", "Redacción").strip(),
        "date": date_val.strip() if date_val else "",
        "body": body,
        "url": url
    }