"""
Exportador a TXT - Compatible con la estructura de noticias
"""
from datetime import datetime
from pathlib import Path


def export_txt(noticias: list, output_path: str):
    """
    Exporta noticias a TXT
    
    Args:
        noticias: Lista de dicts con keys: 'titulo', 'resumen', 'url', 'fuente', 'categoria', 'fecha'
        output_path: Ruta del archivo de salida
    """
    lines = []
    lines.append("=" * 80)
    lines.append("VINOTINTO GALÁCTICO - NOTICIAS EXTRAÍDAS")
    lines.append(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    lines.append("=" * 80)
    lines.append("")

    for idx, noticia in enumerate(noticias, 1):
        # Estructura flexible - acepta diferentes formatos
        titulo = noticia.get('titulo', noticia.get('title', 'Sin título'))
        resumen = noticia.get('resumen', noticia.get('summary', noticia.get('content', '')))
        url = noticia.get('url', '')
        fuente = noticia.get('fuente', noticia.get('source', 'Desconocida'))
        categoria = noticia.get('categoria', noticia.get('category', ''))
        fecha = noticia.get('fecha', noticia.get('date', ''))

        lines.append(f"NOTICIA #{idx}")
        lines.append("-" * 80)
        lines.append(f"TÍTULO: {titulo}")
        if categoria:
            lines.append(f"CATEGORÍA: {categoria}")
        lines.append(f"FUENTE: {fuente}")
        if fecha:
            lines.append(f"FECHA: {fecha}")
        lines.append(f"URL: {url}")
        lines.append("")
        lines.append("RESUMEN:")
        lines.append(resumen if resumen else "Sin resumen disponible")
        lines.append("")
        lines.append("=" * 80)
        lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return len(noticias)