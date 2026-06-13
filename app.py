"""
VINOTINTO GALÁCTICO NEWS EXTRACTOR v3.0
Versión estable - Tabs: Panel Prensa | Vinotinto | Mundial
"""
import os
import sys
import time
import asyncio
import base64
import logging
import uuid
from pathlib import Path
from datetime import datetime

import streamlit as st

# ═════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN INICIAL
# ═════════════════════════════════════════════════════════════════════════════
os.environ['TZ'] = 'America/Caracas'
if hasattr(time, 'tzset'):
    time.tzset()

# RUTA BASE ABSOLUTA (CRÍTICO PARA LA NUBE)
BASE_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ═════════════════════════════════════════════════════════════════════════════
# IMPORTACIONES DEL PROYECTO
# ═════════════════════════════════════════════════════════════════════════════
try:
    from core.excel_reader import load_sources_vinotinto, load_sources_mundial
    from core.txt_exporter import export_txt
    from core.html_exporter import export_html
    from extractores.factory import get_extractor
except ImportError as e:
    st.error(f"❌ Error importando módulos del proyecto: {e}")
    st.stop()

# ═════════════════════════════════════════════════════════════════════════════
# CONFIG DE PÁGINA
# ═════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="VG Extractor | Vinotinto + Mundial",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

CATEGORY_ICONS = {
    "Real Madrid Masculino": "👑",
    "Real Madrid Femenino": "👑",
    "LaLiga": "🇪🇸",
    "Selección Española Masculina": "🇪🇸",
    "Selección Española Femenina": "🇪🇸",
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
    display: flex;
    align-items: center;
    justify-content: space-between;
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
# TABS PRINCIPALES
# ═════════════════════════════════════════════════════════════════════════════
tab_panel, tab_vinotinto, tab_mundial = st.tabs([
    "📰 PANEL DE PRENSA",
    "🔴 VINOTINTO GALÁCTICO",
    "🌍 MUNDIAL 2026"
])

# ═════════════════════════════════════════════════════════════════════════════
# FUNCIÓN GENÉRICA DE EXTRACCIÓN
# ═════════════════════════════════════════════════════════════════════════════
def run_extraction(urls_to_extract, output_prefix):
    """Ejecuta la extracción de noticias de forma asíncrona"""
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
            st.error(f"❌ Error fatal en extracción: {e}")
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
        st.info("ℹ️ No se encontraron noticias del día en las fuentes seleccionadas")

    # Mostrar logs
    with st.expander("📊 Ver log detallado"):
        for log in logs:
            if "error" in log:
                st.error(f"❌ {log['source']}: {log['error']}")
            else:
                st.success(f"✅ {log.get('source', '?')}: {log.get('count', 0)} noticias")

# ═════════════════════════════════════════════════════════════════════════════
# TAB 1: PANEL DE PRENSA
# ═════════════════════════════════════════════════════════════════════════════
with tab_panel:
    st.markdown('<div class="vg-titlebar"><h1>📰 PANEL DE PRENSA</h1></div>', unsafe_allow_html=True)
    st.info("🔗 Accesos directos a todas las fuentes de prensa deportiva")

    html_path = BASE_DIR / "static" / "Prensa_Deportiva.html"
    if html_path.exists():
        try:
            with open(html_path, "r", encoding="utf-8") as f:
                st.markdown(f.read(), unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error al leer HTML: {e}")
    else:
        st.warning(f"⚠️ No se encontró `static/Prensa_Deportiva.html`. Crea la carpeta `static/` y copia el archivo ahí.")

# ═════════════════════════════════════════════════════════════════════════════
# TAB 2: VINOTINTO GALÁCTICO
# ═════════════════════════════════════════════════════════════════════════════
with tab_vinotinto:
    st.markdown('<div class="vg-titlebar"><h1>🔴 VINOTINTO GALÁCTICO</h1></div>', unsafe_allow_html=True)

    if banner_b64:
        st.markdown(f'<div style="text-align:center;"><img src="data:image/png;base64,{banner_b64}" style="max-width:100%; max-height:220px; border-radius:8px;"></div>', unsafe_allow_html=True)

    try:
        sources_vinotinto = load_sources_vinotinto()
    except Exception as e:
        st.error(f"❌ Error al cargar Excel Vinotinto: {e}")
        logger.exception(e)
        sources_vinotinto = {}

    if sources_vinotinto:
        st.markdown("### 📋 Selecciona las fuentes a extraer")

        # Botones de selección rápida
        col_sel1, col_sel2, col_sel3 = st.columns(3)
        with col_sel1:
            select_all_vg = st.button("✅ Seleccionar todo", key="sel_all_vg")
        with col_sel2:
            deselect_all_vg = st.button("❌ Deseleccionar todo", key="desel_all_vg")
        with col_sel3:
            total_f = sum(len(f) for f in sources_vinotinto.values())
            st.info(f"📊 {len(sources_vinotinto)} categorías · {total_f} fuentes")

        # Inicializar session state
        if "vg_checks" not in st.session_state:
            st.session_state.vg_checks = {}

        # Aplicar selección/deselección masiva
        if select_all_vg:
            for cat, fuentes in sources_vinotinto.items():
                for nombre, url in fuentes:
                    st.session_state.vg_checks[f"vg_{cat}_{nombre}"] = True
            st.rerun()
        if deselect_all_vg:
            st.session_state.vg_checks = {}
            st.rerun()

        selected_vinotinto = {}
        for categoria, fuentes in sorted(sources_vinotinto.items()):
            icon = CATEGORY_ICONS.get(categoria, "📰")
            with st.expander(f"{icon} **{categoria}** ({len(fuentes)} fuentes)", expanded=False):
                selected_vinotinto[categoria] = {}
                cols = st.columns(2)
                for idx, (nombre, url) in enumerate(fuentes):
                    with cols[idx % 2]:
                        check_key = f"vg_{categoria}_{nombre}"
                        checked = st.checkbox(
                            f"{nombre}",
                            key=check_key,
                            value=st.session_state.vg_checks.get(check_key, False)
                        )
                        if checked:
                            selected_vinotinto[categoria][nombre] = url

        st.markdown("---")
        if st.button("⚡ EXTRAER NOTICIAS VINOTINTO", key="btn_vg", use_container_width=True, type="primary"):
            urls_to_extract = []
            for cat, nombres_urls in selected_vinotinto.items():
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
    st.warning("⚠️ Contenido temporal disponible hasta el **19 de Julio de 2026**")

    try:
        sources_mundial = load_sources_mundial()
    except Exception as e:
        st.error(f"❌ Error al cargar Excel Mundial: {e}")
        logger.exception(e)
        sources_mundial = {}

    if sources_mundial:
        st.markdown("### 📋 Fuentes del Mundial")

        col_sel1, col_sel2, col_sel3 = st.columns(3)
        with col_sel1:
            select_all_m = st.button("✅ Seleccionar todo", key="sel_all_m")
        with col_sel2:
            deselect_all_m = st.button("❌ Deseleccionar todo", key="desel_all_m")
        with col_sel3:
            total_m = sum(len(f) for f in sources_mundial.values())
            st.info(f"🏆 {total_m} fuentes disponibles")

        if "mundial_checks" not in st.session_state:
            st.session_state.mundial_checks = {}

        if select_all_m:
            for cat, fuentes in sources_mundial.items():
                for nombre, url in fuentes:
                    st.session_state.mundial_checks[f"mundial_{cat}_{nombre}"] = True
            st.rerun()
        if deselect_all_m:
            st.session_state.mundial_checks = {}
            st.rerun()

        selected_mundial = {}
        for categoria, fuentes in sources_mundial.items():
            icon = CATEGORY_ICONS.get(categoria, "🌍")
            with st.expander(f"{icon} **{categoria}** ({len(fuentes)} fuentes)", expanded=True):
                selected_mundial[categoria] = {}
                cols = st.columns(3)
                for idx, (nombre, url) in enumerate(fuentes):
                    with cols[idx % 3]:
                        check_key = f"mundial_{categoria}_{nombre}"
                        checked = st.checkbox(
                            f"{nombre}",
                            key=check_key,
                            value=st.session_state.mundial_checks.get(check_key, False)
                        )
                        if checked:
                            selected_mundial[categoria][nombre] = url

        st.markdown("---")
        if st.button("⚡ EXTRAER NOTICIAS MUNDIAL", key="btn_mundial", use_container_width=True, type="primary"):
            urls_to_extract = []
            for cat, nombres_urls in selected_mundial.items():
                for nombre, url in nombres_urls.items():
                    urls_to_extract.append((nombre, url, cat))
            run_extraction(urls_to_extract, "noticias_mundial")
    else:
        st.error("❌ No se cargaron fuentes. Verifica `data/Prensa_Mundial_2026_ListaEnlaces.xlsx`")

# ═════════════════════════════════════════════════════════════════════════════
# FOOTER
# ═════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown('<div style="text-align:center; color:#888; font-size:0.85em;">⚽ Vinotinto Galáctico News Extractor v3.0 · Estable</div>', unsafe_allow_html=True)