"""
Tests unitarios para DateFilter.
Valida: Requisitos 2.4, 2.5
"""
from datetime import date, timedelta
from VG_Extractor import DateFilter


def test_date_filter_relative_today():
    """'hace 2 horas' se acepta como hoy."""
    df = DateFilter()
    assert df.is_today("hace 2 horas", date.today()) is True


def test_date_filter_hoy():
    """'hoy' se acepta como hoy."""
    df = DateFilter()
    assert df.is_today("hoy", date.today()) is True


def test_date_filter_today_english():
    """'today' se acepta como hoy."""
    df = DateFilter()
    assert df.is_today("today", date.today()) is True


def test_date_filter_yesterday():
    """La fecha de ayer en formato DD/MM/YYYY se rechaza."""
    df = DateFilter()
    yesterday = date.today() - timedelta(days=1)
    date_str = yesterday.strftime("%d/%m/%Y")
    assert df.is_today(date_str, date.today()) is False


def test_date_filter_iso_format_today():
    """La fecha de hoy en formato YYYY-MM-DD se acepta."""
    df = DateFilter()
    today_str = date.today().strftime("%Y-%m-%d")
    assert df.is_today(today_str, date.today()) is True


def test_date_filter_spanish_text_today():
    """'15 de enero de 2025' con reference_date=date(2025,1,15) se acepta."""
    df = DateFilter()
    assert df.is_today("15 de enero de 2025", date(2025, 1, 15)) is True


def test_date_filter_empty_string():
    """Cadena vacía retorna False."""
    df = DateFilter()
    assert df.is_today("", date.today()) is False


def test_date_filter_unknown_format():
    """Formato desconocido retorna False."""
    df = DateFilter()
    assert df.is_today("not a date", date.today()) is False
