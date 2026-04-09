"""
Unit tests for TxtWriter class.
Covers: test_txt_writer_includes_jull_instructions, test_txt_writer_no_temporal_closings
"""
import os
import tempfile
import pytest
from VG_Extractor import TxtWriter, NewsItem


def make_news_item(**kwargs):
    defaults = dict(
        titulo="Título de prueba",
        subtitulos=[],
        fecha="01/01/2025",
        contenido="Contenido de la noticia de prueba con suficiente texto para ser válida.",
        autor="Autor Prueba",
        fuente="fuente.com",
        link="https://fuente.com/noticia-1",
    )
    defaults.update(kwargs)
    return NewsItem(**defaults)


@pytest.fixture
def writer():
    return TxtWriter()


@pytest.fixture
def tmp_output(tmp_path):
    return str(tmp_path / "PROMPT_PARA_JULL.txt")


def read_output(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


# ── Header ──────────────────────────────────────────────────────────────────

def test_header_contains_fecha(writer, tmp_output):
    writer.write({}, "15/07/2025", tmp_output)
    content = read_output(tmp_output)
    assert "FECHA: 15/07/2025" in content


def test_header_contains_protocol_title(writer, tmp_output):
    writer.write({}, "01/01/2025", tmp_output)
    content = read_output(tmp_output)
    assert "PROTOCOLO VINOTINTO GALÁCTICO" in content


# ── News fields ──────────────────────────────────────────────────────────────

def test_noticia_titulo_present(writer, tmp_output):
    results = {"REAL MADRID": [make_news_item(titulo="Gran victoria del Madrid")]}
    writer.write(results, "01/01/2025", tmp_output)
    content = read_output(tmp_output)
    assert "TITULO: Gran victoria del Madrid" in content


def test_noticia_fecha_present(writer, tmp_output):
    results = {"REAL MADRID": [make_news_item(fecha="25/12/2024")]}
    writer.write(results, "01/01/2025", tmp_output)
    content = read_output(tmp_output)
    assert "FECHA: 25/12/2024" in content


def test_noticia_contenido_present(writer, tmp_output):
    results = {"REAL MADRID": [make_news_item(contenido="Texto completo del artículo sin truncar.")]}
    writer.write(results, "01/01/2025", tmp_output)
    content = read_output(tmp_output)
    assert "Texto completo del artículo sin truncar." in content


def test_noticia_autor_present(writer, tmp_output):
    results = {"REAL MADRID": [make_news_item(autor="Juan Pérez")]}
    writer.write(results, "01/01/2025", tmp_output)
    content = read_output(tmp_output)
    assert "AUTOR: Juan Pérez" in content


def test_noticia_fuente_present(writer, tmp_output):
    results = {"REAL MADRID": [make_news_item(fuente="marca.com")]}
    writer.write(results, "01/01/2025", tmp_output)
    content = read_output(tmp_output)
    assert "FUENTE: marca.com" in content


def test_noticia_link_present(writer, tmp_output):
    results = {"REAL MADRID": [make_news_item(link="https://marca.com/noticia-1")]}
    writer.write(results, "01/01/2025", tmp_output)
    content = read_output(tmp_output)
    assert "LINK: https://marca.com/noticia-1" in content


def test_noticia_subtitulos_present_when_exist(writer, tmp_output):
    results = {"REAL MADRID": [make_news_item(subtitulos=["Sub 1", "Sub 2"])]}
    writer.write(results, "01/01/2025", tmp_output)
    content = read_output(tmp_output)
    assert "SUBTITULOS: Sub 1 | Sub 2" in content


def test_noticia_subtitulos_omitted_when_empty(writer, tmp_output):
    results = {"REAL MADRID": [make_news_item(subtitulos=[])]}
    writer.write(results, "01/01/2025", tmp_output)
    content = read_output(tmp_output)
    assert "SUBTITULOS:" not in content


def test_noticia_numbering(writer, tmp_output):
    results = {"BLOQUE": [make_news_item(), make_news_item(), make_news_item()]}
    writer.write(results, "01/01/2025", tmp_output)
    content = read_output(tmp_output)
    assert "NOTICIA 1:" in content
    assert "NOTICIA 2:" in content
    assert "NOTICIA 3:" in content


# ── Empty blocks ─────────────────────────────────────────────────────────────

def test_empty_block_omitted(writer, tmp_output):
    results = {"REAL MADRID": [], "VINOTINTO": [make_news_item()]}
    writer.write(results, "01/01/2025", tmp_output)
    content = read_output(tmp_output)
    assert "REAL MADRID" not in content
    assert "VINOTINTO" in content


def test_all_empty_blocks_produces_no_sections(writer, tmp_output):
    results = {"BLOQUE A": [], "BLOQUE B": []}
    writer.write(results, "01/01/2025", tmp_output)
    content = read_output(tmp_output)
    assert "SECCIÓN:" not in content


# ── JULL instructions ────────────────────────────────────────────────────────

def test_txt_writer_includes_jull_instructions(writer, tmp_output):
    writer.write({}, "01/01/2025", tmp_output)
    content = read_output(tmp_output)
    assert "INSTRUCCIONES PARA JULL" in content


def test_txt_writer_includes_noticiero_largo(writer, tmp_output):
    writer.write({}, "01/01/2025", tmp_output)
    content = read_output(tmp_output)
    assert "NOTICIERO LARGO" in content


def test_txt_writer_includes_shorts(writer, tmp_output):
    writer.write({}, "01/01/2025", tmp_output)
    content = read_output(tmp_output)
    assert "4 SHORTS" in content


def test_txt_writer_no_temporal_closings(writer, tmp_output):
    """Instructions must explicitly prohibit temporal closings like 'mañana' or 'hoy'."""
    writer.write({}, "01/01/2025", tmp_output)
    content = read_output(tmp_output)
    assert "mañana" in content.lower()  # the prohibition text mentions the word
    assert "hoy" in content.lower()     # the prohibition text mentions the word
    assert "PROHIBICIONES" in content


def test_jull_instructions_at_end(writer, tmp_output):
    results = {"BLOQUE": [make_news_item()]}
    writer.write(results, "01/01/2025", tmp_output)
    content = read_output(tmp_output)
    # JULL instructions should appear after the news content
    news_pos = content.index("NOTICIA 1:")
    jull_pos = content.index("INSTRUCCIONES PARA JULL")
    assert jull_pos > news_pos


# ── File encoding ────────────────────────────────────────────────────────────

def test_output_file_is_utf8(writer, tmp_output):
    results = {"VINOTINTO": [make_news_item(titulo="Vinotinto campeón")]}
    writer.write(results, "01/01/2025", tmp_output)
    # If file is not UTF-8 this will raise UnicodeDecodeError
    with open(tmp_output, encoding="utf-8") as f:
        content = f.read()
    assert "Vinotinto campeón" in content
