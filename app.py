"""
VINOTINTO GALÁCTICO NEWS EXTRACTOR v7.0
Banner tamaño YouTube + Checkboxes estables + Todo funcional
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

try:
    from core.excel_reader import load_sources_vinotinto, load_sources_mundial
    from core.txt_exporter import export_txt
    from core.html_exporter import export_html
    from extractores.factory import get_extractor
except ImportError as e:
    st.error(f"❌ Error: {e}")
    st.stop()

# ═════════════════════════════════════════════════════════════════════════════
# CONFIG DE PÁGINA
# ═════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="VG Extractor",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═════════════════════════════════════════════════════════════════════════════
# CSS - Banner tamaño YouTube (normal)
# ═════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&display=swap');

/* Banner YouTube-size - NI MUY GRANDE NI MUY PEQUEÑO */
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

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #1a1a1a;
    width: 320px !important;
}

/* Títulos categoría */
.cat-title {
    font-family: 'Bebas Neue', sans-serif;
    color: #c0392b;
    font-size: 0.95rem;
    letter-spacing: 2px;
    margin: 1rem 0 0.5rem 0;
    text-transform: uppercase;
    border-bottom: 2px solid #2a2a2a;
    padding-bottom: 0.3rem;
}

/* Checkboxes */
.stCheckbox label {
    color: #d0d0d0 !important;
    font-size: 0.9rem;
}

/* Botones */
.stButton > button {
    width: 100%;
    height: 45px;
    background: linear-gradient(135deg, #c0392b, #8b0000);
    color: white;
    border: none;
    border-radius: 6px;
    font-weight: 600;
    font-size: 0.95rem;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #e74c3c, #c0392b);
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

# ═════════════════════════════════════════════════════════════════════════════
# FUNCIÓN DE EXTRACCIÓN
# ═════════════════════════════════════════════════════════════════════════════
def run_extraction(urls_to_extract, output_prefix):
    if not urls_to_extract:
        st.warning("⚠️ Selecciona al menos una fuente")
        return None, None

    st.info(f"🚀 Procesando {len(urls_to_extract)} fuentes...")
    progress_bar = st.progress(0)
    status = st.empty()
    noticias = []
    logs = []

    async def extract_all():
        for idx, (nombre, url, categoria) in enumerate(urls_to_extract):
            status.text(f"📥 [{idx+1}/{len(urls_to_extract)}] {nombre}")
            try:
                extractor = get_extractor(nombre, url, categoria)
                noticias_ext, log = await extractor.extract()
                noticias.extend(noticias_ext)
                logs.append(log)
            except Exception as e:
                logger.error(f"❌ {nombre}: {e}")
                logs.append({"source": nombre, "error": str(e), "count": 0})
            progress_bar.progress((idx + 1) / len(urls_to_extract))
        status.text("✅ ¡Completado!")

    with st.spinner("Extrayendo..."):
        try:
            asyncio.run(extract_all())
        except Exception as e:
            st.error(f"❌ Error: {e}")
            return None, None

    if noticias:
        txt_path = OUTPUT_DIR / f"{output_prefix}.txt"
        html_path = OUTPUT_DIR / f"{output_prefix}.html"
        export_txt(noticias, str(txt_path))
        export_html(noticias, str(html_path))
        return txt_path, html_path
    return None, None

# ═════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    # Logo VG
    st.markdown("""
    <div style="text-align: center; margin: 1.5rem 0;">
        <div style="font-family: 'Bebas Neue', sans-serif; font-size: 4.5rem; color: #c0392b; line-height: 1;">
            VG
        </div>
        <div style="color: #888; font-size: 0.75rem; letter-spacing: 3px; margin-top: 0.5rem;">
            VINOTINTO GALÁCTICO
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 📰 Fuentes")
    st.markdown("---")

    # Cargar fuentes
    try:
        sources_vinotinto = load_sources_vinotinto()
    except Exception as e:
        st.error(f"❌ Error: {e}")
        sources_vinotinto = {}

    # ORDEN EXACTO
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

    # Mostrar categorías EN ORDEN
    selected_sources = {}
    
    for categoria in CATEGORY_ORDER:
        if categoria not in sources_vinotinto:
            continue
            
        fuentes = sources_vinotinto[categoria]
        icon = CATEGORY_ICONS.get(categoria, "📰")
        
        # Título
        st.markdown(f'<div class="cat-title">{icon} {categoria}</div>', unsafe_allow_html=True)
        
        # Botones "Todas/Ninguna" por categoría
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("✓ Todas", key=f"btn_all_{categoria.replace(' ', '_')}", type="secondary"):
                for nombre, url in fuentes:
                    st.session_state.vg_selection[f"vg_{categoria}_{nombre}"] = True
                st.rerun()
        with col_b:
            if st.button("✗ Ninguna", key=f"btn_none_{categoria.replace(' ', '_')}", type="secondary"):
                for nombre, url in fuentes:
                    st.session_state.vg_selection[f"vg_{categoria}_{nombre}"] = False
                st.rerun()
        
        # Checkboxes individuales
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

# Banner tamaño YouTube
if banner_b64:
    st.markdown(f'''
    <div class="banner-container">
        <img src="data:image/png;base64,{banner_b64}" alt="Vinotinto Galáctico">
    </div>
    ''', unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a0810, #0d0d0d); 
                padding: 3rem; text-align: center; border: 3px solid #c0392b;
                border-radius: 8px; max-width: 800px; margin: 0 auto 2rem auto;">
        <h1 style="font-family: 'Bebas Neue', sans-serif; font-size: 3rem; color: #fff; margin: 0;">
            VINOTINTO GALÁCTICO
        </h1>
        <p style="color: #888; font-size: 1.1rem; margin: 0.5rem 0 0 0;">
            PASIÓN, FÚTBOL Y ESTRELLAS
        </p>
    </div>
    """, unsafe_allow_html=True)

# Fecha
hoy = datetime.now().strftime("%d / %m / %Y")
st.markdown(f'<div style="color: #c0392b; font-size: 0.85rem; margin: -1rem 0 1.5rem 0;">📅 HOY: {hoy}</div>', unsafe_allow_html=True)

# Botones principales
col1, col2 = st.columns(2)

with col1:
    if st.button("📰 PRENSA DEPORTIVA", key="btn_prensa"):
        html_path = BASE_DIR / "static" / "Prensa_Deportiva.html"
        if html_path.exists():
            st.info("📋 Ver static/Prensa_Deportiva.html")
        else:
            st.warning("⚠️ Crea static/Prensa_Deportiva.html")

with col2:
    if st.button("⚡ EXTRAER NOTICIAS", key="btn_extraer"):
        urls_to_extract = []
        for cat, nombres_urls in selected_sources.items():
            for nombre, url in nombres_urls.items():
                urls_to_extract.append((nombre, url, cat))
        
        txt_path, html_path = run_extraction(urls_to_extract, "noticias_vinotinto")
        
        if txt_path and html_path:
            st.success(f"✅ {len(urls_to_extract)} fuentes procesadas")
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                with open(txt_path, "rb") as f:
                    st.download_button("📥 TXT", f, "noticias_vinotinto.txt", key="dl_txt")
            with col_d2:
                with open(html_path, "rb") as f:
                    st.download_button("📥 HTML", f, "noticias_vinotinto.html", key="dl_html")

st.markdown("---")

# Footer
st.markdown('<div style="text-align: center; color: #666; font-size: 0.8rem; margin-top: 2rem;">⚽ Vinotinto Galáctico v7.0</div>', unsafe_allow_html=True)