import os
import sys
import time
from pathlib import Path
import asyncio
import base64
import logging
from datetime import datetime
import uuid

import streamlit as st

# ═════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE RUTAS (CRÍTICO PARA LA NUBE)
# ═════════════════════════════════════════════════════════════════════════════

BASE_DIR = Path(__file__).parent
os.environ['TZ'] = 'America/Caracas'
if hasattr(time, 'tzset'):
    time.tzset()

# Crear carpetas si no existen
Path(BASE_DIR / "output").mkdir(exist_ok=True)
Path(BASE_DIR / "logs").mkdir(exist_ok=True)

# ═════════════════════════════════════════════════════════════════════════════
# IMPORTACIONES
# ═════════════════════════════════════════════════════════════════════════════

from core.excel_reader import load_sources_vinotinto, load_sources_mundial
from core.txt_exporter import export_txt
from core.html_exporter import export_html
from extractores.factory import get_extractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ═════════════════════════════════════════════════════════════════════════════
# CONFIG
# ═════════════════════════════════════════════════════════════════════════════

CATEGORY_ICONS = {
    "Real Madrid Masculino": "👑",
    "Real Madrid Femenino": "👑",
    "LaLiga": "🇪🇸",
    "Selección Española Masculina": "🇪🇸",
    "Selección Española Femenina": "🇪",
    "Vinotinto Masculina": "🇻🇪",
    "Vinotinto Femenina": "🇻",
    "Liga FUTVE": "🇻🇪",
}

st.set_page_config(
    page_title="VG Extractor | Vinotinto + Mundial",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ═════════════════════════════════════════════════════════════════════════════
# CARGAR IMÁGENES
# ═════════════════════════════════════════════════════════════════════════════

def _b64(path: str) -> str:
    """Convierte archivo a base64 de forma segura"""
    try:
        full_path = BASE_DIR / path
        if full_path.exists():
            with open(full_path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except Exception as e:
        logger.warning(f"No se pudo cargar {path}: {e}")
    return ""

banner_b64 = _b64("banner-vinotinto.png")

# ═════════════════════════════════════════════════════════════════════════════
# TABS PRINCIPALES
# ═════════════════════════════════════════════════════════════════════════════

tab_panel, tab_vinotinto, tab_mundial = st.tabs([
    "📰 PANEL DE PRENSA",
    "🔴 VINOTINTO GALÁCTICO",
    "🟢 MUNDIAL 2026"
])

# ═════════════════════════════════════════════════════════════════════════════
# TAB 1: PANEL DE PRENSA DEPORTIVA
# ═════════════════════════════════════════════════════════════════════════════

with tab_panel:
    st.markdown("### 📰 PANEL DE PRENSA - ACCESOS DIRECTOS")
    st.info("🔗 Haz clic en cualquier link para abrir la fuente en una pestaña nueva")

    html_path = BASE_DIR / "static" / "Prensa_Deportiva.html"
    
    if html_path.exists():
        try:
            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            st.markdown(html_content, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"❌ Error al leer HTML: {e}")
    else:
        st.warning("""
        ⚠️ **El archivo `static/Prensa_Deportiva.html` no existe**
        
        **Solución:**
        1. Crea la carpeta `static` en la raíz del proyecto
        2. Copia tu archivo `Prensa_Deportiva.html` ahí
        3. Recarga la página (presiona R)
        """)

# ═════════════════════════════════════════════════════════════════════════════
# TAB 2: VINOTINTO GALÁCTICO
# ═════════════════════════════════════════════════════════════════════════════

with tab_vinotinto:
    st.markdown('<div style="text-align: center;"><h1>🔴 VINOTINTO GALÁCTICO</h1></div>', unsafe_allow_html=True)

    # Banner
    if banner_b64:
        st.markdown(f'''
        <div style="text-align: center; margin: 20px 0;">
            <img src="data:image/png;base64,{banner_b64}" style="max-width: 100%; height: auto; border-radius: 10px;">
        </div>
        ''', unsafe_allow_html=True)

    # Cargar fuentes
    sources_vinotinto = {}
    try:
        sources_vinotinto = load_sources_vinotinto()
        if not sources_vinotinto:
            st.warning("⚠️ No se encontraron fuentes en el Excel de Vinotinto")
    except Exception as e:
        st.error(f"❌ Error al cargar Excel: {e}")
        logger.error(f"Error cargando Vinotinto: {e}")

    # Selector de fuentes
    st.markdown("### 📋 SELECCIONA FUENTES")

    if sources_vinotinto:
        # Inicializar estado de selección
        if 'vg_selection' not in st.session_state:
            st.session_state.vg_selection = {}

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("**Categorías disponibles:**")
            
            selected_vinotinto = {}
            
            for categoria, fuentes in sorted(sources_vinotinto.items()):
                icon = CATEGORY_ICONS.get(categoria, "📰")
                with st.expander(f"{icon} {categoria}", expanded=False):
                    selected_vinotinto[categoria] = {}
                    for idx, (nombre, url) in enumerate(fuentes):
                        # KEY ÚNICA GARANTIZADA con UUID
                        unique_key = f"vg_{uuid.uuid4().hex[:8]}_{categoria}_{idx}"
                        selected_vinotinto[categoria][nombre] = st.checkbox(
                            f"{nombre}",
                            key=unique_key
                        )

        with col2:
            st.markdown("**Información:**")
            total_fuentes = sum(len(f) for f in sources_vinotinto.values())
            st.info(f"""
            📁 Total categorías: {len(sources_vinotinto)}
            
            📰 Total fuentes: {total_fuentes}
            """)

        # Botón de extracción
        st.markdown("---")
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        with col_btn2:
            if st.button("⚡ EXTRAER NOTICIAS VINOTINTO", key="btn_vg", use_container_width=True, type="primary"):
                # Recopilar URLs seleccionadas
                urls_to_extract = []
                for categoria, fuentes_dict in selected_vinotinto.items():
                    if categoria in sources_vinotinto:
                        for nombre, url in sources_vinotinto[categoria]:
                            if fuentes_dict.get(nombre, False):
                                urls_to_extract.append((nombre, url, categoria))

                if not urls_to_extract:
                    st.warning("⚠️ Selecciona al menos una fuente")
                else:
                    st.success(f"✅ Procesando {len(urls_to_extract)} fuentes...")
                    
                    progress_bar = st.progress(0)
                    status = st.empty()
                    noticias = []
                    logs = []

                    async def extract():
                        for idx, (nombre, url, categoria) in enumerate(urls_to_extract):
                            status.text(f"📥 Procesando: {nombre} ({idx+1}/{len(urls_to_extract)})")
                            try:
                                extractor = get_extractor(nombre, url, categoria)
                                noticias_ext, log = await extractor.extract()
                                noticias.extend(noticias_ext)
                                logs.append(log)
                            except Exception as e:
                                logger.error(f"Error extrayendo {nombre}: {e}")
                            progress_bar.progress((idx + 1) / len(urls_to_extract))
                        
                        status.text("✅ ¡Completado!")

                    with st.spinner("Extrayendo noticias..."):
                        asyncio.run(extract())

                    if noticias:
                        export_txt(noticias, BASE_DIR / "output" / "noticias_vinotinto.txt")
                        export_html(noticias, BASE_DIR / "output" / "noticias_vinotinto.html")

                        st.success(f"✅ {len(noticias)} noticias extraídas exitosamente")

                        col1, col2 = st.columns(2)
                        with col1:
                            with open(BASE_DIR / "output" / "noticias_vinotinto.txt", "rb") as f:
                                st.download_button("📥 Descargar TXT", f, "noticias_vinotinto.txt", key="dl_txt_vg")
                        with col2:
                            with open(BASE_DIR / "output" / "noticias_vinotinto.html", "rb") as f:
                                st.download_button("📥 Descargar HTML", f, "noticias_vinotinto.html", key="dl_html_vg")
                    else:
                        st.info("ℹ️ No se encontraron noticias del día en las fuentes seleccionadas")
    else:
        st.error("❌ No se pudieron cargar las fuentes. Verifica que el Excel exista en data/Prensa Deportiva.xlsx")

# ═════════════════════════════════════════════════════════════════════════════
# TAB 3: MUNDIAL 2026
# ═════════════════════════════════════════════════════════════════════════════

with tab_mundial:
    st.markdown('<div style="text-align: center;"><h1>🌍 MUNDIAL 2026</h1></div>', unsafe_allow_html=True)
    st.warning("⚠️ Contenido temporal disponible hasta el **19 de Julio de 2026**")

    # Cargar fuentes
    sources_mundial = {}
    try:
        sources_mundial = load_sources_mundial()
        if not sources_mundial:
            st.warning("⚠️ No se encontraron fuentes en el Excel del Mundial")
    except Exception as e:
        st.error(f"❌ Error al cargar Excel: {e}")
        logger.error(f"Error cargando Mundial: {e}")

    # Selector de fuentes
    st.markdown("### 📋 FUENTES DEL MUNDIAL")

    if sources_mundial and "Mundial Global" in sources_mundial:
        selected_mundial = {}
        selected_mundial["Mundial Global"] = {}

        st.markdown("**Selecciona las fuentes:**")
        
        # Mostrar en columnas
        cols = st.columns(3)
        fuentes_list = sources_mundial["Mundial Global"]

        for idx, (nombre, url) in enumerate(fuentes_list):
            with cols[idx % 3]:
                # KEY ÚNICA GARANTIZADA
                unique_key = f"mundial_{uuid.uuid4().hex[:8]}_{idx}"
                selected_mundial["Mundial Global"][nombre] = st.checkbox(
                    f"{nombre}",
                    key=unique_key
                )

        # Información
        st.markdown("---")
        st.info(f"""
        🏆 Total fuentes: {len(sources_mundial['Mundial Global'])}
        
        ⏰ Válido hasta: 19/07/2026
        """)

        # Botón de extracción
        st.markdown("---")
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        with col_btn2:
            if st.button("⚡ EXTRAER NOTICIAS MUNDIAL", key="btn_mundial", use_container_width=True, type="primary"):
                urls_to_extract = []
                for nombre, url in sources_mundial.get("Mundial Global", []):
                    if selected_mundial["Mundial Global"].get(nombre, False):
                        urls_to_extract.append((nombre, url, "Mundial Global"))

                if not urls_to_extract:
                    st.warning("⚠️ Selecciona al menos una fuente")
                else:
                    st.success(f"✅ Procesando {len(urls_to_extract)} fuentes...")
                    
                    progress_bar = st.progress(0)
                    status = st.empty()
                    noticias = []
                    logs = []

                    async def extract():
                        for idx, (nombre, url, categoria) in enumerate(urls_to_extract):
                            status.text(f"📥 Procesando: {nombre} ({idx+1}/{len(urls_to_extract)})")
                            try:
                                extractor = get_extractor(nombre, url, categoria)
                                noticias_ext, log = await extractor.extract()
                                noticias.extend(noticias_ext)
                                logs.append(log)
                            except Exception as e:
                                logger.error(f"Error extrayendo {nombre}: {e}")
                            progress_bar.progress((idx + 1) / len(urls_to_extract))
                        
                        status.text("✅ ¡Completado!")

                    with st.spinner("Extrayendo noticias del Mundial..."):
                        asyncio.run(extract())

                    if noticias:
                        export_txt(noticias, BASE_DIR / "output" / "noticias_mundial.txt")
                        export_html(noticias, BASE_DIR / "output" / "noticias_mundial.html")

                        st.success(f"✅ {len(noticias)} noticias extraídas exitosamente")

                        col1, col2 = st.columns(2)
                        with col1:
                            with open(BASE_DIR / "output" / "noticias_mundial.txt", "rb") as f:
                                st.download_button("📥 Descargar TXT", f, "noticias_mundial.txt", key="dl_txt_mundial")
                        with col2:
                            with open(BASE_DIR / "output" / "noticias_mundial.html", "rb") as f:
                                st.download_button("📥 Descargar HTML", f, "noticias_mundial.html", key="dl_html_mundial")
                    else:
                        st.info("ℹ️ No se encontraron noticias del día en las fuentes seleccionadas")
    else:
        st.error("❌ No se pudieron cargar las fuentes del Mundial. Verifica que el Excel exista en data/Prensa_Mundial_2026_ListaEnlaces.xlsx")

# Footer
st.markdown("---")
st.markdown('<div style="text-align: center; color: gray; font-size: 0.9em;">⚽ Vinotinto Galáctico News Extractor v3.0 - Corregido</div>', unsafe_allow_html=True)