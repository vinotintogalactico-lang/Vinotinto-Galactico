"""
VINOTINTO GALÁCTICO NEWS EXTRACTOR v4.0
Orden correcto + Botones funcionales + Sin errores
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
# CONFIGURACIÓN INICIAL
# ═════════════════════════════════════════════════════════════════════════════
BASE_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ═════════════════════════════════════════════════════════════════════════════
# IMPORTACIONES
# ═════════════════════════════════════════════════════════════════════════════
try:
    from core.excel_reader import load_sources_vinotinto, load_sources_mundial
    from core.txt_exporter import export_txt
    from core.html_exporter import export_html
    from extractores.factory import get_extractor
except ImportError as e:
    st.error(f"❌ Error importando módulos: {e}")
    st.stop()

# ═════════════════════════════════════════════════════════════════════════════
# CONFIG DE PÁGINA - SIN SIDEBAR
# ═════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="VG Extractor | Vinotinto + Mundial",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ═════════════════════════════════════════════════════════════════════════════
# ORDEN EXACTO DE CATEGORÍAS (SEGÚN EL EXCEL)
# ═════════════════════════════════════════════════════════════════════════════
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
    "Liga FUTVE": "🇻🇪",
    "Mundial Global": "🌍",
}

# ═════════════════════════════════════════════════════════════════════════════
# CSS
# ═════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;600&display=swap');

.vg-titlebar {
    background: linear-gradient(135deg, #0d0d0d 0%, #1a0810 50%, #0d0d0d 100%);
    border-bottom: 3px solid #c0392b;
    padding: 1rem 1.5rem;
    margin: 0 -1rem 1.5rem -1rem;
}
.vg-titlebar h1 {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.2rem;
    color: #fff;
    letter-spacing: 3px;
    margin: 0;
}
.stButton>button {
    background: linear-gradient(135deg, #c0392b, #8b0000);
    color: white;
    font-weight: 600;
    border: none;
    padding: 0.6rem 1.5rem;
    border-radius: 6px;
}
.stButton>button:hover {
    background: linear-gradient(135deg, #e74c3c, #c0392b);
}
.category-header {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.1rem;
    letter-spacing: 2px;
    color: #c0392b;
    margin: 1rem 0 0.5rem 0;
    padding-bottom: 0.3rem;
    border-bottom: 2px solid #2a2a2a;
}
</style>
""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# UTILIDADES
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
    """Ejecuta la extracción de noticias"""
    if not urls_to_extract:
        st.warning("⚠️ Selecciona al menos una fuente")
        return

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
            st.error(f"❌ Error fatal: {e}")
            logger.exception(e)
            return

    if noticias:
        txt_path = OUTPUT_DIR / f"{output_prefix}.txt"
        html_path = OUTPUT_DIR / f"{output_prefix}.html"
        export_txt(noticias, str(txt_path))
        export_html(noticias, str(html_path))

        st.success(f"✅ {len(noticias)} noticias extraídas de {len(urls_to_extract)} fuentes")

        col1, col2 = st.columns(2)
        with col1:
            with open(txt_path, "rb") as f:
                st.download_button("📥 Descargar TXT", f, file_name=f"{output_prefix}.txt", key=f"dl_txt_{output_prefix}")
        with col2:
            with open(html_path, "rb") as f:
                st.download_button("📥 Descargar HTML", f, file_name=f"{output_prefix}.html", key=f"dl_html_{output_prefix}")
    else:
        st.info("ℹ️ No se encontraron noticias del día")

    with st.expander("📊 Ver log detallado"):
        for log in logs:
            if "error" in log:
                st.error(f"❌ {log['source']}: {log['error']}")
            else:
                st.success(f"✅ {log.get('source', '?')}: {log.get('count', 0)} noticias")

# ═════════════════════════════════════════════════════════════════════════════
# TABS PRINCIPALES
# ═════════════════════════════════════════════════════════════════════════════
tab_panel, tab_vinotinto, tab_mundial = st.tabs([
    "📰 PANEL DE PRENSA",
    "🔴 VINOTINTO GALÁCTICO",
    "🌍 MUNDIAL 2026"
])

# ═════════════════════════════════════════════════════════════════════════════
# TAB 1: PANEL DE PRENSA
# ═════════════════════════════════════════════════════════════════════════════
with tab_panel:
    st.markdown('<div class="vg-titlebar"><h1>📰 PANEL DE PRENSA</h1></div>', unsafe_allow_html=True)
    st.info("🔗 Accesos directos a todas las fuentes")

    html_path = BASE_DIR / "static" / "Prensa_Deportiva.html"
    if html_path.exists():
        try:
            with open(html_path, "r", encoding="utf-8") as f:
                st.markdown(f.read(), unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error al leer HTML: {e}")
    else:
        st.warning("⚠️ No se encontró `static/Prensa_Deportiva.html`")

# ═════════════════════════════════════════════════════════════════════════════
# TAB 2: VINOTINTO GALÁCTICO
# ═════════════════════════════════════════════════════════════════════════════
with tab_vinotinto:
    st.markdown('<div class="vg-titlebar"><h1>🔴 VINOTINTO GALÁCTICO</h1></div>', unsafe_allow_html=True)

    if banner_b64:
        st.markdown(f'<div style="text-align:center;"><img src="data:image/png;base64,{banner_b64}" style="max-width:100%; max-height:220px; border-radius:8px;"></div>', unsafe_allow_html=True)

    # Cargar fuentes
    try:
        all_sources = load_sources_vinotinto()
    except Exception as e:
        st.error(f"❌ Error al cargar Excel: {e}")
        logger.exception(e)
        all_sources = {}

    if all_sources:
        st.markdown("### 📋 Selecciona las fuentes")

        # Inicializar session state para checkboxes
        if "vg_selection" not in st.session_state:
            st.session_state.vg_selection = {}

        # Botones globales
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
        with col_btn1:
            if st.button("✅ Seleccionar TODAS", key="sel_all_global"):
                for cat in CATEGORY_ORDER:
                    if cat in all_sources:
                        for nombre, url in all_sources[cat]:
                            st.session_state.vg_selection[f"vg_{cat}_{nombre}"] = True
                st.rerun()
        with col_btn2:
            if st.button("❌ Deseleccionar TODAS", key="desel_all_global"):
                st.session_state.vg_selection = {}
                st.rerun()
        with col_btn3:
            total = sum(len(f) for f in all_sources.values())
            st.info(f"📊 {len(all_sources)} categorías · {total} fuentes")

        st.markdown("---")

        # Mostrar categorías EN ORDEN
        selected_sources = {}
        for categoria in CATEGORY_ORDER:
            if categoria not in all_sources:
                continue
                
            fuentes = all_sources[categoria]
            icon = CATEGORY_ICONS.get(categoria, "📰")
            
            st.markdown(f'<div class="category-header">{icon} {categoria.upper()} ({len(fuentes)} fuentes)</div>', unsafe_allow_html=True)
            
            # Botones por categoría
            col_sel1, col_sel2 = st.columns(2)
            with col_sel1:
                if st.button(f"✅ Todas", key=f"sel_{categoria}"):
                    for nombre, url in fuentes:
                        st.session_state.vg_selection[f"vg_{categoria}_{nombre}"] = True
                    st.rerun()
            with col_sel2:
                if st.button(f"❌ Ninguna", key=f"desel_{categoria}"):
                    for nombre, url in fuentes:
                        st.session_state.vg_selection[f"vg_{categoria}_{nombre}"] = False
                    st.rerun()

            # Checkboxes en 2 columnas
            cols = st.columns(2)
            selected_sources[categoria] = {}
            for idx, (nombre, url) in enumerate(fuentes):
                with cols[idx % 2]:
                    check_key = f"vg_{categoria}_{nombre}"
                    checked = st.checkbox(
                        f"{nombre}",
                        key=check_key,
                        value=st.session_state.vg_selection.get(check_key, False)
                    )
                    if checked:
                        selected_sources[categoria][nombre] = url

            st.markdown("")  # Espacio

        # Botón de extracción
        st.markdown("---")
        if st.button("⚡ EXTRAER NOTICIAS VINOTINTO", key="btn_vg", use_container_width=True, type="primary"):
            urls_to_extract = []
            for cat, nombres_urls in selected_sources.items():
                for nombre, url in nombres_urls.items():
                    urls_to_extract.append((nombre, url, cat))
            run_extraction(urls_to_extract, "noticias_vinotinto")
    else:
        st.error("❌ No se cargaron fuentes. Verifica `data/Prensa Deportiva.xlsx`")

# ═════════════════════════════════════════════════════════════════════════════
# TAB 3: MUNDIAL 2026
# ═════════════════════════════════════════════════════════════════════════════
with tab_mundial:
    st.markdown('<div class="vg-titlebar"><h1>🌍 MUNDIAL 2026</h1></div>', unsafe_allow_html=True)
    st.warning("⚠️ Contenido temporal hasta el **19 de Julio de 2026**")

    try:
        sources_mundial = load_sources_mundial()
    except Exception as e:
        st.error(f"❌ Error al cargar Excel: {e}")
        logger.exception(e)
        sources_mundial = {}

    if sources_mundial:
        st.markdown("### 📋 Fuentes del Mundial")

        if "mundial_selection" not in st.session_state:
            st.session_state.mundial_selection = {}

        # Botones globales
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
        with col_btn1:
            if st.button("✅ Seleccionar TODAS", key="sel_all_mundial"):
                for cat, fuentes in sources_mundial.items():
                    for nombre, url in fuentes:
                        st.session_state.mundial_selection[f"mundial_{cat}_{nombre}"] = True
                st.rerun()
        with col_btn2:
            if st.button("❌ Deseleccionar TODAS", key="desel_all_mundial"):
                st.session_state.mundial_selection = {}
                st.rerun()
        with col_btn3:
            total = sum(len(f) for f in sources_mundial.values())
            st.info(f"🏆 {total} fuentes")

        st.markdown("---")

        selected_mundial = {}
        for categoria, fuentes in sources_mundial.items():
            icon = CATEGORY_ICONS.get(categoria, "🌍")
            st.markdown(f'<div class="category-header">{icon} {categoria.upper()} ({len(fuentes)} fuentes)</div>', unsafe_allow_html=True)
            
            # Botones por categoría
            col_sel1, col_sel2 = st.columns(2)
            with col_sel1:
                if st.button(f"✅ Todas", key=f"sel_mundial_{categoria}"):
                    for nombre, url in fuentes:
                        st.session_state.mundial_selection[f"mundial_{categoria}_{nombre}"] = True
                    st.rerun()
            with col_sel2:
                if st.button(f"❌ Ninguna", key=f"desel_mundial_{categoria}"):
                    for nombre, url in fuentes:
                        st.session_state.mundial_selection[f"mundial_{categoria}_{nombre}"] = False
                    st.rerun()

            # Checkboxes en 3 columnas
            cols = st.columns(3)
            selected_mundial[categoria] = {}
            for idx, (nombre, url) in enumerate(fuentes):
                with cols[idx % 3]:
                    check_key = f"mundial_{categoria}_{nombre}"
                    checked = st.checkbox(
                        f"{nombre}",
                        key=check_key,
                        value=st.session_state.mundial_selection.get(check_key, False)
                    )
                    if checked:
                        selected_mundial[categoria][nombre] = url

            st.markdown("")

        st.markdown("---")
        if st.button("⚡ EXTRAER NOTICIAS MUNDIAL", key="btn_mundial", use_container_width=True, type="primary"):
            urls_to_extract = []
            for cat, nombres_urls in selected_mundial.items():
                for nombre, url in nombres_urls.items():
                    urls_to_extract.append((nombre, url, cat))
            run_extraction(urls_to_extract, "noticias_mundial")
    else:
        st.error("❌ No se cargaron fuentes del Mundial")

# ═════════════════════════════════════════════════════════════════════════════
# FOOTER
# ═════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown('<div style="text-align:center; color:#888; font-size:0.85em;">⚽ Vinotinto Galáctico News Extractor v4.0</div>', unsafe_allow_html=True)