"""
VINOTINTO GALÁCTICO NEWS EXTRACTOR v5.0
Diseño ORIGINAL con sidebar - Como en la captura
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
# CONFIGURACIÓN
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
    st.error(f"❌ Error importando: {e}")
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
# CSS - Banner GRANDE y layout original
# ═════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;600&display=swap');

/* Banner GRANDE como YouTube */
.banner-container {
    width: 100%;
    margin: 0 auto 2rem auto;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 8px 32px rgba(192, 57, 43, 0.3);
}
.banner-container img {
    width: 100%;
    height: auto;
    display: block;
}

/* Botones principales */
.main-button {
    height: 50px;
    font-size: 1rem;
    font-weight: 600;
    border: none;
    border-radius: 8px;
    transition: all 0.3s;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #1a1a1a;
    width: 320px !important;
}
section[data-testid="stSidebar"] .stExpander {
    background: #252525;
    border-radius: 8px;
    margin-bottom: 0.5rem;
}

/* Títulos de categoría en sidebar */
.category-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 0.9rem;
    color: #c0392b;
    letter-spacing: 2px;
    margin: 0.5rem 0;
    text-transform: uppercase;
}

/* Noticias */
.news-container {
    max-height: none;
    overflow-y: visible;
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
        logger.warning(f"No se pudo cargar {path}: {e}")
    return ""

banner_b64 = _b64(BASE_DIR / "banner-vinotinto.png")

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
                logger.info(f"✅ {nombre}: {len(noticias_ext)} noticias")
            except Exception as e:
                logger.error(f"❌ Error en {nombre}: {e}")
                logs.append({"source": nombre, "error": str(e), "count": 0})
            progress_bar.progress((idx + 1) / len(urls_to_extract))
        status.text("✅ ¡Extracción completada!")

    with st.spinner("Extrayendo noticias..."):
        try:
            asyncio.run(extract_all())
        except Exception as e:
            st.error(f"❌ Error: {e}")
            logger.exception(e)
            return None, None

    if noticias:
        txt_path = OUTPUT_DIR / f"{output_prefix}.txt"
        html_path = OUTPUT_DIR / f"{output_prefix}.html"
        export_txt(noticias, str(txt_path))
        export_html(noticias, str(html_path))
        return txt_path, html_path
    return None, None

# ═════════════════════════════════════════════════════════════════════════════
# SIDEBAR - TODAS LAS CATEGORÍAS
# ═════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    # Logo VG
    st.markdown("""
    <div style="text-align: center; margin: 1rem 0 2rem 0;">
        <div style="font-family: 'Bebas Neue', sans-serif; font-size: 4rem; color: #c0392b; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">
            VG
        </div>
        <div style="color: #888; font-size: 0.8rem;">VINOTINTO GALÁCTICO</div>
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

    # Inicializar session state
    if "vg_selection" not in st.session_state:
        st.session_state.vg_selection = {}

    # ORDEN EXACTO de categorías
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
        "Vinotinto Femenina": "🇻🇪",
        "Liga FUTVE": "🇻",
    }

    # Mostrar categorías EN ORDEN
    selected_sources = {}
    
    for categoria in CATEGORY_ORDER:
        if categoria not in sources_vinotinto:
            continue
            
        fuentes = sources_vinotinto[categoria]
        icon = CATEGORY_ICONS.get(categoria, "📰")
        
        # Título de categoría
        st.markdown(f'<div class="category-title">{icon} {categoria}</div>', unsafe_allow_html=True)
        
        # Checkbox "Seleccionar todo" para esta categoría
        select_all_key = f"select_all_{categoria.replace(' ', '_')}"
        if st.checkbox("□ Seleccionar todo", key=select_all_key):
            for nombre, url in fuentes:
                st.session_state.vg_selection[f"vg_{categoria}_{nombre}"] = True
            st.rerun()
        
        # Checkboxes de fuentes
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
        
        st.markdown("")  # Espacio

# ═════════════════════════════════════════════════════════════════════════════
# ÁREA PRINCIPAL
# ═════════════════════════════════════════════════════════════════════════════

# Banner GRANDE
if banner_b64:
    st.markdown(f'''
    <div class="banner-container">
        <img src="data:image/png;base64,{banner_b64}" alt="Vinotinto Galáctico">
    </div>
    ''', unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a0810 0%, #0d0d0d 100%); 
                padding: 3rem; border-radius: 12px; text-align: center; margin-bottom: 2rem;
                border: 3px solid #c0392b;">
        <h1 style="font-family: 'Bebas Neue', sans-serif; font-size: 3rem; color: #fff; margin: 0;">
            VINOTINTO GALÁCTICO
        </h1>
        <p style="color: #888; margin: 0.5rem 0 0 0;">NEWS EXTRACTOR</p>
    </div>
    """, unsafe_allow_html=True)

# Fecha
from datetime import datetime
hoy = datetime.now().strftime("%d / %m / %Y")
st.markdown(f'<div style="color: #c0392b; font-size: 0.9rem; margin: -1rem 0 1rem 0;">📅 HOY: {hoy}</div>', unsafe_allow_html=True)

# Botones principales - 3 COLUMNAS
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🏆 MUNDIAL 2026", key="btn_mundial_tab", use_container_width=True, className="main-button"):
        st.session_state.show_mundial = not st.session_state.get('show_mundial', False)
        st.rerun()

with col2:
    if st.button("📰 PRENSA DEPORTIVA", key="btn_prensa", use_container_width=True, className="main-button"):
        # Abrir HTML en nueva pestaña (simulado)
        st.info("📋 Accesos directos en el sidebar inferior")

with col3:
    if st.button("⚡ EXTRAER NOTICIAS", key="btn_extraer", use_container_width=True, className="main-button"):
        # Recopilar URLs seleccionadas del sidebar
        urls_to_extract = []
        for cat, nombres_urls in selected_sources.items():
            for nombre, url in nombres_urls.items():
                urls_to_extract.append((nombre, url, cat))
        
        txt_path, html_path = run_extraction(urls_to_extract, "noticias_vinotinto")
        
        if txt_path and html_path:
            st.success(f"✅ Extracción completada")
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                with open(txt_path, "rb") as f:
                    st.download_button("📥 Descargar TXT", f, "noticias_vinotinto.txt", key="dl_txt")
            with col_d2:
                with open(html_path, "rb") as f:
                    st.download_button("📥 Descargar HTML", f, "noticias_vinotinto.html", key="dl_html")

st.markdown("---")

# Mostrar sección del Mundial si está activada
if st.session_state.get('show_mundial', False):
    st.markdown("### 🌍 MUNDIAL 2026")
    try:
        sources_mundial = load_sources_mundial()
        if "Mundial Global" in sources_mundial:
            st.info(f"🏆 {len(sources_mundial['Mundial Global'])} fuentes disponibles")
            # Aquí irían los checkboxes del mundial (simplificado)
    except Exception as e:
        st.error(f"Error cargando Mundial: {e}")

# Instrucciones
st.markdown("""
<div style="text-align: center; color: #888; margin-top: 2rem; padding: 1rem; background: #1a1a1a; border-radius: 8px;">
    <p style="margin: 0;">SELECCIONA LAS FUENTES EN EL SIDEBAR Y PULSA <strong style="color: #c0392b;">EXTRAER</strong></p>
    <p style="margin: 0.5rem 0 0 0; font-size: 0.85rem;">Solo se extraerán noticias del día de hoy · Máximo 3 por fuente</p>
</div>
""", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown('<div style="text-align: center; color: #666; font-size: 0.8rem;">⚽ Vinotinto Galáctico News Extractor v5.0</div>', unsafe_allow_html=True)