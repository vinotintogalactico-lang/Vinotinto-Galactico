"""
Unit tests for PortadaParser (Task 4.2)
Validates: Requirements 2.1
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from VG_Extractor import PortadaParser

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), '..', 'fixtures')
BASE_URL = "https://example.com"


def load_fixture(filename: str) -> str:
    path = os.path.join(FIXTURES_DIR, filename)
    with open(path, encoding='utf-8') as f:
        return f.read()


@pytest.fixture
def parser():
    return PortadaParser()


@pytest.fixture
def portada_html():
    return load_fixture('sample_portada.html')


# ── test_portada_parser_returns_article_urls ──────────────────────────────────

def test_portada_parser_returns_article_urls(parser, portada_html):
    """Only article URLs are returned; social, tag, and anchor links are excluded."""
    urls = parser.extract_article_links(portada_html, BASE_URL)

    # Must contain the two absolute article links
    assert "https://example.com/noticias/articulo-1" in urls
    assert "https://example.com/2024/nota" in urls

    # Must NOT contain excluded links
    for url in urls:
        assert "twitter.com" not in url, "Social media links must be excluded"
        assert "/tag/" not in url, "Tag links must be excluded"
        assert url != "#section", "Anchor links must be excluded"
        assert url != "https://example.com/contacto", "Non-article links must be excluded"


# ── test_portada_parser_resolves_relative_urls ────────────────────────────────

def test_portada_parser_resolves_relative_urls(parser, portada_html):
    """Relative URLs are resolved to absolute using base_url."""
    urls = parser.extract_article_links(portada_html, BASE_URL)

    # The relative link /futbol/partido-hoy.html must be resolved
    assert "https://example.com/futbol/partido-hoy.html" in urls

    # All returned URLs must be absolute
    for url in urls:
        assert url.startswith("http"), f"URL should be absolute: {url}"


# ── test_portada_parser_max_3_results ─────────────────────────────────────────

def test_portada_parser_max_3_results(parser):
    """At most 3 URLs are returned even when more article links are present."""
    # Build HTML with 5 valid article links
    links = "\n".join(
        f'<a href="https://example.com/noticias/articulo-{i}">Artículo {i}</a>'
        for i in range(1, 6)
    )
    html = f"<html><body>{links}</body></html>"

    urls = parser.extract_article_links(html, BASE_URL)
    assert len(urls) <= 3
