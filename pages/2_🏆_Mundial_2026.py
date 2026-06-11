"""
Página: 🏆 Mundial 2026
Extractor de noticias independiente para el Mundial FIFA 2026.
Incluye enlaces fijos como fallback por si falla el Excel en la nube.
"""
import os
import time
import asyncio
import logging
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import streamlit as st

from core.txt_exporter import export_txt
from core.html_exporter import export_html
from extractores.factory import get_extractor
from core.excel_reader import _friendly_name

logging.basicConfig(level=logging.WARNING)

# Enlaces de fallback (hardcoded) para que NUNCA falle en GitHub aunque el excel no suba
FALLBACK_LINKS = [
    'https://www.telemundodeportes.com/copa-mundial-fifa-2026', 'https://www.tudn.com/mundial-2026', 
    'https://www.tvazteca.com/aztecadeportes/futbol', 'https://televen.com/elnoticiero/copa-mundial-de-la-fifa-2026/', 
    'https://noticias.caracoltv.com/golcaracol/mundial-2026', 'https://www.noticiasrcn.com/deportes', 
    'https://www.tycsports.com/mundial', 'https://mitelefe.com/deportes/', 'https://www.directvgo.com/deportes', 
    'https://elcanaldelfutbol.com/', 'https://www.chilevision.cl/deportes', 'https://www.13.cl/deportes', 
    'https://www.latina.pe/deportes', 'https://www.rtve.es/play/deportes/', 
    'https://www.liderendeportes.com/noticias/futbol/mundial-2026/', 'https://meridiano.net/futbol/futbol-internacional/', 
    'https://www.winsports.co/futbol-internacional/', 'https://www.futbolred.com/futbol-internacional', 
    'https://www.record.com.mx/futbol', 'https://www.mediotiempo.com/futbol', 'https://www.foxsports.com.mx/futbol/', 
    'https://www.ole.com.ar/mundial/mundial-2026', 'https://www.elgrafico.com.ar/', 'https://redgol.cl/mundial/', 
    'https://www.alairelibre.cl/noticias/deportes/futbol/mundial/', 'https://depor.com/futbol-internacional/', 
    'https://libero.pe/futbol-internacional/', 'https://www.elpais.com.uy/ovacion/futbol', 
    'https://studiofutbol.com.ec/category/internacional/', 'https://www.diez.hn/futbolinternacional/', 
    'https://www.marca.com/futbol/mundial/', 'https://as.com/futbol/mundial/', 
    'https://www.mundodeportivo.com/futbol/mundial', 'https://www.sport.es/es/mundial/', 
    'https://www.relevo.com/futbol/mundial-futbol/', 'https://espndeportes.espn.com/futbol/copa-mundial/', 
    'https://www.infobae.com/deportes/', 'https://www.clarosports.com/futbol/mundial/', 
    'https://www.eltiempo.com/deportes/futbol-internacional', 'https://www.latercera.com/canal/el-deportivo/', 
    'https://www.eluniversal.com.mx/deportes/'
]

sources_dict = {"Mundial Global": [{"nombre": _friendly_name(url), "url": url} for url in FALLBACK_LINKS]}

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;600&display=swap');

/* Fondo general */
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background: #080808 !important;
}
[data-testid="stSidebar"] {
    background: #0a0a0a !important;
    border-right: 1px solid #1a1a1a;
}

/* Banner */
.wc-hero {
    background: linear-gradient(160deg, #0a0a0a 0%, #0d1f15 50%, #0a0a0a 100%);
    border-bottom: 2px solid #00ff85;
    padding: 1.5rem 2rem 1rem;
    margin: -1rem -1rem 1.5rem -1rem;
    display: flex;
    align-items: center;
    gap: 1.5rem;
}
.wc-hero img.wc-logo {
    height: 80px;
    width: auto;
    filter: drop-shadow(0 0 10px rgba(0,255,133,0.5));
}
.wc-hero .wc-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 3rem;
    color: #fff;
    letter-spacing: 4px;
    line-height: 1;
    text-shadow: 0 0 20px rgba(0,255,133,0.3);
}
.wc-hero .wc-subtitle {
    font-family: 'Inter', sans-serif;
    font-size: .85rem;
    color: #00ff85;
    letter-spacing: 2px;
    margin-top: .3rem;
}

/* Sidebar labels */
.wc-cat-label {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.2rem;
    letter-spacing: 2px;
    color: #00ff85;
    padding: .4rem 0 .1rem 0;
    border-bottom: 1px solid #1e1e1e;
    margin-top: .8rem;
    margin-bottom: .3rem;
}

/* Checkbox select all */
.sel-all { margin-bottom: 1rem; }

/* Botón extraer */
div[data-testid="stButton"] button {
    background: linear-gradient(135deg, #00b050, #00803a) !important;
    border: none !important;
    border-radius: 6px !important;
    width: 100% !important;
    box-shadow: 0 4px 20px rgba(0,255,133,0.35) !important;
    transition: all 0.2s ease !important;
    padding: 0.65rem 0.5rem !important;
}
div[data-testid="stButton"] button p {
    color: #fff !important;
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 18px !important;
    letter-spacing: 2px !important;
    margin: 0 !important;
}
div[data-testid="stButton"] button:hover {
    box-shadow: 0 6px 30px rgba(0,255,133,0.6) !important;
    transform: translateY(-2px) !important;
}
</style>
""", unsafe_allow_html=True)

LOGO_URL = "https://upload.wikimedia.org/wikipedia/en/thumb/4/4b/2026_FIFA_World_Cup_logo.svg/1200px-2026_FIFA_World_Cup_logo.svg.png"

st.markdown(f"""
<div class="wc-hero">
    <img class="wc-logo" src="{LOGO_URL}" alt="FIFA World Cup 2026">
    <div>
        <div class="wc-title">MUNDIAL 2026</div>
        <div class="wc-subtitle">EXTRACTOR DE PRENSA GLOBAL</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📰 Fuentes del Mundial")
    
    selected = []
    fuentes_list = sources_dict["Mundial Global"]
    
    # 1. Seleccionar todo
    todo_key = "wc_todo"
    def toggle_all():
        val = st.session_state[todo_key]
        for idx in range(len(fuentes_list)):
            st.session_state[f"wc_chk_{idx}"] = val
            
    st.checkbox("🔳 SELECCIONAR TODO", key=todo_key, on_change=toggle_all)
    st.markdown("<hr style='margin: 0.5rem 0; border-color:#2a2a2a;'>", unsafe_allow_html=True)

    # 2. Lista de fuentes
    for idx, f in enumerate(fuentes_list):
        if st.checkbox(f["nombre"], key=f"wc_chk_{idx}"):
            selected.append(f)
            
    st.markdown("---")
    st.caption(f"**{len(selected)}** fuente(s) seleccionada(s)")
    
    # Enlace para volver a la app principal
    if st.button("← VOLVER A PRENSA DEPORTIVA", key="back_btn"):
        st.switch_page("app.py")

# ── BOTÓN EXTRAER ─────────────────────────────────────────────────────────────
col_info, col_btn = st.columns([3, 1])
with col_info:
    st.markdown('<p style="color:#888; font-size:.9rem; margin-top:.5rem;">Selecciona las fuentes en el panel izquierdo y extrae las noticias globales del Mundial 2026.</p>', unsafe_allow_html=True)
with col_btn:
    run = st.button("⚡ EXTRAER NOTICIAS", disabled=len(selected) == 0, use_container_width=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ── EXTRACCIÓN ────────────────────────────────────────────────────────────────
if "wc_resultado" not in st.session_state:
    st.session_state.wc_resultado = None

if run:
    st.session_state.wc_resultado = None
    all_noticias: list[dict] = []
    all_log: list[dict] = []

    total = len(selected)
    progress = st.progress(0, text="Iniciando extracción del Mundial…")
    status_box = st.empty()

    async def run_all():
        for i, f in enumerate(selected):
            status_box.info(f"🔍 **{f['nombre']}**")
            extractor = get_extractor(f["nombre"], f["url"], "Mundial Global")
            noticias, log = await extractor.extract()
            all_noticias.extend(noticias)
            all_log.append(log)
            progress.progress((i + 1) / total, text=f"{i+1}/{total} fuentes procesadas")

    asyncio.run(run_all())
    progress.empty()
    status_box.empty()

    txt_path = export_txt(all_noticias, all_log)
    html_path = export_html(all_noticias, all_log)

    st.session_state.wc_resultado = {
        "noticias": all_noticias,
        "log": all_log,
        "txt_path": txt_path,
        "html_path": html_path,
    }

# ── RESULTADOS ────────────────────────────────────────────────────────────────
if st.session_state.wc_resultado:
    res = st.session_state.wc_resultado
    noticias = res["noticias"]
    log = res["log"]
    txt_path: Path = res["txt_path"]
    html_path: Path = res["html_path"]

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("📰 Extraídas", len(noticias))
    k2.metric("✅ Exitosas", sum(1 for l in log if l["estado"] == "Correcto"))
    k3.metric("⚠️ Vacías", sum(1 for l in log if "sin noticias" in l["estado"].lower()))
    k4.metric("❌ Errores", sum(1 for l in log if l["estado"] == "Error"))

    st.markdown("<hr>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    if txt_path.exists():
        col1.download_button("📥 Descargar .txt", data=txt_path.read_bytes(),
                             file_name="mundial_noticias.txt", mime="text/plain")
    if html_path.exists():
        col2.download_button("🌐 Descargar .html", data=html_path.read_bytes(),
                             file_name="mundial_noticias.html", mime="text/html")

    st.markdown("<hr>", unsafe_allow_html=True)
    
    # ── Visor de resultados integrados igual que app.py ──
    for i, n in enumerate(noticias, 1):
        st.markdown(f"#### [{n.get('title', 'Sin título')}]({n.get('url', '#')})")
        st.markdown(f"<div style='color:#00ff85; font-size:1.05rem;'>📌 Fuente: {n.get('fuente','')} | 📅 {n.get('date','')}</div>", unsafe_allow_html=True)
        resumen = n.get("body", "")[:400] + ('...' if len(n.get("body", "")) > 400 else '')
        st.markdown(f"<div style='color:#ddd;'>{resumen}</div>", unsafe_allow_html=True)
        st.markdown("---")
else:
    st.markdown(f"""
    <div style="text-align:center; padding: 2rem 0; color: #555;">
        <img src="{LOGO_URL}" style="width:120px; filter: drop-shadow(0 0 15px rgba(0,255,133,0.5));">
        <h2 style="color:#00ff85; font-family:'Bebas Neue', sans-serif; letter-spacing:2px;">LISTO PARA EXTRAER</h2>
        <p>Marca las fuentes en el menú izquierdo y pulsa el botón verde.</p>
    </div>
    """, unsafe_allow_html=True)
