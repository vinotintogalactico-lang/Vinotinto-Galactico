"""
VINOTINTO GALÁCTICO NEWS EXTRACTOR v8.0
FINAL - Logo real + Banner normal + Noticias completas en centro
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
# CSS
# ═════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;600&display=swap');

/* Banner tamaño YouTube - NI GRANDE NI PEQUEÑO */
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
    width: 300px !important;
}

/* Títulos categoría */
.cat-title {
    font-family: 'Bebas Neue', sans-serif;
    color: #c0392b;
    font-size: 0.9rem;
    letter-spacing: 2px;
    margin: 1rem 0 0.5rem 0;
    text-transform: uppercase;
    border-bottom: 2px solid #2a2a2a;
    padding-bottom: 0.3rem;
}

/* Checkboxes */
.stCheckbox label {
    color: #d0d0d0 !important;
    font-size: 0.85rem;
}

/* Botones principales */
.stButton > button {
    height: 45px;
    background: linear-gradient(135deg, #c0392b, #8b0000);
    color: white;
    border: none;
    border-radius: 6px;
    font-weight: 600;
    font-size: 0.9rem;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #e74c3c, #c0392b);
}

/* Noticias - Centro */
.news-display {
    max-width: 1000px;
    margin: 2rem auto;
    padding: 2rem;
    background: #1a1a1a;
    border-radius: 8px;
    border: 2px solid #c0392b;
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
    font-size: 1.2rem;
}
.news-meta {
    color: #888;
    font-size: 0.85rem;
    margin-bottom: 1rem;
}
.news-content {
    color: #d0d0d0;
    line-height: 1.6;
    text-align: justify;
}
</style>
""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# CARGAR LOGO Y BANNER
# ═════════════════════════════════════════════════════════════════════════════
def _b64(path: Path) -> str:
    try:
        if path.exists():
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except Exception as e:
        logger.warning(f"No se cargó {path}: {e}")
    return ""

logo_b64 = _b64(BASE_DIR / "Logo.jpg")
banner_b64 = _b64(BASE_DIR / "banner-vinotinto.png")

# ═════════════════════════════════════════════════════════════════════════════
# INICIALIZAR SESSION STATE
# ═════════════════════════════════════════════════════════════════════════════
if 'vg_selection' not in st.session_state:
    st.session_state.vg_selection = {}
if 'extraer_clicked' not in st.session_state:
    st.session_state.extraer_clicked = False
if 'noticias_extraidas' not in st.session_state:
    st.session_state.noticias_extraidas = []

# ═════════════════════════════════════════════════════════════════════════════
# FUNCIÓN DE EXTRACCIÓN
# ═════════════════════════════════════════════════════════════════════════════
def run_extraction(urls_to_extract):
    if not urls_to_extract:
        st.warning("⚠️ Selecciona al menos una fuente")
        return []

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
                logger.info(f"✅ {nombre}: {len(noticias_ext)} noticias")
            except Exception as e:
                logger.error(f"❌ {nombre}: {e}")
                logs.append({"source": nombre, "error": str(e), "count": 0})
            progress_bar.progress((idx + 1) / len(urls_to_extract))
        status.text("✅ ¡Extracción completada!")

    with st.spinner("Extrayendo noticias..."):
        try:
            asyncio.run(extract_all())
        except Exception as e:
            st.error(f"❌ Error: {e}")
            return []

    if noticias:
        txt_path = OUTPUT_DIR / "noticias_vinotinto.txt"
        html_path = OUTPUT_DIR / "noticias_vinotinto.html"
        export_txt(noticias, str(txt_path))
        export_html(noticias, str(html_path))
        st.success(f"✅ {len(noticias)} noticias extraídas")
        
        col1, col2 = st.columns(2)
        with col1:
            with open(txt_path, "rb") as f:
                st.download_button("📥 Descargar TXT", f, "noticias_vinotinto.txt", key="dl_txt")
        with col2:
            with open(html_path, "rb") as f:
                st.download_button("📥 Descargar HTML", f, "noticias_vinotinto.html", key="dl_html")
    
    return noticias

# ═════════════════════════════════════════════════════════════════════════════
# SIDEBAR - SOLO CHECKBOXES
# ═════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    # Logo REAL (Logo.jpg)
    if logo_b64:
        st.markdown(f'''
        <div style="text-align: center; margin: 1rem 0;">
            <img src="data:image/jpg;base64,{logo_b64}" style="width: 120px; height: auto; border-radius: 8px;">
        </div>
        ''', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align: center; margin: 1rem 0;">
            <div style="font-family: 'Bebas Neue', sans-serif; font-size: 4rem; color: #c0392b;">VG</div>
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

    # Mostrar categorías EN ORDEN - SOLO CHECKBOXES
    selected_sources = {}
    
    for categoria in CATEGORY_ORDER:
        if categoria not in sources_vinotinto:
            continue
            
        fuentes = sources_vinotinto[categoria]
        icon = CATEGORY_ICONS.get(categoria, "📰")
        
        # Título
        st.markdown(f'<div class="cat-title">{icon} {categoria}</div>', unsafe_allow_html=True)
        
        # Checkboxes individuales - SIN BOTONES
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

# Banner NORMAL
if banner_b64:
    st.markdown(f'''
    <div class="banner-container">
        <img src="data:image/png;base64,{banner_b64}" alt="Vinotinto Galáctico">
    </div>
    ''', unsafe_allow_html=True)

# Fecha
hoy = datetime.now().strftime("%d / %m / %Y")
st.markdown(f'<div style="color: #c0392b; font-size: 0.85rem; margin: -1rem 0 1rem 0; text-align: center;">📅 HOY: {hoy}</div>', unsafe_allow_html=True)

# TRES BOTONES EN UNA FILA - ALINEADOS
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🏆 MUNDIAL 2026", key="btn_mundial", use_container_width=True):
        st.session_state.show_mundial = not st.session_state.get('show_mundial', False)
        st.rerun()

with col2:
    if st.button("📰 PRENSA DEPORTIVA", key="btn_prensa", use_container_width=True):
        html_path = BASE_DIR / "static" / "Prensa_Deportiva.html"
        if html_path.exists():
            st.info("📋 Ver static/Prensa_Deportiva.html")
        else:
            st.warning("⚠️ Crea static/Prensa_Deportiva.html")

with col3:
    if st.button("⚡ EXTRAER NOTICIAS", key="btn_extraer", use_container_width=True):
        st.session_state.extraer_clicked = True
        urls_to_extract = []
        for cat, nombres_urls in selected_sources.items():
            for nombre, url in nombres_urls.items():
                urls_to_extract.append((nombre, url, cat))
        st.session_state.noticias_extraidas = run_extraction(urls_to_extract)
        st.rerun()

st.markdown("---")

# Mostrar Mundial si está activado
if st.session_state.get('show_mundial', False):
    st.markdown("### 🌍 MUNDIAL 2026")
    try:
        sources_mundial = load_sources_mundial()
        if "Mundial Global" in sources_mundial:
            st.info(f"🏆 {len(sources_mundial['Mundial Global'])} fuentes disponibles")
    except Exception as e:
        st.error(f"Error: {e}")

# MOSTRAR NOTICIAS COMPLETAS EN EL CENTRO
if st.session_state.noticias_extraidas:
    st.markdown("### 📰 NOTICIAS EXTRAÍDAS")
    st.markdown("---")
    
    for idx, noticia in enumerate(st.session_state.noticias_extraidas, 1):
        st.markdown(f"""
        <div class="news-item">
            <h3>{noticia.get('titulo', 'Sin título')}</h3>
            <div class="news-meta">
                <strong>Fuente:</strong> {noticia.get('fuente', 'Desconocida')} | 
                <strong>Categoría:</strong> {noticia.get('categoria', '')} | 
                <strong>Fecha:</strong> {noticia.get('fecha', 'N/A')}
            </div>
            <div class="news-content">
                {noticia.get('resumen', noticia.get('content', 'Sin contenido'))}
            </div>
        </div>
        """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown('<div style="text-align: center; color: #666; font-size: 0.8rem; margin-top: 2rem;">⚽ Vinotinto Galáctico v8.0</div>', unsafe_allow_html=True)