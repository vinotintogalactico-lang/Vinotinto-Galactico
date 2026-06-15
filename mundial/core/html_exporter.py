from pathlib import Path
from datetime import date
import html as html_lib

OUTPUT_PATH = Path(__file__).parent.parent / "output" / "mundial_noticias.html"

CAT_ICONS = {
    "📺 TV / Canal":     "📺",
    "📰 Prensa Escrita": "📰",
    "💻 Digital":        "💻",
}


def export_html(noticias: list[dict], log: list[dict]) -> Path:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    def e(text: str) -> str:
        return html_lib.escape(str(text or ""))

    articles_html = ""
    for i, n in enumerate(noticias, 1):
        cat = n.get("categoria", "")
        icon = CAT_ICONS.get(cat, "⚽")
        body_html = "".join(
            f"<p>{e(p)}</p>"
            for p in n.get("body", "").split("\n\n")
            if p.strip()
        )
        articles_html += f"""
        <article>
            <div class="meta">
                <span class="num">#{i}</span>
                <span class="cat">{icon} {e(cat)}</span>
                <span class="src">{e(n.get('fuente',''))}</span>
            </div>
            <h2>{e(n.get('title',''))}</h2>
            {"<p class='subtitle'>" + e(n['subtitle']) + "</p>" if n.get('subtitle') else ""}
            <div class="byline">
                {"<span>✍ " + e(n['author']) + "</span>" if n.get('author') else ""}
                <span>📅 {e(n.get('date',''))}</span>
                <a href="{e(n.get('url',''))}" target="_blank">🔗 Ver original</a>
            </div>
            <div class="body">{body_html}</div>
        </article>"""

    log_rows = ""
    for entry in log:
        sc = "ok" if entry["estado"] == "Correcto" else (
            "warn" if "sin noticias" in entry["estado"].lower() else "err"
        )
        err_cell = (
            f"<td class='err-msg'>{e(entry.get('error',''))}</td>"
            if entry.get("error") else "<td></td>"
        )
        log_rows += f"""
        <tr class="{sc}">
            <td>{e(entry['fuente'])}</td>
            <td>{entry['encontradas']}</td>
            <td>{entry['extraidas']}</td>
            <td>{e(entry['estado'])}</td>
            {err_cell}
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mundial 2026 — {date.today().strftime('%d/%m/%Y')}</title>
<style>
  :root {{
    --bg: #0a0f0a; --card: #111811; --border: #1e2e1e;
    --accent: #1a6b1a; --accent2: #d4af37;
    --text: #e8e8e8; --muted: #888; --link: #d4af37;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--text); font-family: Georgia, serif; padding: 2rem; }}
  header {{ border-bottom: 3px solid var(--accent2); padding-bottom: 1rem; margin-bottom: 2rem; }}
  header h1 {{ font-size: 1.9rem; color: var(--accent2); letter-spacing: 2px; }}
  header p {{ color: var(--muted); font-size: .9rem; margin-top: .3rem; }}
  article {{
    background: var(--card); border: 1px solid var(--border);
    border-left: 4px solid var(--accent); border-radius: 4px;
    padding: 1.5rem; margin-bottom: 1.5rem;
  }}
  .meta {{ font-size: .75rem; color: var(--muted); margin-bottom: .6rem; display: flex; gap: .8rem; flex-wrap: wrap; }}
  .num {{ background: var(--accent); color: #fff; padding: .1rem .4rem; border-radius: 2px; }}
  .cat {{ color: var(--accent2); font-weight: bold; }}
  h2 {{ font-size: 1.25rem; color: #fff; margin-bottom: .5rem; line-height: 1.4; }}
  .subtitle {{ color: #bbb; font-style: italic; margin-bottom: .6rem; }}
  .byline {{ font-size: .8rem; color: var(--muted); display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1rem; }}
  .byline a {{ color: var(--link); text-decoration: none; }}
  .body p {{ line-height: 1.75; margin-bottom: .8rem; color: #d0d0d0; }}
  section.log {{ margin-top: 3rem; }}
  section.log h2 {{ font-size: 1.2rem; color: var(--accent2); margin-bottom: 1rem; }}
  table {{ width: 100%; border-collapse: collapse; font-size: .85rem; }}
  th {{ background: var(--accent); color: #fff; padding: .5rem .8rem; text-align: left; }}
  td {{ padding: .4rem .8rem; border-bottom: 1px solid var(--border); }}
  tr.ok td {{ color: #2ecc71; }} tr.warn td {{ color: #f39c12; }} tr.err td {{ color: #e74c3c; }}
  .err-msg {{ font-size: .78rem; color: #e74c3c !important; }}
</style>
</head>
<body>
<header>
  <h1>🌍 MUNDIAL 2026 — NOTICIAS EXTRAÍDAS</h1>
  <p>Fecha de extracción: {date.today().strftime('%d de %B de %Y')} · Total: {len(noticias)} noticias</p>
</header>
{articles_html}
<section class="log">
  <h2>📋 INFORME DE CONTROL</h2>
  <table>
    <thead><tr><th>Fuente</th><th>Encontradas</th><th>Extraídas</th><th>Estado</th><th>Error</th></tr></thead>
    <tbody>{log_rows}</tbody>
  </table>
</section>
</body>
</html>"""

    OUTPUT_PATH.write_text(html, encoding="utf-8")
    return OUTPUT_PATH
