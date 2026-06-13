"""
Exportador a HTML - Compatible con estructura flexible
"""
from datetime import datetime
from pathlib import Path


def export_html(noticias: list, output_path: str):
    """
    Exporta noticias a HTML
    
    Args:
        noticias: Lista de dicts con noticias
        output_path: Ruta del archivo de salida
    """
    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vinotinto Galáctico - Noticias</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0d0d0d;
            color: #e0e0e0;
            margin: 0;
            padding: 2rem;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            background: linear-gradient(135deg, #1a0810, #0d0d0d);
            border-bottom: 3px solid #c0392b;
            padding: 2rem;
            text-align: center;
            margin-bottom: 2rem;
            border-radius: 8px;
        }}
        .header h1 {{
            font-size: 2.5rem;
            margin: 0;
            color: #fff;
        }}
        .news-item {{
            background: #1a1a1a;
            border-left: 4px solid #c0392b;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            border-radius: 4px;
        }}
        .news-meta {{
            font-size: 0.85rem;
            color: #888;
            margin-bottom: 0.5rem;
        }}
        .news-cat {{
            color: #c0392b;
            font-weight: 600;
        }}
        .news-title {{
            font-size: 1.3rem;
            color: #fff;
            margin: 0.5rem 0;
        }}
        .news-body {{
            color: #c8c8c8;
            line-height: 1.6;
        }}
        .news-url {{
            color: #3498db;
            text-decoration: none;
            font-size: 0.9rem;
        }}
        .news-url:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔴 VINOTINTO GALÁCTICO</h1>
            <p>Noticias extraídas - {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        </div>
"""

    for idx, noticia in enumerate(noticias, 1):
        # Estructura flexible - usar .get() para evitar KeyError
        titulo = noticia.get('titulo', noticia.get('title', 'Sin título'))
        resumen = noticia.get('resumen', noticia.get('summary', noticia.get('content', '')))
        url = noticia.get('url', '')
        fuente = noticia.get('fuente', noticia.get('source', 'Desconocida'))
        categoria = noticia.get('categoria', noticia.get('category', ''))
        fecha = noticia.get('fecha', noticia.get('date', ''))
        
        # Verificar si existe 'estado' antes de usarlo
        estado = noticia.get('estado', 'Correcto')

        html_content += f"""
        <div class="news-item">
            <div class="news-meta">
                <span class="news-cat">{categoria}</span> · 
                <span>{fuente}</span> · 
                <span>{fecha if fecha else 'Fecha no disponible'}</span>
            </div>
            <h2 class="news-title">{titulo}</h2>
            <div class="news-body">{resumen}</div>
            <a href="{url}" class="news-url" target="_blank">Ver noticia original →</a>
        </div>
"""

    html_content += """
    </div>
</body>
</html>
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return len(noticias)