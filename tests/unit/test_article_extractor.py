"""
Unit tests for ArticleExtractor (Task 5.2)
Validates: Requirements 3.2, 3.3
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from VG_Extractor import ArticleExtractor, NewsItem

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), '..', 'fixtures')


def load_fixture(filename: str) -> str:
    with open(os.path.join(FIXTURES_DIR, filename), encoding='utf-8') as f:
        return f.read()


# ── Full extraction ───────────────────────────────────────────────────────────

def test_article_extractor_full_extraction():
    """All fields are correctly extracted from the full fixture."""
    html = load_fixture('sample_article.html')
    extractor = ArticleExtractor()
    result = extractor.extract(html, 'https://example.com/articulo-1', 'Example')

    assert result is not None
    assert isinstance(result, NewsItem)
    assert result.titulo == 'Real Madrid golea al Barcelona en el Clásico'
    assert result.fecha == '2025-01-15'
    assert result.autor == 'Juan Pérez'
    assert len(result.subtitulos) == 2
    assert 'Primer tiempo' in result.subtitulos[0]
    assert len(result.contenido) >= 200
    assert result.fuente == 'Example'
    assert result.link == 'https://example.com/articulo-1'


# ── No author ─────────────────────────────────────────────────────────────────

def test_article_extractor_no_author():
    """autor is 'No disponible' when no author markup is present (Requirement 3.2)."""
    html = """<!DOCTYPE html>
<html><body>
  <article>
    <h1>Noticia sin autor</h1>
    <time datetime="2025-01-15">15 de enero de 2025</time>
    <p>Este es el primer párrafo de la noticia que tiene suficiente contenido para superar el umbral mínimo requerido de setenta caracteres por párrafo.</p>
    <p>Este es el segundo párrafo de la noticia que también tiene suficiente contenido para superar el umbral mínimo requerido de setenta caracteres por párrafo.</p>
    <p>Este es el tercer párrafo de la noticia que igualmente tiene suficiente contenido para superar el umbral mínimo requerido de setenta caracteres por párrafo.</p>
  </article>
</body></html>"""
    extractor = ArticleExtractor()
    result = extractor.extract(html, 'https://example.com/sin-autor', 'Example')

    assert result is not None
    assert result.autor == 'No disponible'


# ── No subtitles ──────────────────────────────────────────────────────────────

def test_article_extractor_no_subtitles():
    """subtitulos is an empty list when there are no h2 or h3 tags (Requirement 3.3)."""
    html = """<!DOCTYPE html>
<html><body>
  <article>
    <h1>Noticia sin subtítulos</h1>
    <time datetime="2025-01-15">15 de enero de 2025</time>
    <a rel="author">Carlos López</a>
    <p>Este es el primer párrafo de la noticia que tiene suficiente contenido para superar el umbral mínimo requerido de setenta caracteres por párrafo.</p>
    <p>Este es el segundo párrafo de la noticia que también tiene suficiente contenido para superar el umbral mínimo requerido de setenta caracteres por párrafo.</p>
    <p>Este es el tercer párrafo de la noticia que igualmente tiene suficiente contenido para superar el umbral mínimo requerido de setenta caracteres por párrafo.</p>
  </article>
</body></html>"""
    extractor = ArticleExtractor()
    result = extractor.extract(html, 'https://example.com/sin-subtitulos', 'Example')

    assert result is not None
    assert result.subtitulos == []


# ── Short content returns None ────────────────────────────────────────────────

def test_article_extractor_short_content_returns_none():
    """Returns None when total content is less than 200 characters."""
    html = """<!DOCTYPE html>
<html><body>
  <article>
    <h1>Noticia corta</h1>
    <p>Texto muy corto.</p>
  </article>
</body></html>"""
    extractor = ArticleExtractor()
    result = extractor.extract(html, 'https://example.com/corta', 'Example')

    assert result is None
