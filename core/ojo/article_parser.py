from __future__ import annotations
import re
from bs4 import BeautifulSoup, Tag


# ── Selectores a eliminar (publicidad, nav, widgets, etc.) ──────────────────
_REMOVE_SELECTORS = [
    # Publicidad
    "[class*='ad']", "[id*='ad']", "[class*='advert']",
    "[class*='publicidad']", "[class*='promo']", "[class*='sponsor']",
    "[class*='patrocinado']", "[class*='sponsored']",
    # Redes sociales
    "[class*='social']", "[class*='share']", "[class*='compartir']",
    "[class*='tweet']", "[class*='facebook']", "[class*='instagram']",
    "[class*='whatsapp']",
    # Noticias relacionadas / recomendaciones
    "[class*='related']", "[class*='relacionad']", "[class*='recomend']",
    "[class*='mas-noticias']", "[class*='more-news']", "[class*='te-puede']",
    "[class*='also-read']", "[class*='read-more']",
    # Newsletter
    "[class*='newsletter']", "[class*='suscri']", "[class*='subscribe']",
    # Comentarios
    "[class*='comment']", "[class*='comentario']", "[id*='comment']",
    # Navegación
    "nav", "header", "footer",
    "[class*='breadcrumb']", "[class*='menu']", "[class*='navbar']",
    "[class*='pagination']",
    # Widgets externos
    "iframe", "script", "style", "noscript",
    "[class*='widget']", "[class*='sidebar']", "[class*='aside']",
    # Encuestas / votaciones
    "[class*='poll']", "[class*='encuesta']", "[class*='vote']",
    # Tags / etiquetas
    "[class*='tags']", "[class*='etiquetas']", "[class*='label']",
]

# ── Selectores de contenido principal (en orden de prioridad) ───────────────
_ARTICLE_SELECTORS = [
    "article",
    "[class*='article-body']",
    "[class*='article-content']",
    "[class*='entry-content']",
    "[class*='post-content']",
    "[class*='news-body']",
    "[class*='noticia-cuerpo']",
    "[class*='cuerpo-noticia']",
    "[class*='article__body']",
    "[class*='news__body']",
    "[class*='story-body']",
    "main",
    "[role='main']",
]

# ── Selectores de subtítulo ──────────────────────────────────────────────────
_SUBTITLE_SELECTORS = [
    "[class*='subtitle']", "[class*='subtitulo']", "[class*='subheadline']",
    "[class*='lead']", "[class*='standfirst']", "[class*='deck']",
    "h2.subtitle", ".article__subtitle", ".news-subtitle",
]

# ── Selectores de autor ──────────────────────────────────────────────────────
_AUTHOR_SELECTORS = [
    "[class*='author']", "[class*='autor']", "[rel='author']",
    "[class*='byline']", "[class*='firma']",
]

# ── Selectores de fecha ──────────────────────────────────────────────────────
_DATE_SELECTORS = [
    "time", "[class*='date']", "[class*='fecha']",
    "[class*='timestamp']", "[class*='published']", "[class*='publicado']",
    "[itemprop='datePublished']", "[property='article:published_time']",
]


def parse_article(html: str, url: str = "") -> dict:
    """
    Extrae título, subtítulo, autor, fecha y cuerpo limpio de un artículo HTML.
    Devuelve un dict con las claves: title, subtitle, author, date, url, body.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Título
    title = _get_title(soup)

    # Subtítulo
    subtitle = _get_first_text(soup, _SUBTITLE_SELECTORS)

    # Autor
    author = _get_first_text(soup, _AUTHOR_SELECTORS)

    # Fecha (texto + atributo datetime)
    date_str = _get_date(soup)

    # Cuerpo
    body = _get_body(soup)

    return {
        "title": title,
        "subtitle": subtitle,
        "author": author,
        "date": date_str,
        "url": url,
        "body": body,
    }


def _get_title(soup: BeautifulSoup) -> str:
    for sel in ["h1", "[class*='title']", "[class*='titulo']", "title"]:
        tag = soup.select_one(sel)
        if tag:
            return tag.get_text(strip=True)
    return ""


def _get_first_text(soup: BeautifulSoup, selectors: list[str]) -> str:
    for sel in selectors:
        tag = soup.select_one(sel)
        if tag:
            text = tag.get_text(strip=True)
            if text:
                return text
    return ""


def _get_date(soup: BeautifulSoup) -> str:
    for sel in _DATE_SELECTORS:
        tag = soup.select_one(sel)
        if tag:
            # Preferir atributo datetime si existe
            dt = tag.get("datetime") or tag.get("content") or tag.get_text(strip=True)
            if dt:
                return str(dt)
    return ""


def _get_body(soup: BeautifulSoup) -> str:
    # Clonar para no mutilar el soup original
    working = BeautifulSoup(str(soup), "html.parser")

    # Eliminar elementos no deseados
    for sel in _REMOVE_SELECTORS:
        for tag in working.select(sel):
            tag.decompose()

    # Buscar contenedor del artículo
    container: Tag | None = None
    for sel in _ARTICLE_SELECTORS:
        container = working.select_one(sel)
        if container:
            break

    if container is None:
        container = working.find("body") or working

    # Extraer párrafos
    paragraphs = []
    for p in container.find_all(["p", "h2", "h3", "h4", "blockquote"]):
        text = p.get_text(separator=" ", strip=True)
        if len(text) > 30:  # Filtrar fragmentos muy cortos / nav items
            paragraphs.append(text)

    body = "\n\n".join(paragraphs)
    # Colapsar espacios múltiples
    body = re.sub(r"[ \t]{2,}", " ", body)
    return body.strip()
