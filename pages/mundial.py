import os
import time

os.environ['TZ'] = 'America/Caracas'
if hasattr(time, 'tzset'):
    time.tzset()

import asyncio
import logging
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import streamlit as st

# ── Instalar Playwright automáticamente ──────────────────────────────────────
@st.cache_resource(show_spinner=False)
def _install_playwright():
    try:
        os.system(f"{sys.executable} -m playwright install chromium")
    except Exception as e:
        print(f"Error instalando playwright: {e}")

_install_playwright()
Path("output").mkdir(exist_ok=True)

from mundial.mundial_core.excel_reader import load_sources
from mundial.mundial_core.txt_exporter import export_txt
from mundial.mundial_core.html_exporter import export_html
from mundial.mundial_extractores.factory import get_extractor

logging.basicConfig(level=logging.INFO)

CATEGORY_ICONS = {
    "📺 TV / Canal":     "📺",
    "📰 Prensa Escrita": "📰",
    "💻 Digital":        "💻",
}



# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;600&display=swap');

/* ─── BANNER ─── */
.mw-banner-wrap {
    margin: -1rem -1rem 0 -1rem;
    overflow: hidden;
    background: linear-gradient(135deg, #0a1a0a 0%, #0d2b0d 50%, #0a1a0a 100%);
    border-bottom: 4px solid #d4af37;
    padding: 2rem 2rem 1.5rem 2rem;
    text-align: center;
}
.mw-banner-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 3.5rem;
    color: #d4af37;
    letter-spacing: 6px;
    line-height: 1;
    text-shadow: 0 0 30px rgba(212,175,55,0.4);
}
.mw-banner-sub {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.2rem;
    color: #aaa;
    letter-spacing: 4px;
    margin-top: 0.3rem;
}
.mw-ball { font-size: 3rem; margin-bottom: 0.5rem; }

/* ─── TITLE BAR ─── */
.mw-titlebar {
    background: linear-gradient(135deg, #0a1a0a, #0d2b0d);
    border-bottom: 2px solid #1a6b1a;
    padding: .8rem 1.5rem;
    margin: 0 -1rem 1.5rem -1rem;
    display: flex; align-items: center;
    justify-content: space-between; gap: 1rem;
}

/* ─── CATEGORÍAS SIDEBAR ─── */
.cat-label {
    font-family: 'Bebas Neue', sans-serif; font-size: 1rem;
    letter-spacing: 2px; color: #d4af37;
    padding: .3rem 0 .1rem 0; border-bottom: 1px solid #1a3a1a;
    margin-top: .8rem; margin-bottom: .3rem;
}

/* ─── BOTÓN EXTRAER ─── */
div[data-testid="stButton"] button {
    background: linear-gradient(135deg, #1a6b1a, #2d9e2d) !important;
    color: white !important; border: none !important;
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 1.2rem !important; letter-spacing: 3px !important;
    padding: .75rem 1.5rem !important; border-radius: 6px !important;
    width: 100% !important;
    box-shadow: 0 4px 15px rgba(45,158,45,0.4) !important;
    transition: all 0.2s ease !important;
}
div[data-testid="stButton"] button:hover {
    box-shadow: 0 6px 20px rgba(212,175,55,0.6) !important;
    transform: translateY(-1px);
}

/* ─── TARJETAS ─── */
.news-card {
    background: #111811; border: 1px solid #1e2e1e;
    border-left: 4px solid #1a6b1a; border-radius: 4px;
    padding: 1.2rem 1.5rem; margin-bottom: 1.2rem;
}
</style>
""", unsafe_allow_html=True)

# ── BANNER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="mw-banner-wrap">
    <div class="mw-ball">🌍⚽🏆</div>
    <div class="mw-banner-title">MUNDIAL 2026</div>
    <div class="mw-banner-sub">NEWS EXTRACTOR · ESTADOS UNIDOS · CANADÁ · MÉXICO</div>
</div>
""", unsafe_allow_html=True)

# ── CARGAR FUENTES ────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def _load_sources_mundial():
    return load_sources()

try:
    sources = _load_sources_mundial()
    excel_ok = True
except Exception as exc:
    sources = {}
    excel_ok = False
    excel_error = str(exc)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 1rem 0 0.5rem 0;">
        <div style="font-size:2.5rem;">🏆</div>
        <div style="font-family:'Bebas Neue',sans-serif; font-size:1.4rem;
                    color:#d4af37; letter-spacing:3px;">MUNDIAL 2026</div>
        <div style="font-size:0.75rem; color:#666; letter-spacing:1px;">FUENTES DE PRENSA</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    if not excel_ok:
        st.error(f"❌ Error al leer el Excel:\n\n{excel_error}")
        st.stop()

    selected: dict[str, list[dict]] = {}

    for cat, fuentes in sources.items():
        icon = CATEGORY_ICONS.get(cat, "📌")
        st.markdown(f'<div class="cat-label">{icon} {cat}</div>', unsafe_allow_html=True)

        cat_key = cat.replace(" ", "_").replace("/", "_")
        todo_key = f"todo_{cat_key}"

        fuentes_keys = []
        for idx, f in enumerate(fuentes):
            url_slug = urlparse(f["url"]).netloc.replace(".", "_")
            path_slug = urlparse(f["url"]).path.strip("/").replace("/", "_")[:30]
            chk_key = f"chk_{cat_key}_{url_slug}_{path_slug}_{idx}"
            fuentes_keys.append((f, chk_key))

        def toggle_all(tk=todo_key, fk=[k for _, k in fuentes_keys]):
            val = st.session_state[tk]
            for key in fk:
                st.session_state[key] = val

        for f, k in fuentes_keys:
            if st.checkbox(f["nombre"], key=k):
                selected.setdefault(cat, []).append(f)

        st.checkbox("🔳 Seleccionar todo", key=todo_key, on_change=toggle_all)
        st.markdown("")

    st.markdown("---")
    total_sel = sum(len(v) for v in selected.values())
    st.caption(f"**{total_sel}** fuente(s) seleccionada(s)")

# ── BARRA PRINCIPAL ───────────────────────────────────────────────────────────
col_title, col_btn = st.columns([4, 1])

with col_title:
    st.markdown(f"""
    <div style="padding:.4rem 0 .2rem 0;">
        <div style="font-family:'Bebas Neue',sans-serif;font-size:2rem;
                    color:#fff;letter-spacing:3px;line-height:1;">
            EXTRACTOR DE NOTICIAS
        </div>
        <div style="background:#1a6b1a;color:#fff;font-size:.72rem;
                    padding:.2rem .7rem;border-radius:20px;letter-spacing:1px;
                    display:inline-block;margin-top:.3rem;
                    box-shadow:0 2px 8px rgba(0,0,0,0.4);">
            HOY: {date.today().strftime("%d / %m / %Y")}
        </div>
        <span style="background:#d4af37;color:#000;font-size:.72rem;
                     padding:.2rem .7rem;border-radius:20px;letter-spacing:1px;
                     display:inline-block;margin-top:.3rem;margin-left:.5rem;
                     font-weight:700;">
            FIFA WORLD CUP 2026
        </span>
    </div>
    """, unsafe_allow_html=True)

with col_btn:
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    run = st.button("⚡ EXTRAER NOTICIAS", disabled=total_sel == 0, use_container_width=True)

st.markdown("<hr style='border-color:#1e2e1e;margin-top:.5rem;'>", unsafe_allow_html=True)

# ── EXTRACCIÓN ────────────────────────────────────────────────────────────────
if "resultado_mundial" not in st.session_state:
    st.session_state.resultado_mundial = None

if run:
    st.session_state.resultado_mundial = None
    all_noticias: list[dict] = []
    all_log: list[dict] = []

    progress = st.progress(0, text="Iniciando extracción Mundial 2026…")
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

    st.session_state.resultado_mundial = {
        "noticias": all_noticias,
        "log": all_log,
        "txt_path": txt_path,
        "html_path": html_path,
    }

# ── RESULTADOS ────────────────────────────────────────────────────────────────
if st.session_state.resultado_mundial:
    res = st.session_state.resultado_mundial
    noticias = res["noticias"]
    log = res["log"]
    txt_path: Path = res["txt_path"]
    html_path: Path = res["html_path"]

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🌍 Noticias extraídas", len(noticias))
    k2.metric("✅ Fuentes con noticias", sum(1 for l in log if l["estado"] == "Correcto"))
    k3.metric("🕳️ Sin noticias hoy", sum(1 for l in log if "sin noticias" in l["estado"].lower()))
    k4.metric("❌ Errores", sum(1 for l in log if l["estado"] == "Error"))

    st.markdown("---")

    col1, col2 = st.columns(2)
    if txt_path.exists():
        col1.download_button(
            "📥 Descargar mundial_noticias.txt",
            data=txt_path.read_bytes(),
            file_name="mundial_noticias.txt",
            mime="text/plain"
        )
    if html_path.exists():
        col2.download_button(
            "🌐 Descargar mundial_noticias.html",
            data=html_path.read_bytes(),
            file_name="mundial_noticias.html",
            mime="text/html"
        )

    st.markdown("---")
    tab_news, tab_log = st.tabs([f"🌍 Noticias ({len(noticias)})", "📋 Informe de control"])

    with tab_news:
        if not noticias:
            st.warning("No se encontraron noticias del día en las fuentes seleccionadas.")
        for n in noticias:
            cat = n.get("categoria", "")
            icon = CATEGORY_ICONS.get(cat, "⚽")
            st.markdown(f"##### {icon} [{n.get('title', 'Sin título')}]({n.get('url', '#')})")
            cols = st.columns([1, 4])
            if n.get("imagen"):
                cols[0].image(n["imagen"], use_container_width=True)
            with cols[1]:
                st.markdown(
                    f"<div style='color:#d4af37;font-size:0.9rem;font-weight:600;"
                    f"margin-bottom:0.4rem;'>📡 {n.get('fuente','')} &nbsp;|&nbsp; "
                    f"{cat} &nbsp;|&nbsp; 📅 {n.get('date','')} &nbsp;|&nbsp; "
                    f"✍ {n.get('author','')}</div>",
                    unsafe_allow_html=True
                )
                resumen = n.get("body", "")[:400]
                if len(n.get("body", "")) > 400:
                    resumen += "..."
                st.markdown(
                    f"<div style='font-size:0.93rem;color:#ddd;line-height:1.5;'>"
                    f"{resumen}</div>",
                    unsafe_allow_html=True
                )
            st.markdown("---")

    with tab_log:
        for entry in log:
            icon = "✅" if entry["estado"] == "Correcto" else (
                "⚠️" if "sin" in entry["estado"].lower() else "❌"
            )
            err = f" — `{entry['error']}`" if entry.get("error") else ""
            st.markdown(
                f"{icon} **{entry['fuente']}** · "
                f"Encontradas: `{entry['encontradas']}` · "
                f"Extraídas: `{entry['extraidas']}` · "
                f"{entry['estado']}{err}"
            )

else:
    st.markdown("""
    <div style="text-align:center; padding: 4rem 0; color: #555;">
        <div style="font-size:5rem;">🏆</div>
        <div style="font-family:'Bebas Neue',sans-serif; font-size:1.6rem;
                    letter-spacing:3px; color:#d4af37; margin-top:1rem;">
            SELECCIONA LAS FUENTES Y PULSA EXTRAER
        </div>
        <div style="font-size:.9rem; margin-top:.5rem; color:#666;">
            Solo se extraerán noticias del día de hoy · Máximo 3 por fuente · 41 fuentes disponibles
        </div>
        <div style="font-size:.8rem; margin-top:1rem; color:#444;">
            🇲🇽 México · 🇻🇪 Venezuela · 🇨🇴 Colombia · 🇦🇷 Argentina · 🇨🇱 Chile · 🇵🇪 Perú · 🇺🇾 Uruguay · 🇭🇳 Honduras · 🇪🇨 Ecuador · 🇪🇸 España · 🌎 USA Hispano
        </div>
    </div>
    """, unsafe_allow_html=True)
