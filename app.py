import os
import time

os.environ['TZ'] = 'America/Caracas'
if hasattr(time, 'tzset'):
    time.tzset()

import asyncio
import base64
import logging
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import streamlit as st

@st.cache_resource(show_spinner=False)
def _install_playwright():
    try:
        os.system(f"{sys.executable} -m playwright install chromium")
    except Exception as e:
        print(f"Error instalando playwright: {e}")

_install_playwright()
Path("output").mkdir(exist_ok=True)

logging.basicConfig(level=logging.INFO)

st.set_page_config(page_title="VG · Extractor de Noticias", page_icon="⚽", layout="wide")

# ═══════════════════════════════════════════════════════════════
# CSS GLOBAL
# ═══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;600&display=swap');

/* ── OCULTAR navegación multi-página de Streamlit ── */
[data-testid="stSidebarNav"] { display: none !important; }
section[data-testid="stSidebar"] > div:first-child { padding-top: 0.5rem; }

/* ── SELECTOR DE MODO (los dos botones grandes) ── */
.modo-wrap {
    display: flex; gap: 1rem; margin: 0.5rem 0 1.2rem 0;
}
.modo-btn {
    flex: 1; padding: 0.9rem 1rem; border: none; border-radius: 8px;
    font-family: 'Bebas Neue', sans-serif; font-size: 1.4rem;
    letter-spacing: 3px; cursor: pointer; transition: all 0.2s ease;
    box-shadow: 0 4px 15px rgba(0,0,0,0.4);
}
.modo-vg {
    background: linear-gradient(135deg, #7a1a2e, #c0392b);
    color: white;
}
.modo-mundial {
    background: linear-gradient(135deg, #0d2b0d, #1a6b1a);
    color: white;
}
.modo-btn:hover { transform: translateY(-2px); filter: brightness(1.15); }
.modo-btn.activo { outline: 3px solid white; filter: brightness(1.2); }

/* ── BANNER ── */
.vg-banner-wrap {
    margin: -1rem -1rem 0 -1rem; overflow: hidden;
    position: relative; background: #0d0d0d;
}
.vg-banner-wrap img {
    width: 100%; display: block;
    object-fit: contain; object-position: center top;
    max-height: 180px;
}
.vg-banner-wrap::after {
    content: ''; position: absolute; bottom: 0; left: 0; right: 0;
    height: 40px; background: linear-gradient(to bottom, transparent, #0d0d0d);
}

/* ── CATEGORÍAS SIDEBAR ── */
.cat-label {
    font-family: 'Bebas Neue', sans-serif; font-size: 1rem;
    letter-spacing: 2px; padding: .3rem 0 .1rem 0;
    border-bottom: 1px solid #2a2a2a;
    margin-top: .8rem; margin-bottom: .3rem;
}
.cat-vg   { color: #c0392b; }
.cat-mun  { color: #d4af37; }

/* ── BOTÓN EXTRAER ── */
div[data-testid="stButton"] button {
    color: white !important; border: none !important;
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 1.2rem !important; letter-spacing: 3px !important;
    padding: .75rem 1.5rem !important; border-radius: 6px !important;
    width: 100% !important; transition: all 0.2s ease !important;
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════
def _b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

try:
    banner_b64  = _b64("banner-vinotinto.png")
    banner_html = f'<img src="data:image/png;base64,{banner_b64}" alt="Vinotinto Galáctico">'
except Exception:
    banner_html = ""

try:
    logo_b64 = _b64("Logo.jpg")
    logo_src = f"data:image/jpeg;base64,{logo_b64}"
except Exception:
    logo_src = ""

# ═══════════════════════════════════════════════════════════════
# ESTADO DEL MODO  (vg | mundial)
# ═══════════════════════════════════════════════════════════════
if "modo" not in st.session_state:
    st.session_state.modo = "vg"

# ═══════════════════════════════════════════════════════════════
# BANNER (siempre visible)
# ═══════════════════════════════════════════════════════════════
if banner_html:
    st.markdown(f'<div class="vg-banner-wrap">{banner_html}</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# SELECTOR DE MODO  — dos botones grandes
# ═══════════════════════════════════════════════════════════════
col_vg, col_mun = st.columns(2)
with col_vg:
    if st.button("⚽  VINOTINTO GALÁCTICO", use_container_width=True, key="btn_vg"):
        st.session_state.modo = "vg"
        st.session_state.resultado = None
with col_mun:
    if st.button("🌍  MUNDIAL 2026", use_container_width=True, key="btn_mun"):
        st.session_state.modo = "mundial"
        st.session_state.resultado = None

modo = st.session_state.modo

# Color del botón activo según modo
if modo == "vg":
    st.markdown("""
    <style>
    button[kind="secondary"]:first-of-type,
    div[data-testid="stButton"]:nth-child(1) button {
        background: linear-gradient(135deg,#7a1a2e,#c0392b) !important;
        box-shadow: 0 4px 15px rgba(192,57,43,0.5) !important;
    }
    div[data-testid="stButton"]:nth-child(2) button {
        background: #1a1a1a !important;
        box-shadow: none !important;
        border: 1px solid #333 !important;
    }
    </style>""", unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
    div[data-testid="stButton"]:nth-child(1) button {
        background: #1a1a1a !important;
        box-shadow: none !important;
        border: 1px solid #333 !important;
    }
    div[data-testid="stButton"]:nth-child(2) button {
        background: linear-gradient(135deg,#0d2b0d,#1a6b1a) !important;
        box-shadow: 0 4px 15px rgba(45,158,45,0.5) !important;
    }
    </style>""", unsafe_allow_html=True)

st.markdown("<hr style='border-color:#2a2a2a;margin:.4rem 0 1rem 0;'>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# IMPORTS SEGÚN MODO
# ═══════════════════════════════════════════════════════════════
if modo == "vg":
    from core.excel_reader import load_sources
    from core.txt_exporter import export_txt
    from core.html_exporter import export_html
    from extractores.factory import get_extractor
    CATEGORY_ICONS = {
        "Real Madrid Masculino":        "👑",
        "Real Madrid Femenino":         "👑",
        "LaLiga":                       "🇪🇸",
        "Selección Española Masculina":  "🇪🇸",
        "Selección Española Femenina":   "🇪🇸",
        "Vinotinto Masculina":          "🇻🇪",
        "Vinotinto Femenina":           "🇻🇪",
        "Liga FUTVE":                   "🇻🇪",
    }
    cat_css = "cat-vg"
    accent  = "#c0392b"
else:
    from mundial.core.excel_reader  import load_sources
    from mundial.core.txt_exporter  import export_txt
    from mundial.core.html_exporter import export_html
    from mundial.extractores.factory import get_extractor
    CATEGORY_ICONS = {
        "📺 TV / Canal":     "📺",
        "📰 Prensa Escrita": "📰",
        "💻 Digital":        "💻",
    }
    cat_css = "cat-mun"
    accent  = "#d4af37"

# ═══════════════════════════════════════════════════════════════
# CARGAR FUENTES
# ═══════════════════════════════════════════════════════════════
@st.cache_data(show_spinner=False)
def _load_vg():
    from core.excel_reader import load_sources as ls
    return ls()

@st.cache_data(show_spinner=False)
def _load_mundial():
    from mundial.core.excel_reader import load_sources as ls
    return ls()

try:
    sources  = _load_vg() if modo == "vg" else _load_mundial()
    excel_ok = True
except Exception as exc:
    sources    = {}
    excel_ok   = False
    excel_error = str(exc)

# ═══════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    if logo_src:
        st.markdown(
            f'<div style="overflow:hidden;width:90%;margin:0.5rem auto 1rem auto;'
            f'border-radius:50%;aspect-ratio:1/1;">'
            f'<img src="{logo_src}" style="width:100%;transform:scale(1.7);'
            f'transform-origin:center center;display:block;" alt="Logo"></div>',
            unsafe_allow_html=True
        )

    titulo_sidebar = "⚽ VG · Fuentes" if modo == "vg" else "🌍 MUNDIAL · Fuentes"
    st.markdown(f"## {titulo_sidebar}")

    if not excel_ok:
        st.error(f"❌ Error al leer el Excel:\n\n{excel_error}")
        st.stop()

    selected: dict[str, list[dict]] = {}

    for cat, fuentes in sources.items():
        icon = CATEGORY_ICONS.get(cat, "📌")
        st.markdown(f'<div class="cat-label {cat_css}">{icon} {cat}</div>', unsafe_allow_html=True)

        cat_key  = cat.replace(" ", "_").replace("/","_")
        todo_key = f"todo_{modo}_{cat_key}"

        fuentes_keys = []
        for idx, f in enumerate(fuentes):
            url_slug  = urlparse(f["url"]).netloc.replace(".", "_")
            path_slug = urlparse(f["url"]).path.strip("/").replace("/", "_")[:30]
            chk_key   = f"chk_{modo}_{cat_key}_{url_slug}_{path_slug}_{idx}"
            fuentes_keys.append((f, chk_key))

        def toggle_all(tk=todo_key, fk=[k for _, k in fuentes_keys]):
            val = st.session_state[tk]
            for key in fk:
                st.session_state[key] = val

        for f, k in fuentes_keys:
            if st.checkbox(f["nombre"], key=k):
                selected.setdefault(cat, []).append(f)

        st.checkbox("🔳 Seleccionar todo", key=todo_key, on_change=toggle_all)

    st.markdown("---")
    total_sel = sum(len(v) for v in selected.values())
    st.caption(f"**{total_sel}** fuente(s) seleccionada(s)")

# ═══════════════════════════════════════════════════════════════
# BARRA TÍTULO + BOTONES
# ═══════════════════════════════════════════════════════════════
titulo_modo = "VINOTINTO GALÁCTICO" if modo == "vg" else "MUNDIAL 2026"
emoji_modo  = "⚽" if modo == "vg" else "🌍"

col_title, col_btn_prensa, col_btn_extraer = st.columns([3, 1, 1])

with col_title:
    st.markdown(f"""
    <div style="padding:.4rem 0 .2rem 0;">
        <div style="font-family:'Bebas Neue',sans-serif;font-size:2rem;
                    color:#fff;letter-spacing:3px;line-height:1;">
            {emoji_modo} NEWS EXTRACTOR · {titulo_modo}
        </div>
        <div style="background:{accent};color:#fff;font-size:.72rem;
                    padding:.2rem .7rem;border-radius:20px;letter-spacing:1px;
                    display:inline-block;margin-top:.3rem;
                    box-shadow:0 2px 8px rgba(0,0,0,0.4);">
            HOY: {date.today().strftime("%d / %m / %Y")}
        </div>
    </div>
    """, unsafe_allow_html=True)

# Botón Prensa Deportiva (solo en modo VG)
with col_btn_prensa:
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    if modo == "vg":
        html_content = None
        for p in [Path("Prensa Deportiva/Prensa_Deportiva.html"), Path("Prensa_Deportiva.html")]:
            if p.exists():
                try:
                    html_content = p.read_bytes()
                    break
                except Exception:
                    pass
        if html_content:
            import json
            import streamlit.components.v1 as components
            html_json  = json.dumps(html_content.decode("utf-8", errors="replace"))
            button_html = f"""
            <style>
            body {{ margin:0;padding:0;background:transparent;overflow:hidden; }}
            button {{
                background:linear-gradient(135deg,#7a1a2e,#c0392b);
                color:white;border:none;padding:0.5rem;
                font-family:'Bebas Neue',sans-serif;font-size:1.15rem;
                letter-spacing:1px;border-radius:6px;cursor:pointer;
                width:100%;box-shadow:0 4px 15px rgba(192,57,43,0.4);
                transition:all 0.2s ease;box-sizing:border-box;
            }}
            button:hover {{ box-shadow:0 6px 20px rgba(192,57,43,0.7);transform:translateY(-1px); }}
            </style>
            <button onclick='(function(){{
                var w=window.open("","_blank");
                if(w){{w.document.open();w.document.write({html_json});w.document.close();}}
                else{{alert("Habilita ventanas emergentes para ver la prensa.");}}
            }})()'>🗞️ PRENSA DEPORTIVA</button>"""
            components.html(button_html, height=65)
    else:
        st.markdown(
            f'<div style="height:42px;display:flex;align-items:center;justify-content:center;'
            f'background:#111;border:1px solid #222;border-radius:6px;'
            f'color:#d4af37;font-family:\'Bebas Neue\',sans-serif;font-size:1rem;'
            f'letter-spacing:2px;">🌍 MUNDIAL 2026</div>',
            unsafe_allow_html=True
        )

with col_btn_extraer:
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    run = st.button("⚡ EXTRAER NOTICIAS", disabled=total_sel == 0,
                    use_container_width=True, key="btn_extraer")

st.markdown("<hr style='border-color:#2a2a2a;margin-top:.5rem;'>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# EXTRACCIÓN
# ═══════════════════════════════════════════════════════════════
if "resultado" not in st.session_state:
    st.session_state.resultado = None

if run:
    st.session_state.resultado = None
    all_noticias: list[dict] = []
    all_log:      list[dict] = []

    progress   = st.progress(0, text="Iniciando extracción…")
    status_box = st.empty()

    flat = [(cat, f) for cat, fuentes in selected.items() for f in fuentes]
    total = len(flat)

    async def run_all():
        for i, (cat, f) in enumerate(flat):
            status_box.info(f"🔍 Procesando: **{f['nombre']}** — {cat}")
            ext = get_extractor(f["nombre"], f["url"], cat)
            noticias, log = await ext.extract()
            all_noticias.extend(noticias)
            all_log.append(log)
            progress.progress((i + 1) / total, text=f"{i+1}/{total} fuentes procesadas")

    asyncio.run(run_all())
    progress.empty()
    status_box.empty()

    txt_path  = export_txt(all_noticias, all_log)
    html_path = export_html(all_noticias, all_log)

    st.session_state.resultado = {
        "noticias":  all_noticias,
        "log":       all_log,
        "txt_path":  txt_path,
        "html_path": html_path,
        "modo":      modo,
    }

# ═══════════════════════════════════════════════════════════════
# RESULTADOS
# ═══════════════════════════════════════════════════════════════
import streamlit.components.v1 as components

if st.session_state.resultado:
    res      = st.session_state.resultado
    noticias = res["noticias"]
    log      = res["log"]
    txt_path  = res["txt_path"]
    html_path = res["html_path"]

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("📰 Noticias extraídas",    len(noticias))
    k2.metric("✅ Fuentes con noticias",  sum(1 for l in log if l["estado"] == "Correcto"))
    k3.metric("🕳️ Sin noticias hoy",      sum(1 for l in log if "sin noticias" in l["estado"].lower()))
    k4.metric("❌ Errores",               sum(1 for l in log if l["estado"] == "Error"))

    st.markdown("---")
    c1, c2 = st.columns(2)
    if Path(txt_path).exists():
        c1.download_button("📥 Descargar noticias.txt",  data=Path(txt_path).read_bytes(),
                           file_name="noticias.txt",  mime="text/plain")
    if Path(html_path).exists():
        c2.download_button("🌐 Descargar noticias.html", data=Path(html_path).read_bytes(),
                           file_name="noticias.html", mime="text/html")

    st.markdown("---")

    tabs = [f"📰 Noticias ({len(noticias)})", "📋 Informe de control"]
    if res.get("modo") == "vg":
        tabs.append("🗞️ Panel de Prensa")

    tab_objs = st.tabs(tabs)

    with tab_objs[0]:
        if not noticias:
            st.warning("No se encontraron noticias del día en las fuentes seleccionadas.")
        for n in noticias:
            st.markdown(f"##### [{n.get('title','Sin título')}]({n.get('url','#')})")
            cols = st.columns([1, 4])
            if n.get("imagen"):
                cols[0].image(n["imagen"], use_container_width=True)
            with cols[1]:
                st.markdown(
                    f"<div style='color:{accent};font-size:.9rem;font-weight:600;"
                    f"margin-bottom:.4rem;'>📌 {n.get('fuente','')} &nbsp;|&nbsp; "
                    f"{n.get('categoria','')} &nbsp;|&nbsp; 📅 {n.get('date','')} "
                    f"&nbsp;|&nbsp; ✍ {n.get('author','')}</div>",
                    unsafe_allow_html=True
                )
                resumen = n.get("body","")[:400]
                if len(n.get("body","")) > 400:
                    resumen += "..."
                st.markdown(
                    f"<div style='font-size:.93rem;color:#ddd;line-height:1.5;'>"
                    f"{resumen}</div>", unsafe_allow_html=True
                )
            st.markdown("---")

    with tab_objs[1]:
        for entry in log:
            icon = "✅" if entry["estado"] == "Correcto" else (
                   "⚠️" if "sin" in entry["estado"].lower() else "❌")
            err = f" — `{entry['error']}`" if entry.get("error") else ""
            st.markdown(
                f"{icon} **{entry['fuente']}** · "
                f"Encontradas: `{entry['encontradas']}` · "
                f"Extraídas: `{entry['extraidas']}` · "
                f"{entry['estado']}{err}"
            )

    if res.get("modo") == "vg" and len(tab_objs) > 2:
        with tab_objs[2]:
            for p in [Path("Prensa Deportiva/Prensa_Deportiva.html"), Path("Prensa_Deportiva.html")]:
                if p.exists():
                    components.html(p.read_text(encoding="utf-8"), height=800, scrolling=True)
                    break
            else:
                st.error("No se encontró Prensa_Deportiva.html")

else:
    logo_html = (f'<img src="{logo_src}" style="width:100px;border-radius:12px;'
                 f'box-shadow:0 6px 20px rgba(0,0,0,0.6);">'
                 if logo_src else '<div style="font-size:4rem;">⚽</div>')
    desc = ("Solo se extraerán noticias del día de hoy · Máximo 3 por fuente"
            if modo == "vg" else
            "41 fuentes · 16 TV · 17 Prensa · 8 Digital · Solo noticias de hoy")
    st.markdown(f"""
    <div style="text-align:center; padding: 3rem 0; color: #555;">
        {logo_html}
        <div style="font-family:'Bebas Neue',sans-serif; font-size:1.6rem;
                    letter-spacing:3px; color:{accent}; margin-top:1rem;">
            SELECCIONA LAS FUENTES Y PULSA EXTRAER
        </div>
        <div style="font-size:.9rem; margin-top:.5rem; color:#666;">{desc}</div>
    </div>
    """, unsafe_allow_html=True)
