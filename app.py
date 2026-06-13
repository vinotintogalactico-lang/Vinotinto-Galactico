import asyncio
import logging
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import streamlit as st

from core.excel_reader import load_sources
from core.txt_exporter import export_txt
from core.html_exporter import export_html
from extractores.factory import get_extractor

logging.basicConfig(level=logging.INFO)

CATEGORY_ICONS = {
    "Real Madrid Masculino":      "👑",
    "Real Madrid Femenino":       "👑",
    "LaLiga":                     "🇪🇸",
    "Selección Española Masculina": "🇪🇸",
    "Selección Española Femenina":  "🇪🇸",
    "Vinotinto Masculina":        "🇻🇪",
    "Vinotinto Femenina":         "🇻🇪",
    "Liga FUTVE":                 "🇻🇪",
}

st.set_page_config(page_title="Vinotinto Galáctico · Extractor", page_icon="⚽", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;600&display=swap');
.vg-header {
    background: linear-gradient(135deg, #0d0d0d 0%, #1a0810 50%, #0d0d0d 100%);
    border-bottom: 3px solid #c0392b;
    padding: 1.5rem 2rem;
    margin: -1rem -1rem 2rem -1rem;
    display: flex; align-items: center; gap: 1.2rem;
}
.vg-header h1 {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.4rem; color: #fff; letter-spacing: 3px; margin: 0;
}
.vg-header .date-badge {
    background: #7a1a2e; color: #fff; font-size: .75rem;
    padding: .2rem .7rem; border-radius: 20px; letter-spacing: 1px; margin-top: .2rem;
}
.cat-label {
    font-family: 'Bebas Neue', sans-serif; font-size: 1rem;
    letter-spacing: 2px; color: #c0392b;
    padding: .3rem 0 .1rem 0; border-bottom: 1px solid #2a2a2a;
    margin-top: .8rem; margin-bottom: .3rem;
}
div[data-testid="stButton"] button {
    background: linear-gradient(135deg, #7a1a2e, #c0392b) !important;
    color: white !important; border: none !important;
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 1.1rem !important; letter-spacing: 2px !important;
    padding: .6rem 2rem !important; border-radius: 4px !important;
    width: 100% !important;
}
.news-card {
    background: #161616; border: 1px solid #2a2a2a;
    border-left: 4px solid #7a1a2e; border-radius: 4px;
    padding: 1.2rem 1.5rem; margin-bottom: 1.2rem;
}
.news-card .nc-meta { font-size: .72rem; color: #888; margin-bottom: .4rem; display: flex; gap: .8rem; flex-wrap: wrap; }
.news-card .nc-cat { color: #c0392b; font-weight: 600; }
.news-card h3 { font-size: 1.05rem; color: #eee; margin: .3rem 0; }
.news-card .nc-subtitle { color: #aaa; font-size: .9rem; font-style: italic; margin-bottom: .5rem; }
.news-card .nc-byline { font-size: .78rem; color: #666; margin-bottom: .8rem; }
.news-card .nc-body { font-size: .88rem; color: #c8c8c8; line-height: 1.7; }
</style>
""", unsafe_allow_html=True)

import base64
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

try:
    logo_b64 = get_base64_of_bin_file("Logo.jpg")
    logo_html = f'<img src="data:image/jpeg;base64,{logo_b64}" width="80" style="border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.5);">'
except Exception:
    logo_html = '<div style="font-size: 3rem;">⚽</div>'

st.markdown(f"""
<div class="vg-header">
    <div>{logo_html}</div>
    <div>
        <h1>VINOTINTO GALÁCTICO · NEWS EXTRACTOR</h1>
        <div class="date-badge">HOY: {date.today().strftime('%d / %m / %Y')}</div>
    </div>
</div>
""", unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def _load_sources():
    return load_sources()

try:
    sources = _load_sources()
    excel_ok = True
except Exception as exc:
    sources = {}
    excel_ok = False
    excel_error = str(exc)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    import os
    if os.path.exists("Logo.jpg"):
        st.image("Logo.jpg", use_container_width=True)
    
    st.markdown("## 📰 Fuentes")

    if not excel_ok:
        st.error(f"❌ Error al leer el Excel:\n\n{excel_error}")
        st.stop()

    selected: dict[str, list[dict]] = {}

    for cat, fuentes in sources.items():
        icon = CATEGORY_ICONS.get(cat, "📌")
        st.markdown(f'<div class="cat-label">{icon} {cat}</div>', unsafe_allow_html=True)

        cat_key = cat.replace(" ", "_")
        todo_key = f"todo_{cat_key}"
        
        # Identificamos cada checkbox de las fuentes
        fuentes_keys = []
        for idx, f in enumerate(fuentes):
            url_slug = urlparse(f["url"]).netloc.replace(".", "_")
            path_slug = urlparse(f["url"]).path.strip("/").replace("/", "_")
            chk_key = f"chk_{cat_key}_{url_slug}_{path_slug}_{idx}"
            fuentes_keys.append((f, chk_key))

        # Función que se dispara al tocar "Seleccionar todo"
        def toggle_all(tk=todo_key, fk=[k for _, k in fuentes_keys]):
            val = st.session_state[tk]
            for key in fk:
                st.session_state[key] = val

        # 1. Dibujamos las fuentes primero
        for f, k in fuentes_keys:
            if st.checkbox(f["nombre"], key=k):
                selected.setdefault(cat, []).append(f)

        # 2. Dibujamos "Seleccionar todo" AL FINAL
        st.checkbox("🔳 Seleccionar todo", key=todo_key, on_change=toggle_all)

    st.markdown("---")
    total_sel = sum(len(v) for v in selected.values())
    st.caption(f"**{total_sel}** fuente(s) seleccionada(s)")
    run = st.button("⚡ EXTRAER NOTICIAS", disabled=total_sel == 0)

# ── Extracción ────────────────────────────────────────────────────────────────
if "resultado" not in st.session_state:
    st.session_state.resultado = None

if run:
    st.session_state.resultado = None
    all_noticias: list[dict] = []
    all_log: list[dict] = []

    progress = st.progress(0, text="Iniciando extracción…")
    status_box = st.empty()

    flat_sources = [(cat, f) for cat, fuentes in selected.items() for f in fuentes]
    total = len(flat_sources)

    async def run_all():
        for i, (cat, f) in enumerate(flat_sources):
            status_box.info(f"🔍 Procesando: **{f['nombre']}** — {cat}")
            extractor = get_extractor(f["nombre"], f["url"], cat)
            noticias, log = await extractor.extract()
            all_noticias.extend(noticias)
            all_log.append(log)
            progress.progress((i + 1) / total, text=f"{i+1}/{total} fuentes procesadas")

    asyncio.run(run_all())
    progress.empty()
    status_box.empty()

    txt_path = export_txt(all_noticias, all_log)
    html_path = export_html(all_noticias, all_log)

    st.session_state.resultado = {
        "noticias": all_noticias,
        "log": all_log,
        "txt_path": txt_path,
        "html_path": html_path,
    }

# ── Resultados ────────────────────────────────────────────────────────────────
if st.session_state.resultado:
    res = st.session_state.resultado
    noticias = res["noticias"]
    log = res["log"]
    txt_path: Path = res["txt_path"]
    html_path: Path = res["html_path"]

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("📰 Noticias extraídas", len(noticias))
    k2.metric("✅ Fuentes con noticias", sum(1 for l in log if l["estado"] == "Correcto"))
    k3.metric("🕳️ Sin noticias hoy", sum(1 for l in log if "sin noticias" in l["estado"].lower()))
    k4.metric("❌ Errores", sum(1 for l in log if l["estado"] == "Error"))

    st.markdown("---")

    col1, col2 = st.columns(2)
    if txt_path.exists():
        col1.download_button("📥 Descargar noticias.txt", data=txt_path.read_bytes(),
                             file_name="noticias.txt", mime="text/plain")
    if html_path.exists():
        col2.download_button("🌐 Descargar noticias.html", data=html_path.read_bytes(),
                             file_name="noticias.html", mime="text/html")

    st.markdown("---")
    tab_news, tab_log = st.tabs([f"📰 Noticias ({len(noticias)})", "📋 Informe de control"])

    with tab_news:
        if not noticias:
            st.warning("No se encontraron noticias del día en las fuentes seleccionadas.")
        else:
            cats_disp = sorted({n["categoria"] for n in noticias})
            cat_filter = st.multiselect("Filtrar por categoría", cats_disp, default=cats_disp)
            for n in [x for x in noticias if x["categoria"] in cat_filter]:
                body_preview = n.get("body", "")[:400]
                if len(n.get("body", "")) > 400:
                    body_preview += "…"
                
                subtitle_html = f"<div class='nc-subtitle'>{n['subtitle']}</div>" if n.get('subtitle') else ""
                author_html = f"<div class='nc-byline'>✍ {n['author']}</div>" if n.get('author') else ""
                
                html_str = f"<div class='news-card'><div class='nc-meta'><span class='nc-cat'>{n.get('categoria','')}</span><span>{n.get('fuente','')}</span><span>{n.get('date','')}</span><a href='{n.get('url','')}' target='_blank' style='color:#e74c3c'>🔗 Ver original</a></div><h3>{n.get('title','')}</h3>{subtitle_html}{author_html}<div class='nc-body'>{body_preview}</div></div>"
                st.markdown(html_str, unsafe_allow_html=True)

    with tab_log:
        for entry in log:
            icon = "✅" if entry["estado"] == "Correcto" else ("⚠️" if "sin" in entry["estado"].lower() else "❌")
            err = f" — `{entry['error']}`" if entry.get("error") else ""
            st.markdown(f"{icon} **{entry['fuente']}** · Encontradas: `{entry['encontradas']}` · Extraídas: `{entry['extraidas']}` · {entry['estado']}{err}")
else:
    st.markdown("""
    <div style="text-align:center; padding: 4rem 0; color: #555;">
        <div style="font-size: 4rem;">⚽</div>
        <div style="font-family:'Bebas Neue',sans-serif; font-size:1.6rem; letter-spacing:3px; color:#7a1a2e; margin-top:.5rem;">
            SELECCIONA LAS FUENTES Y PULSA EXTRAER
        </div>
        <div style="font-size:.9rem; margin-top:.5rem; color:#666;">
            Solo se extraerán noticias del día de hoy · Máximo 3 por fuente
        </div>
    </div>
    """, unsafe_allow_html=True)