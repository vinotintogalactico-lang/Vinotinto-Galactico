"""
VINOTINTO GALÁCTICO NEWS EXTRACTOR v11.0
Funcional - Sin instalación automática de playwright
"""
import os
import sys
import time
from pathlib import Path
os.environ['TZ'] = 'America/Caracas'
if hasattr(time, 'tzset'):
    time.tzset()

import asyncio
import base64
import logging
from datetime import datetime
import streamlit as st

# ═════════════════════════════════════════════════════════════════════════════
# CONFIG
# ═════════════════════════════════════════════════════════════════════════════
BASE_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ═════════════════════════════════════════════════════════════════════════════
# CONFIG DE PÁGINA
# ═════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="VG Extractor",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ═════════════════════════════════════════════════════════════════════════════
# CSS
# ═════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
.banner-container {
    width: 100%;
    max-width: 1200px;
    margin: 0 auto 2rem auto;
    border-radius: 8px;
    overflow: hidden;
}
.banner-container img {
    width: 100%;
    height: auto;
    display: block;
}
[data-testid="stSidebar"] {
    display: none;
}
.stButton > button {
    height: 50px;
    background: linear-gradient(135deg, #c0392b, #8b0000);
    color: white;
    border: none;
    border-radius: 6px;
    font-weight: 600;
    font-size: 1rem;
    width: 100%;
}
.news-item {
    background: #252525;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    border-left: 4px solid #c0392b;
    border-radius: 4px;
}
.news-item h3 {
    color: #fff;
    margin: 0 0 0.5rem 0;
}
.news-meta {
    color: #888;
    font-size: 0.85rem;
    margin-bottom: 1rem;
}
.news-content {
    color: #d0d0d0;
    line-height: 1.6;
}
</style>
""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# CARGAR BANNER
# ═════════════════════════════════════════════════════════════════════════════
def _b64(path: Path) -> str:
    try:
        if path.exists():
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except Exception as e:
        logger.warning(f"No se cargó {path}: {e}")
    return ""

banner_b64 = _b64(BASE_DIR / "banner-vinotinto.png")

# ═════════════════════════════════════════════════════════════════════════════
# INICIALIZAR SESSION STATE
# ═════════════════════════════════════════════════════════════════════════════
if 'vg_selection' not in st.session_state:
    st.session_state.vg_selection = {}
if 'mundial_selection' not in st.session_state:
    st.session_state.mundial_selection = {}
if 'noticias_extraidas' not in st.session_state:
    st.session_state.noticias_extraidas = []
if 'show_mundial' not in st.session_state:
    st.session_state.show_mundial = False

# ═════════════════════════════════════════════════════════════════════════════
# IMPORTAR MÓDULOS (DESPUÉS de inicializar session_state)
# ═════════════════════════════════════════════════════════════════════════════
try:
    from core.excel_reader import load_sources_vinotinto, load_sources_mundial
    from core.txt_exporter import export_txt
    from core.html_exporter import export_html
    from extractores.factory import get_extractor
except ImportError as e:
    st.error(f"❌ Error importando módulos: {e}")
    st.error("💡 Ejecuta: pip install -r requirements.txt")
    st.stop()

# ═════════════════════════════════════════════════════════════════════════════
# FUNCIÓN DE EXTRACCIÓN
# ═════════════════════════════════════════════════════════════════════════════
def run_extraction(urls_to_extract, output_prefix):
    if not urls_to_extract:
        st.warning("⚠️ Selecciona al menos una fuente")
        return []

    st.info(f"🚀 Procesando {len(urls_to_extract)} fuentes...")
    progress_bar = st.progress(0)
    status = st.empty()
    noticias = []

    async def extract_all():
        for idx, (nombre, url, categoria) in enumerate(urls_to_extract):
            status.text(f"📥 [{idx+1}/{len(urls_to_extract)}] {nombre}")
            try:
                extractor = get_extractor(nombre, url, categoria)
                noticias_ext, log = await extractor.extract()
                noticias.extend(noticias_ext)
            except Exception as e:
                logger.error(f"❌ {nombre}: {e}")
            progress_bar.progress((idx + 1) / len(urls_to_extract))
        status.text("✅ ¡Extracción completada!")

    with st.spinner("Extrayendo noticias..."):
        try:
            asyncio.run(extract_all())
        except Exception as e:
            st.error(f"❌ Error: {e}")
            return []

    if noticias:
        txt_path = OUTPUT_DIR / f"{output_prefix}.txt"
        html_path = OUTPUT_DIR / f"{output_prefix}.html"
        export_txt(noticias, str(txt_path))
        export_html(noticias, str(html_path))
        st.success(f"✅ {len(noticias)} noticias extraídas")
        
        col1, col2 = st.columns(2)
        with col1:
            with open(txt_path, "rb") as f:
                st.download_button("📥 TXT", f, f"{output_prefix}.txt", key=f"dl_txt_{output_prefix}")
        with col2:
            with open(html_path, "rb") as f:
                st.download_button("📥 HTML", f, f"{output_prefix}.html", key=f"dl_html_{output_prefix}")
    
    return noticias

# ═════════════════════════════════════════════════════════════════════════════
# SIDEBAR - FUENTES VINOTINTO
# ═════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 📰 Fuentes")
    st.markdown("---")

    try:
        sources_vinotinto = load_sources_vinotinto()
    except Exception as e:
        st.error(f"❌ Error: {e}")
        sources_vinotinto = {}

    CATEGORY_ORDER = [
        "Real Madrid Masculino",
        "Real Madrid Femenino",
        "LaLiga",
        "Selección Española Masculina",
        "Selección Española Femenina",
        "Vinotinto Masculina",
        "Liga FUTVE",
        "Vinotinto Femenina"
    ]

    CATEGORY_ICONS = {
        "Real Madrid Masculino": "👑",
        "Real Madrid Femenino": "👑",
        "LaLiga": "🇪🇸",
        "Selección Española Masculina": "🇪🇸",
        "Selección Española Femenina": "🇪",
        "Vinotinto Masculina": "🇻🇪",
        "Vinotinto Femenina": "🇻",
        "Liga FUTVE": "🇻",
    }

    selected_sources = {}
    
    for categoria in CATEGORY_ORDER:
        if categoria not in sources_vinotinto:
            continue
            
        fuentes = sources_vinotinto[categoria]
        icon = CATEGORY_ICONS.get(categoria, "📰")
        
        st.markdown(f"**{icon} {categoria}**")
        
        # CHECKBOX "SELECCIONAR TODO" - TOGGLE
        select_all_key = f"select_all_{categoria.replace(' ', '_')}"
        select_all = st.checkbox(
            "□ Seleccionar todo",
            key=select_all_key,
            value=False
        )
        
        if select_all:
            for nombre, url in fuentes:
                st.session_state.vg_selection[f"vg_{categoria}_{nombre}"] = True
        else:
            for nombre, url in fuentes:
                st.session_state.vg_selection[f"vg_{categoria}_{nombre}"] = False
        
        selected_sources[categoria] = {}
        for nombre, url in fuentes:
            check_key = f"vg_{categoria}_{nombre}"
            checked = st.checkbox(
                f"□ {nombre}",
                key=check_key,
                value=st.session_state.vg_selection.get(check_key, False)
            )
            if checked:
                selected_sources[categoria][nombre] = url
        
        st.markdown("")

# ═════════════════════════════════════════════════════════════════════════════
# ÁREA PRINCIPAL
# ═════════════════════════════════════════════════════════════════════════════

# Banner
if banner_b64:
    st.markdown(f'''
    <div class="banner-container">
        <img src="data:image/png;base64,{banner_b64}" alt="Vinotinto Galáctico">
    </div>
    ''', unsafe_allow_html=True)

# Fecha
hoy = datetime.now().strftime("%d / %m / %Y")
st.markdown(f'<div style="color: #c0392b; font-size: 0.85rem; margin: -1rem 0 1rem 0; text-align: center;">📅 HOY: {hoy}</div>', unsafe_allow_html=True)

# BOTONES PRINCIPALES
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🏆 MUNDIAL 2026", key="btn_mundial"):
        st.session_state.show_mundial = not st.session_state.show_mundial

with col2:
    if st.button("📰 PRENSA DEPORTIVA", key="btn_prensa"):
        html_path = BASE_DIR / "static" / "Prensa_Deportiva.html"
        if html_path.exists():
            st.info(f"📄 Archivo: {html_path}")
            st.markdown(f'<a href="/app/static/Prensa_Deportiva.html" target="_blank">Abrir en nueva pestaña</a>', unsafe_allow_html=True)
        else:
            st.error("❌ No existe static/Prensa_Deportiva.html")

with col3:
    if st.button("⚡ EXTRAER NOTICIAS", key="btn_extraer"):
        urls_to_extract = []
        for cat, nombres_urls in selected_sources.items():
            for nombre, url in nombres_urls.items():
                urls_to_extract.append((nombre, url, cat))
        st.session_state.noticias_extraidas = run_extraction(urls_to_extract, "noticias_vinotinto")

st.markdown("---")

# MOSTRAR MUNDIAL
if st.session_state.show_mundial:
    st.markdown("### 🌍 MUNDIAL 2026")
    try:
        sources_mundial = load_sources_mundial()
        if "Mundial Global" in sources_mundial:
            st.info(f"🏆 {len(sources_mundial['Mundial Global'])} fuentes")
            
            mundial_select_all = st.checkbox(
                "□ Seleccionar todas",
                key="mundial_select_all",
                value=False
            )
            
            if mundial_select_all:
                for nombre, url in sources_mundial["Mundial Global"]:
                    st.session_state.mundial_selection[f"mundial_{nombre}"] = True
            else:
                st.session_state.mundial_selection = {}
            
            cols = st.columns(3)
            selected_mundial = {}
            for idx, (nombre, url) in enumerate(sources_mundial["Mundial Global"]):
                with cols[idx % 3]:
                    check_key = f"mundial_{nombre}"
                    checked = st.checkbox(
                        f"□ {nombre}",
                        key=check_key,
                        value=st.session_state.mundial_selection.get(check_key, False)
                    )
                    if checked:
                        selected_mundial[nombre] = url
            
            if st.button("⚡ EXTRAER MUNDIAL", key="btn_extraer_mundial"):
                urls = [(n, u, "Mundial") for n, u in selected_mundial.items()]
                st.session_state.noticias_extraidas = run_extraction(urls, "noticias_mundial")
    except Exception as e:
        st.error(f"Error: {e}")

# MOSTRAR NOTICIAS
if st.session_state.noticias_extraidas:
    st.markdown("### 📰 NOTICIAS EXTRAÍDAS")
    for noticia in st.session_state.noticias_extraidas:
        st.markdown(f"""
        <div class="news-item">
            <h3>{noticia.get('titulo', 'Sin título')}</h3>
            <div class="news-meta">
                {noticia.get('fuente', '')} | {noticia.get('categoria', '')} | {noticia.get('fecha', '')}
            </div>
            <div class="news-content">
                {noticia.get('resumen', '')[:500]}...
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")
st.markdown('<div style="text-align: center; color: #666; font-size: 0.8rem;">⚽ Vinotinto Galáctico v11.0</div>', unsafe_allow_html=True)