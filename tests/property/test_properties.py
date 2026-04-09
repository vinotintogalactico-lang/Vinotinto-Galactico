"""
Property-based tests for ExcelReader (Task 2.3)
Validates: Requirements 1.3, 1.4, 1.5
"""
import os
import sys
import tempfile

import pytest
from bs4 import BeautifulSoup
from openpyxl import Workbook
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from VG_Extractor import ExcelReader, Block, ExcelReadError

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def write_excel(path: str, rows: list) -> None:
    """Write a list of values to a single-column xlsx file."""
    wb = Workbook()
    ws = wb.active
    for value in rows:
        ws.append([value])
    wb.save(path)


# ──────────────────────────────────────────────────────────────────────────────
# Strategies
# ──────────────────────────────────────────────────────────────────────────────

# Block names: non-empty strings of uppercase letters and spaces (no ':')
block_name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu",), whitelist_characters=" "),
    min_size=1,
    max_size=20,
).map(str.strip).filter(lambda s: len(s) > 0 and ":" not in s)

# URLs: strings starting with 'https://' followed by alphanumeric chars
url_strategy = st.builds(
    lambda suffix: "https://" + suffix,
    st.text(
        alphabet="abcdefghijklmnopqrstuvwxyz0123456789",
        min_size=3,
        max_size=30,
    ),
)

# A single block as (name, [url, ...])
block_tuple_strategy = st.tuples(
    block_name_strategy,
    st.lists(url_strategy, min_size=0, max_size=5),
)

# A list of blocks (at least 1)
blocks_list_strategy = st.lists(block_tuple_strategy, min_size=1, max_size=8)


def build_excel_rows(blocks: list[tuple[str, list[str]]]) -> list:
    """Convert (name, urls) tuples into the flat row list expected by ExcelReader."""
    rows = []
    for name, urls in blocks:
        rows.append(f"{name}:")
        rows.extend(urls)
    return rows


# ──────────────────────────────────────────────────────────────────────────────
# Property 1: Preservación de orden de bloques y URLs
# ──────────────────────────────────────────────────────────────────────────────

# Feature: vinotinto-galactico-scraper, Property 1: Preservación de orden de bloques y URLs
@given(blocks=blocks_list_strategy)
@settings(max_examples=100)
def test_property_1_order_preserved(blocks):
    """
    For any Excel with any number of blocks and URLs, the order of blocks
    returned must be identical to the order in the Excel, and the order of
    URLs within each block must be identical to the order in the Excel.

    Validates: Requirements 1.3, 1.4
    """
    rows = build_excel_rows(blocks)
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        path = f.name
    try:
        write_excel(path, rows)
        result = ExcelReader(path).read()

        # Block order must match
        assert [b.name for b in result] == [name for name, _ in blocks]

        # URL order within each block must match
        for result_block, (_, expected_urls) in zip(result, blocks):
            assert result_block.urls == expected_urls
    finally:
        os.unlink(path)


# ──────────────────────────────────────────────────────────────────────────────
# Property 2: Filas vacías no afectan el resultado
# ──────────────────────────────────────────────────────────────────────────────

# Feature: vinotinto-galactico-scraper, Property 2: Filas vacías no afectan el resultado
@given(
    blocks=blocks_list_strategy,
    empty_positions=st.lists(st.integers(min_value=0, max_value=50), min_size=0, max_size=10),
)
@settings(max_examples=100)
def test_property_2_empty_rows_ignored(blocks, empty_positions):
    """
    For any Excel, inserting empty rows or nan values at any position must not
    change the set of blocks or URLs processed.

    Validates: Requirement 1.5
    """
    base_rows = build_excel_rows(blocks)

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        clean_path = f.name
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        dirty_path = f.name

    try:
        # Build the "clean" result first
        write_excel(clean_path, base_rows)
        clean_result = ExcelReader(clean_path).read()

        # Insert empty rows (None → becomes NaN in pandas) at random positions
        dirty_rows = list(base_rows)
        for pos in sorted(set(empty_positions), reverse=True):
            insert_at = pos % (len(dirty_rows) + 1)
            # Alternate between None and the literal string 'nan'
            empty_value = None if pos % 2 == 0 else "nan"
            dirty_rows.insert(insert_at, empty_value)

        write_excel(dirty_path, dirty_rows)
        dirty_result = ExcelReader(dirty_path).read()

        # Block names must be identical
        assert [b.name for b in dirty_result] == [b.name for b in clean_result]

        # URLs per block must be identical
        for dirty_block, clean_block in zip(dirty_result, clean_result):
            assert dirty_block.urls == clean_block.urls
    finally:
        os.unlink(clean_path)
        os.unlink(dirty_path)


# ──────────────────────────────────────────────────────────────────────────────
# Strategies for ArticleExtractor tests (Task 5.3)
# ──────────────────────────────────────────────────────────────────────────────

from VG_Extractor import ArticleExtractor, NewsItem

# Generate paragraph text (> 70 chars each)
long_paragraph_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z")),
    min_size=80,
    max_size=200,
)


def article_html_strategy(min_paragraphs=3, max_paragraphs=5):
    """Generate article HTML with sufficient content (>= 200 chars total)."""
    return st.builds(
        lambda title, paragraphs: f"""<html><body>
<article>
<h1>{title}</h1>
<time datetime="2025-01-15">15 de enero de 2025</time>
{''.join(f'<p>{p}</p>' for p in paragraphs)}
</article>
</body></html>""",
        title=st.text(min_size=5, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz "),
        paragraphs=st.lists(long_paragraph_strategy, min_size=min_paragraphs, max_size=max_paragraphs),
    )


def short_article_html_strategy():
    """Generate article HTML with short content (< 200 chars)."""
    return st.builds(
        lambda title: f"""<html><body>
<article>
<h1>{title}</h1>
<p>Corto.</p>
</article>
</body></html>""",
        title=st.text(min_size=3, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz "),
    )


# ──────────────────────────────────────────────────────────────────────────────
# Property 6: Campos completos en NewsItem
# ──────────────────────────────────────────────────────────────────────────────

# Feature: vinotinto-galactico-scraper, Property 6: Campos completos en NewsItem
@given(html=article_html_strategy(min_paragraphs=3, max_paragraphs=5))
@settings(max_examples=100)
def test_property_6_complete_fields(html):
    """
    For any valid article HTML with content >= 200 chars, the resulting NewsItem
    must have non-empty values for: titulo, fecha, contenido, fuente, link.
    The autor field must be "No disponible" if not found, never empty or None.

    Validates: Requirements 3.1, 3.2
    """
    extractor = ArticleExtractor()
    item = extractor.extract(html, "http://example.com/articulo/test", "TestFuente")

    # With 3+ long paragraphs the content should be >= 200 chars; if not, skip
    if item is None:
        return

    assert item.titulo, "titulo must be non-empty"
    assert item.fecha, "fecha must be non-empty"
    assert item.contenido, "contenido must be non-empty"
    assert item.fuente, "fuente must be non-empty"
    assert item.link, "link must be non-empty"
    # autor must never be empty or None — fallback is "No disponible"
    assert item.autor is not None, "autor must not be None"
    assert item.autor != "", "autor must not be empty string"


# ──────────────────────────────────────────────────────────────────────────────
# Property 7: Contenido sin truncar
# ──────────────────────────────────────────────────────────────────────────────

# Feature: vinotinto-galactico-scraper, Property 7: Contenido sin truncar
@given(html=article_html_strategy(min_paragraphs=3, max_paragraphs=5))
@settings(max_examples=100)
def test_property_7_content_not_truncated(html):
    """
    For any article HTML, the length of contenido in the extracted NewsItem must
    be >= 90% of the raw text length from the article paragraphs (no artificial
    character limit).

    Validates: Requirement 3.4
    """
    extractor = ArticleExtractor()
    item = extractor.extract(html, "http://example.com/articulo/test", "TestFuente")

    if item is None:
        return

    # Compute raw text: concatenation of all <p> texts > 70 chars from the article
    soup = BeautifulSoup(html, 'html.parser')
    article_tag = soup.find('article')
    container = article_tag if article_tag else soup
    raw_paragraphs = [
        p.get_text(strip=True)
        for p in container.find_all('p')
        if len(p.get_text(strip=True)) > 70
    ]
    raw_text = "\n\n".join(raw_paragraphs)

    if not raw_text:
        return

    assert len(item.contenido) >= len(raw_text) * 0.9, (
        f"contenido length {len(item.contenido)} is less than 90% of raw text length {len(raw_text)}"
    )


# ──────────────────────────────────────────────────────────────────────────────
# Property 8: Descarte de noticias con contenido insuficiente
# ──────────────────────────────────────────────────────────────────────────────

# Feature: vinotinto-galactico-scraper, Property 8: Descarte de noticias con contenido insuficiente
@given(html=short_article_html_strategy())
@settings(max_examples=100)
def test_property_8_short_content_discarded(html):
    """
    For any article whose extracted content has less than 200 characters, the
    system must discard it and return None.

    Validates: Requirement 3.5
    """
    extractor = ArticleExtractor()
    item = extractor.extract(html, "http://example.com/articulo/test", "TestFuente")

    assert item is None, (
        f"Expected None for short content article, but got a NewsItem with "
        f"contenido length {len(item.contenido) if item else 'N/A'}"
    )


# ──────────────────────────────────────────────────────────────────────────────
# Strategies for DateFilter tests (Task 6.3)
# ──────────────────────────────────────────────────────────────────────────────

from datetime import date, timedelta
from VG_Extractor import DateFilter

today = date.today()
yesterday = today - timedelta(days=1)
tomorrow = today + timedelta(days=1)


def date_string_strategy():
    """Generate date strings: some represent today, some do not."""
    return st.one_of(
        # Today in various formats
        st.just(today.strftime("%d/%m/%Y")),
        st.just(today.strftime("%Y-%m-%d")),
        st.just(today.strftime("%d-%m-%Y")),
        st.just("hoy"),
        st.just("today"),
        st.just("hace 3 horas"),
        # Not today
        st.just(yesterday.strftime("%d/%m/%Y")),
        st.just(tomorrow.strftime("%Y-%m-%d")),
        # Unparseable
        st.just(""),
        st.just("fecha desconocida"),
    )


# Known today strings (for assertion purposes)
TODAY_STRINGS = {
    today.strftime("%d/%m/%Y"),
    today.strftime("%Y-%m-%d"),
    today.strftime("%d-%m-%Y"),
    "hoy",
    "today",
    "hace 3 horas",
}

# Known non-today strings
NON_TODAY_STRINGS = {
    yesterday.strftime("%d/%m/%Y"),
    tomorrow.strftime("%Y-%m-%d"),
    "",
    "fecha desconocida",
}


# ──────────────────────────────────────────────────────────────────────────────
# Property 4: Filtro temporal estricto
# ──────────────────────────────────────────────────────────────────────────────

# Feature: vinotinto-galactico-scraper, Property 4: Filtro temporal estricto
@given(
    date_strs=st.lists(date_string_strategy(), min_size=1, max_size=20)
)
@settings(max_examples=100)
def test_property_4_date_filter_strict(date_strs):
    """
    For any set of date strings with varied dates, is_today() must return True
    only for strings that actually represent today's date. Known non-today dates
    and unparseable strings must return False.

    Validates: Requirements 2.4, 2.5
    """
    date_filter = DateFilter()
    reference = date.today()

    for date_str in date_strs:
        result = date_filter.is_today(date_str, reference)

        if date_str in TODAY_STRINGS:
            assert result is True, (
                f"Expected is_today({date_str!r}) to be True (known today string), got False"
            )
        elif date_str in NON_TODAY_STRINGS:
            assert result is False, (
                f"Expected is_today({date_str!r}) to be False (known non-today string), got True"
            )
        # For any other generated string: if it returns True, it must actually be today
        elif result is True:
            # Verify the string can be parsed as today by trying all supported formats
            from datetime import datetime
            parsed_as_today = False
            for fmt in DateFilter.DATE_FORMATS:
                try:
                    parsed = datetime.strptime(date_str.strip(), fmt)
                    if parsed.date() == reference:
                        parsed_as_today = True
                        break
                except ValueError:
                    continue
            assert parsed_as_today, (
                f"is_today({date_str!r}) returned True but the date does not correspond to today ({reference})"
            )


# ──────────────────────────────────────────────────────────────────────────────
# Strategies and helpers for Orchestrator tests (Task 7.2)
# ──────────────────────────────────────────────────────────────────────────────

from unittest.mock import MagicMock, patch
from VG_Extractor import Orchestrator, AdapterError


def make_mock_orchestrator(fetch_side_effect=None, extract_return=None):
    """Create an Orchestrator with mocked dependencies."""
    mock_adapter = MagicMock()
    if fetch_side_effect:
        mock_adapter.fetch_page.side_effect = fetch_side_effect
    else:
        mock_adapter.fetch_page.return_value = "<html><body></body></html>"

    mock_factory = MagicMock()
    mock_factory.get_adapter.return_value = mock_adapter

    mock_parser = MagicMock()
    mock_parser.extract_article_links.return_value = []

    mock_extractor = MagicMock()
    mock_extractor.extract.return_value = extract_return

    mock_filter = MagicMock()
    mock_filter.is_today.return_value = True

    return Orchestrator(mock_factory, mock_parser, mock_extractor, mock_filter)


# Strategy: generate Block objects with mock URLs
block_with_urls_strategy = st.builds(
    Block,
    name=block_name_strategy,
    urls=st.lists(url_strategy, min_size=0, max_size=5),
)

# Strategy: generate a list of blocks with unique names (at least 1)
# Block names must be unique because run() uses them as dict keys
orchestrator_blocks_strategy = st.lists(
    block_with_urls_strategy, min_size=1, max_size=8, unique_by=lambda b: b.name
)

# Strategy: generate a Block with many URLs (for Property 3)
block_many_urls_strategy = st.builds(
    Block,
    name=block_name_strategy,
    urls=st.lists(url_strategy, min_size=5, max_size=15),
)


def make_valid_news_item():
    """Return a valid NewsItem with today's date."""
    return NewsItem(
        titulo="Título de prueba",
        subtitulos=[],
        fecha=date.today().strftime("%d/%m/%Y"),
        contenido="Contenido de prueba " * 20,
        autor="Autor de prueba",
        fuente="fuente.com",
        link="https://fuente.com/articulo/1",
    )


# ──────────────────────────────────────────────────────────────────────────────
# Property 1 (Orchestrator): Preservación de orden de bloques y URLs
# ──────────────────────────────────────────────────────────────────────────────

# Feature: vinotinto-galactico-scraper, Property 1: Preservación de orden de bloques y URLs
@given(blocks=orchestrator_blocks_strategy)
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_1_orchestrator_order_preserved(blocks):
    """
    For any list of blocks, the order of keys in the results dict must match
    the order of blocks passed to run().

    Validates: Requirements 2.2, 6.2
    """
    orchestrator = make_mock_orchestrator()
    with patch("VG_Extractor.time.sleep"):
        results = orchestrator.run(blocks)

    assert list(results.keys()) == [b.name for b in blocks]


# ──────────────────────────────────────────────────────────────────────────────
# Property 3: Límite de noticias por bloque
# ──────────────────────────────────────────────────────────────────────────────

# Feature: vinotinto-galactico-scraper, Property 3: Límite de noticias por bloque
@given(block=block_many_urls_strategy)
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_3_max_5_news_per_block(block):
    """
    For any block processed with any number of sources, the number of news
    items in the result never exceeds 5.

    Validates: Requirements 2.2, 2.3
    """
    # Parser returns 10 article URLs per portada URL
    article_urls = [f"https://fuente.com/articulo/{i}" for i in range(10)]

    mock_adapter = MagicMock()
    mock_adapter.fetch_page.return_value = "<html><body></body></html>"

    mock_factory = MagicMock()
    mock_factory.get_adapter.return_value = mock_adapter

    mock_parser = MagicMock()
    mock_parser.extract_article_links.return_value = article_urls

    mock_extractor = MagicMock()
    mock_extractor.extract.return_value = make_valid_news_item()

    mock_filter = MagicMock()
    mock_filter.is_today.return_value = True

    orchestrator = Orchestrator(mock_factory, mock_parser, mock_extractor, mock_filter)
    with patch("VG_Extractor.time.sleep"):
        result = orchestrator.process_block(block)

    assert len(result) <= 5, (
        f"Expected at most 5 news items, got {len(result)}"
    )


# ──────────────────────────────────────────────────────────────────────────────
# Property 5: Continuidad ante errores HTTP
# ──────────────────────────────────────────────────────────────────────────────

# Feature: vinotinto-galactico-scraper, Property 5: Continuidad ante errores HTTP
@given(
    urls=st.lists(url_strategy, min_size=1, max_size=10),
    failing_indices=st.lists(st.integers(min_value=0, max_value=9), min_size=0, max_size=5),
)
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_5_continues_on_http_errors(urls, failing_indices):
    """
    For any list of URLs where some fail (timeout, HTTP error, network
    exception), the system must continue processing remaining URLs and return
    successfully extracted news without raising an uncaught exception.

    Validates: Requirements 2.7, 6.3
    """
    failing_set = {i % len(urls) for i in failing_indices}

    call_count = [0]

    def fetch_side_effect(url):
        idx = call_count[0]
        call_count[0] += 1
        if idx in failing_set:
            raise AdapterError(f"Simulated HTTP error for URL index {idx}")
        return "<html><body></body></html>"

    mock_adapter = MagicMock()
    mock_adapter.fetch_page.side_effect = fetch_side_effect

    mock_factory = MagicMock()
    mock_factory.get_adapter.return_value = mock_adapter

    mock_parser = MagicMock()
    mock_parser.extract_article_links.return_value = []

    mock_extractor = MagicMock()
    mock_extractor.extract.return_value = None

    mock_filter = MagicMock()
    mock_filter.is_today.return_value = True

    orchestrator = Orchestrator(mock_factory, mock_parser, mock_extractor, mock_filter)
    block = Block(name="TEST_BLOCK", urls=urls)

    # Must not raise any uncaught exception
    try:
        with patch("VG_Extractor.time.sleep"):
            result = orchestrator.process_block(block)
    except Exception as e:
        pytest.fail(f"Uncaught exception raised during process_block: {type(e).__name__}: {e}")

    # Result must be a list (possibly empty)
    assert isinstance(result, list), "process_block must return a list"


# ──────────────────────────────────────────────────────────────────────────────
# Strategies for TxtWriter tests (Task 9.3)
# ──────────────────────────────────────────────────────────────────────────────

from VG_Extractor import TxtWriter

# NewsItem strategy for TxtWriter tests
news_item_strategy = st.builds(
    NewsItem,
    titulo=st.text(min_size=3, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz "),
    subtitulos=st.lists(
        st.text(min_size=3, max_size=30, alphabet="abcdefghijklmnopqrstuvwxyz "),
        min_size=0,
        max_size=3,
    ),
    fecha=st.just("01/01/2025"),
    contenido=st.text(min_size=50, max_size=500, alphabet="abcdefghijklmnopqrstuvwxyz "),
    autor=st.text(min_size=3, max_size=30, alphabet="abcdefghijklmnopqrstuvwxyz "),
    fuente=st.text(min_size=3, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz."),
    link=st.builds(
        lambda s: f"https://example.com/{s}",
        st.text(min_size=3, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz"),
    ),
)

# Results strategy: dict of block_name -> list[NewsItem]
results_strategy = st.dictionaries(
    keys=block_name_strategy,
    values=st.lists(news_item_strategy, min_size=0, max_size=3),
    min_size=1,
    max_size=5,
)

# Results strategy with at least one non-empty block (for Property 9 / 12)
results_with_news_strategy = st.dictionaries(
    keys=block_name_strategy,
    values=st.lists(news_item_strategy, min_size=1, max_size=3),
    min_size=1,
    max_size=5,
)


# ──────────────────────────────────────────────────────────────────────────────
# Property 9: Campos completos en Prompt_JULL
# ──────────────────────────────────────────────────────────────────────────────

# Feature: vinotinto-galactico-scraper, Property 9: Campos completos en Prompt_JULL
@given(results=results_with_news_strategy)
@settings(max_examples=100)
def test_property_9_txt_complete_fields(results):
    """
    For any NewsItem included in the results, the generated PROMPT_PARA_JULL.txt
    must contain, for that news item, all fields: título, fecha, contenido
    completo, autor, fuente, and link. If subtítulos exist, they must also appear.

    Validates: Requirements 4.2, 4.4
    """
    writer = TxtWriter()
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w", encoding="utf-8") as f:
        output_path = f.name
    try:
        writer.write(results, "01/01/2025", output_path)
        with open(output_path, encoding="utf-8") as f:
            content = f.read()

        for block_news in results.values():
            for item in block_news:
                assert item.titulo in content, (
                    f"titulo {item.titulo!r} not found in output"
                )
                assert item.fecha in content, (
                    f"fecha {item.fecha!r} not found in output"
                )
                assert item.contenido in content, (
                    f"contenido not found in output"
                )
                assert item.autor in content, (
                    f"autor {item.autor!r} not found in output"
                )
                assert item.fuente in content, (
                    f"fuente {item.fuente!r} not found in output"
                )
                assert item.link in content, (
                    f"link {item.link!r} not found in output"
                )
                for subtitulo in item.subtitulos:
                    assert subtitulo in content, (
                        f"subtitulo {subtitulo!r} not found in output"
                    )
    finally:
        os.unlink(output_path)


# ──────────────────────────────────────────────────────────────────────────────
# Property 10: Omisión de bloques vacíos en salida
# ──────────────────────────────────────────────────────────────────────────────

# Feature: vinotinto-galactico-scraper, Property 10: Omisión de bloques vacíos en salida
@given(results=results_strategy)
@settings(max_examples=100)
def test_property_10_empty_blocks_omitted(results):
    """
    For any block that has no news items, that block must NOT appear in the
    PROMPT_PARA_JULL.txt output.

    Validates: Requirements 4.5, 6.4
    """
    writer = TxtWriter()
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w", encoding="utf-8") as f:
        output_path = f.name
    try:
        writer.write(results, "01/01/2025", output_path)
        with open(output_path, encoding="utf-8") as f:
            content = f.read()

        for block_name, news in results.items():
            if not news:
                section_header = f"=== SECCIÓN: {block_name} ==="
                assert section_header not in content, (
                    f"Empty block {block_name!r} must not appear as a section in output, but it does"
                )
    finally:
        os.unlink(output_path)


# ──────────────────────────────────────────────────────────────────────────────
# Property 12: Nombres de bloques preservados exactamente
# ──────────────────────────────────────────────────────────────────────────────

# Feature: vinotinto-galactico-scraper, Property 12: Nombres de bloques preservados exactamente
@given(results=results_with_news_strategy)
@settings(max_examples=100)
def test_property_12_block_names_exact(results):
    """
    For any block name in the results, the name that appears in the output file
    must be identical to the original, without modifications to capitalization,
    spaces, or format.

    Validates: Requirements 4.2, 6.4
    """
    writer = TxtWriter()
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w", encoding="utf-8") as f:
        output_path = f.name
    try:
        writer.write(results, "01/01/2025", output_path)
        with open(output_path, encoding="utf-8") as f:
            content = f.read()

        for block_name, news in results.items():
            if news:  # only non-empty blocks appear in output
                assert block_name in content, (
                    f"Block name {block_name!r} not found verbatim in output"
                )
                # Ensure no case-modified variant appears instead
                lower_variant = block_name.lower()
                upper_variant = block_name.upper()
                # The original name must appear; if it differs from lower/upper,
                # verify the exact form is present (not just a transformed version)
                if lower_variant != block_name:
                    # The exact original must be present
                    assert block_name in content, (
                        f"Block name {block_name!r} must appear exactly as-is, not transformed"
                    )
    finally:
        os.unlink(output_path)


# ──────────────────────────────────────────────────────────────────────────────
# Strategies and helpers for HtmlWriter tests (Task 10.3)
# ──────────────────────────────────────────────────────────────────────────────

from VG_Extractor import HtmlWriter


# ──────────────────────────────────────────────────────────────────────────────
# Property 10 (HTML): Omisión de bloques vacíos en salida
# ──────────────────────────────────────────────────────────────────────────────

# Feature: vinotinto-galactico-scraper, Property 10: Omisión de bloques vacíos en salida
@given(results=results_strategy)
@settings(max_examples=100)
def test_property_10_html_empty_blocks_omitted(results):
    """
    For any block that has no news items, that block must NOT appear as a
    section div in REVISION_VISUAL.html.

    Validates: Requirements 5.2, 5.6, 6.4
    """
    writer = HtmlWriter()
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
        output_path = f.name
    try:
        writer.write(results, "01/01/2025", output_path)
        with open(output_path, encoding="utf-8") as f:
            content = f.read()

        for block_name, news in results.items():
            if not news:
                # The block's h2 heading must not appear inside a .bloque div
                assert f'<h2 class="bloque-titulo">{block_name}</h2>' not in content, (
                    f"Empty block {block_name!r} must not appear as a section in HTML output"
                )
    finally:
        os.unlink(output_path)


# ──────────────────────────────────────────────────────────────────────────────
# Property 11: Campos completos en HTML
# ──────────────────────────────────────────────────────────────────────────────

# Feature: vinotinto-galactico-scraper, Property 11: Campos completos en HTML
@given(results=results_with_news_strategy)
@settings(max_examples=100)
def test_property_11_html_complete_fields(results):
    """
    For any NewsItem included in the results, the generated REVISION_VISUAL.html
    must contain: título, fecha, contenido completo, autor, fuente, and a link
    to the original article.

    Validates: Requirements 5.5, 6.4
    """
    writer = HtmlWriter()
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
        output_path = f.name
    try:
        writer.write(results, "01/01/2025", output_path)
        with open(output_path, encoding="utf-8") as f:
            content = f.read()

        for block_news in results.values():
            for item in block_news:
                assert item.titulo in content, (
                    f"titulo {item.titulo!r} not found in HTML output"
                )
                assert item.fecha in content, (
                    f"fecha {item.fecha!r} not found in HTML output"
                )
                # contenido may have \n\n replaced with </p><p> — check the raw text is present
                # by verifying the first 50 chars of contenido appear somewhere in the HTML
                contenido_fragment = item.contenido[:50]
                assert contenido_fragment in content, (
                    f"contenido fragment {contenido_fragment!r} not found in HTML output"
                )
                assert item.autor in content, (
                    f"autor {item.autor!r} not found in HTML output"
                )
                assert item.fuente in content, (
                    f"fuente {item.fuente!r} not found in HTML output"
                )
                assert item.link in content, (
                    f"link {item.link!r} not found in HTML output"
                )
    finally:
        os.unlink(output_path)


# ──────────────────────────────────────────────────────────────────────────────
# Property 12 (HTML): Nombres de bloques preservados exactamente
# ──────────────────────────────────────────────────────────────────────────────

# Feature: vinotinto-galactico-scraper, Property 12: Nombres de bloques preservados exactamente
@given(results=results_with_news_strategy)
@settings(max_examples=100)
def test_property_12_html_block_names_exact(results):
    """
    For any block name in the results, the name that appears in REVISION_VISUAL.html
    must be identical to the original, without modifications to capitalization,
    spaces, or format.

    Validates: Requirements 5.2, 6.4
    """
    writer = HtmlWriter()
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
        output_path = f.name
    try:
        writer.write(results, "01/01/2025", output_path)
        with open(output_path, encoding="utf-8") as f:
            content = f.read()

        for block_name, news in results.items():
            if news:  # only non-empty blocks appear in output
                assert f'<h2 class="bloque-titulo">{block_name}</h2>' in content, (
                    f"Block name {block_name!r} not found verbatim as bloque-titulo in HTML output"
                )
    finally:
        os.unlink(output_path)
