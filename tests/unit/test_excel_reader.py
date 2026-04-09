"""
Unit tests for ExcelReader (Task 2.1)
Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5
"""
import os
import pytest
import pandas as pd
from openpyxl import Workbook

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from VG_Extractor import ExcelReader, Block, ExcelReadError


def make_excel(tmp_path, rows: list) -> str:
    """Helper: write a list of row values to a single-column xlsx and return the path."""
    wb = Workbook()
    ws = wb.active
    for value in rows:
        ws.append([value])
    path = str(tmp_path / "test.xlsx")
    wb.save(path)
    return path


# ── Requirement 1.2 ──────────────────────────────────────────────────────────

def test_excel_reader_file_not_found():
    """ExcelReadError is raised when the file does not exist."""
    reader = ExcelReader("/nonexistent/path/file.xlsx")
    with pytest.raises(ExcelReadError):
        reader.read()


# ── Requirements 1.1, 1.3, 1.4 ───────────────────────────────────────────────

def test_excel_reader_basic_structure(tmp_path):
    """Blocks and URLs are parsed correctly from a well-formed Excel."""
    path = make_excel(tmp_path, [
        "REAL MADRID:",
        "https://www.as.com/real_madrid/",
        "https://www.marca.com/futbol/real-madrid/",
        "LALIGA:",
        "https://www.laliga.com/noticias",
    ])
    blocks = ExcelReader(path).read()

    assert len(blocks) == 2
    assert blocks[0].name == "REAL MADRID"
    assert blocks[0].urls == [
        "https://www.as.com/real_madrid/",
        "https://www.marca.com/futbol/real-madrid/",
    ]
    assert blocks[1].name == "LALIGA"
    assert blocks[1].urls == ["https://www.laliga.com/noticias"]


def test_excel_reader_preserves_block_order(tmp_path):
    """Block order matches the Excel order exactly (Requirement 1.3)."""
    names = ["VINOTINTO", "REAL MADRID", "LALIGA"]
    rows = []
    for name in names:
        rows.append(f"{name}:")
        rows.append(f"https://example.com/{name.lower().replace(' ', '-')}")
    path = make_excel(tmp_path, rows)

    blocks = ExcelReader(path).read()
    assert [b.name for b in blocks] == names


def test_excel_reader_preserves_url_order_within_block(tmp_path):
    """URL order within a block matches the Excel order exactly (Requirement 1.4)."""
    urls = [
        "https://first.com/",
        "https://second.com/",
        "https://third.com/",
    ]
    rows = ["BLOQUE:"] + urls
    path = make_excel(tmp_path, rows)

    blocks = ExcelReader(path).read()
    assert blocks[0].urls == urls


# ── Requirement 1.5 ───────────────────────────────────────────────────────────

def test_excel_reader_ignores_empty_rows(tmp_path):
    """Empty rows between entries are ignored (Requirement 1.5)."""
    path = make_excel(tmp_path, [
        None,
        "BLOQUE:",
        None,
        "https://example.com/",
        None,
    ])
    blocks = ExcelReader(path).read()

    assert len(blocks) == 1
    assert blocks[0].name == "BLOQUE"
    assert blocks[0].urls == ["https://example.com/"]


def test_excel_reader_ignores_nan_string(tmp_path):
    """Rows containing the literal string 'nan' are ignored (Requirement 1.5)."""
    # pandas converts empty cells to NaN; str(NaN) == 'nan'
    path = make_excel(tmp_path, [
        "BLOQUE:",
        "https://example.com/",
    ])
    # Manually inject a NaN row by reading and re-saving with pandas
    df = pd.read_excel(path, header=None)
    # Insert a NaN row at position 1
    top = df.iloc[:1]
    nan_row = pd.DataFrame([[float('nan')]])
    bottom = df.iloc[1:]
    df2 = pd.concat([top, nan_row, bottom], ignore_index=True)
    df2.to_excel(path, index=False, header=False)

    blocks = ExcelReader(path).read()
    assert len(blocks) == 1
    assert blocks[0].urls == ["https://example.com/"]


def test_excel_reader_empty_file_returns_empty_list(tmp_path):
    """An Excel with no meaningful rows returns an empty list."""
    path = make_excel(tmp_path, [None, None])
    blocks = ExcelReader(path).read()
    assert blocks == []


def test_excel_reader_block_name_exact(tmp_path):
    """Block name is stored without the trailing colon and without modification."""
    path = make_excel(tmp_path, ["SELECCIÓN ESPAÑOLA FEMENINO:"])
    blocks = ExcelReader(path).read()
    assert blocks[0].name == "SELECCIÓN ESPAÑOLA FEMENINO"


def test_excel_reader_urls_before_any_block_are_ignored(tmp_path):
    """URLs that appear before the first block header are silently ignored."""
    path = make_excel(tmp_path, [
        "https://orphan-url.com/",
        "BLOQUE:",
        "https://valid.com/",
    ])
    blocks = ExcelReader(path).read()
    assert len(blocks) == 1
    assert blocks[0].urls == ["https://valid.com/"]
