from pathlib import Path
from datetime import date

OUTPUT_PATH = Path(__file__).parent.parent / "output" / "mundial_noticias.txt"


def export_txt(noticias: list[dict], log: list[dict]) -> Path:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = []

    lines.append("=" * 80)
    lines.append("MUNDIAL 2026 — EXTRACCIÓN DE NOTICIAS")
    lines.append(f"Fecha: {date.today().strftime('%d/%m/%Y')}")
    lines.append(f"Total noticias: {len(noticias)}")
    lines.append("=" * 80)
    lines.append("")

    for i, n in enumerate(noticias, 1):
        lines.append("─" * 80)
        lines.append(f"NOTICIA #{i}")
        lines.append(f"FUENTE:    {n.get('fuente', '')}")
        lines.append(f"CATEGORÍA: {n.get('categoria', '')}")
        lines.append(f"TÍTULO:    {n.get('title', '')}")
        if n.get("subtitle"):
            lines.append(f"SUBTÍTULO: {n['subtitle']}")
        if n.get("author"):
            lines.append(f"AUTOR:     {n['author']}")
        lines.append(f"FECHA:     {n.get('date', '')}")
        lines.append(f"URL:       {n.get('url', '')}")
        lines.append("")
        lines.append(n.get("body", ""))
        lines.append("")

    lines.append("=" * 80)
    lines.append("INFORME DE CONTROL")
    lines.append("=" * 80)
    for entry in log:
        lines.append(f"Fuente: {entry['fuente']}")
        lines.append(
            f"  Encontradas: {entry['encontradas']}  |  "
            f"Extraídas: {entry['extraidas']}  |  "
            f"Estado: {entry['estado']}"
        )
        if entry.get("error"):
            lines.append(f"  Error: {entry['error']}")
        lines.append("")

    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    return OUTPUT_PATH
