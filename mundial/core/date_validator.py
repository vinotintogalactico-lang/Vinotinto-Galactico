from datetime import date, datetime
import re

# Meses en español para parseo manual
_MESES_ES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
    "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
    "jul": 7, "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12,
}

_MESES_EN = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

from zoneinfo import ZoneInfo
VNZ_TZ = ZoneInfo("America/Caracas")

def is_today(date_str: str) -> tuple[bool, str]:
    """
    Validación de fecha ESTRICTA: Ayer, Hoy o Mañana.
    Aceptamos ayer por desfase horario España/Venezuela,
    y mañana porque a esta hora (casi media noche) ya es mañana en España.
    """
    if not date_str:
        return False, "Fecha vacía (Rechazada)"

    today = datetime.now(VNZ_TZ).date()
    from datetime import timedelta
    yesterday = today - timedelta(days=1)
    tomorrow  = today + timedelta(days=1)
    
    parsed = _parse_date(date_str.strip(), today)

    if parsed is None:
        return False, f"No se pudo parsear: '{date_str}' (Rechazada)"

    if parsed in (yesterday, today, tomorrow):
        delta_str = {today: "Hoy", tomorrow: "Mañana", yesterday: "Ayer"}[parsed]
        return True, f"Aceptado: {parsed} ({delta_str})"
    else:
        return False, f"Rechazado: {parsed} — no es de Ayer, Hoy ni Mañana (ref: {today})"


def _parse_date(text: str, today: date) -> date | None:
    """Intenta parsear una cadena de fecha en varios formatos."""
    text = text.strip()

    # 1. Formatos ISO directos (los más fiables, vienen de atributos datetime o meta tags)
    for fmt in (
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            dt = datetime.strptime(text[:19], fmt)
            return dt.date()
        except (ValueError, TypeError):
            pass

    # 2. Formatos numéricos europeos
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d/%m/%Y %H:%M", "%d-%m-%Y %H:%M"):
        try:
            dt = datetime.strptime(text[:16], fmt)
            return dt.date()
        except (ValueError, TypeError):
            pass

    # 3. "hace X minutos/horas/segundos" → hoy
    if re.search(r"hace\s+\d+\s+(minuto|hora|segundo)", text, re.I):
        return today
    if re.search(r"\d+\s*(min|hour|ago|h ago|m ago)", text, re.I):
        return today
    if re.search(r"just now|ahora mismo|hace un momento|ahora", text, re.I):
        return today

    # 4. Texto con mes en español/inglés: "7 de junio de 2025" o "7 junio 2025"
    text_lower = text.lower()
    m = re.search(r"(\d{1,2})\s+(?:de\s+)?([a-záéíóú]+)\.?\s+(?:de\s+)?(\d{4})", text_lower)
    if m:
        day, month_str, year = int(m.group(1)), m.group(2), int(m.group(3))
        month = _MESES_ES.get(month_str) or _MESES_EN.get(month_str)
        if month:
            try:
                return date(year, month, day)
            except ValueError:
                pass

    # 5. "June 7, 2025"
    m = re.search(r"([a-z]+)\s+(\d{1,2}),?\s+(\d{4})", text_lower)
    if m:
        month_str, day, year = m.group(1), int(m.group(2)), int(m.group(3))
        month = _MESES_EN.get(month_str) or _MESES_ES.get(month_str)
        if month:
            try:
                return date(year, month, day)
            except ValueError:
                pass

    # Extra: Unix Timestamps (ej. Marca: 1781088275)
    if text.isdigit() and len(text) >= 10:
        try:
            return date.fromtimestamp(int(text))
        except Exception:
            pass

    # 6. Último recurso: dateutil
    if re.search(r"\b(20\d{2})\b", text):
        try:
            from dateutil import parser
            dt = parser.parse(text, fuzzy=True, dayfirst=True).date()
            from datetime import timedelta
            manana = today + timedelta(days=1)
            if dt == today or dt == manana:
                return dt
            else:
                return None
        except Exception:
            pass

    return None
