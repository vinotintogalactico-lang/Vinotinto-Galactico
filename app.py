"""
VINOTINTO GALÁCTICO NEWS EXTRACTOR v2.0
Versión con TABS: Panel Prensa | Vinotinto | Mundial
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

@st.cache_resource(show_spinner=False)
def _install_playwright():
    try:
        os.system(f"{sys.executable} -m playwright install chromium")
    except Exception as e:
        print(f"Error: {e}")

_install_playwright()
Path("output").mkdir(exist_ok=True)

from core.excel_reader import load_sources_vinotinto, load_sources_mundial
from core.txt_exporter import export_txt
from core.html_exporter import export_html
from extractores.factory import get_extractor

logging.basicConfig(level=logging.INFO)

# ═════════════════════════════════════════════════════════════════════════════
# CONFIG
# ═════════════════════════════════════════════════════════════════════════════

CATEGORY_ICONS = {
    "Real Madrid Masculino": "👑",
    "Real Madrid Femenino": "👑",
    "LaLiga": "🇪🇸",
    "Selección Española Masculina": "🇪🇸",
    "Selección Española Femenina": "🇪🇸",
    "Vinotinto Masculina": "🇻🇪",
    "Vinotinto Femenina": "🇻🇪",
    "Liga FUTVE": "🇻🇪",
}

st.set_page_config(
    page_title="VG Extractor | Vinotinto + Mundial", 
    page_icon="⚽", 
    layout="wide"
)

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
    font-size: 2.2rem; color: #fff; letter-spacing: 3px; margin: 0;
}

.cat-label {
    font-family: 'Bebas Neue', sans-serif; font-size: 0.95rem;
    letter-spacing: 2px; color: #c0392b;
    padding: 0.3rem 0 0.1rem 0; border-bottom: 1px solid #2a2a2a;
    margin-top: 0.8rem; margin-bottom: 0.3rem;
}

.section-header {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.3rem;
    color: #fff;
    background: #1a1a1a;
    padding: 0.5rem 1rem;
    border-left: 4px solid;
    margin-top: 1rem;
    margin-bottom: 0.5rem;
}

.section-vinotinto .section-header { border-color: #c0392b; }
.section-mundial .section-header { border-color: #00b050; }

.news-card {
    background: #161616; border: 1px solid #2a2a2a;
    border-left: 4px solid #7a1a2e; border-radius: 4px;
    padding: 1.2rem 1.5rem; margin-bottom: 1.2rem;
}

.news-card .nc-meta { font-size: 0.72rem; color: #888; margin-bottom: 0.4rem; }
.news-card .nc-cat { color: #c0392b; font-weight: 600; }
.news-card h3 { font-size: 1.05rem; color: #eee; margin: 0.3rem 0; }
.news-card .nc-body { font-size: 0.88rem; color: #c8c8c8; line-height: 1.7; }
</style>
""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# CARGAR IMÁGENES
# ═════════════════════════════════════════════════════════════════════════════

def _b64(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
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
    
    try:
        with open("static/Prensa_Deportiva.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        st.markdown(html_content, unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("""
        ⚠️ El archivo `static/Prensa_Deportiva.html` no se encontró.
        
        **Para usar esta función:**
        1. Crea la carpeta `static/` en la raíz del proyecto
        2. Copia `Prensa_Deportiva.html` en esa carpeta
        3. Recarga la página
        """)

# ═════════════════════════════════════════════════════════════════════════════
# TAB 2: VINOTINTO GALÁCTICO
# ═════════════════════════════════════════════════════════════════════════════

with tab_vinotinto:
    st.markdown('<div class="vg-titlebar"><h1>🔴 VINOTINTO GALÁCTICO</h1></div>', unsafe_allow_html=True)
    
    # Banner
    if banner_b64:
        st.markdown(f'<div style="margin:-1rem auto 0;"><img src="data:image/png;base64,{banner_b64}" style="width:100%; max-height:250px; object-fit:cover;"></div>', unsafe_allow_html=True)
    
    # Cargar fuentes
    try:
        sources_vinotinto = load_sources_vinotinto()
    except Exception as e:
        st.error(f"❌ Error al cargar Excel: {e}")
        sources_vinotinto = {}
    
    # Selector de fuentes
    st.markdown("### 📋 SELECCIONA FUENTES")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Categorías disponibles:**")
        selected_vinotinto = {}
        for categoria, fuentes in sorted(sources_vinotinto.items()):
            icon = CATEGORY_ICONS.get(categoria, "📰")
            with st.expander(f"{icon} {categoria}", expanded=False):
                selected_vinotinto[categoria] = {}
                for nombre, url in fuentes:
                    selected_vinotinto[categoria][nombre] = st.checkbox(nombre, key=f"vg_{categoria}_{nombre}")
    
    with col2:
        st.markdown("**Información:**")
        st.info(f"📁 Total categorías: {len(sources_vinotinto)}\n\n📰 Total fuentes: {sum(len(f) for f in sources_vinotinto.values())}")
    
    # Botón de extracción
    st.markdown("---")
    if st.button("⚡ EXTRAER NOTICIAS VINOTINTO", key="btn_vg"):
        urls_to_extract = []
        for categoria, fuentes_dict in selected_vinotinto.items():
            if categoria in sources_vinotinto:
                for nombre, url in sources_vinotinto[categoria]:
                    if fuentes_dict.get(nombre, False):
                        urls_to_extract.append((nombre, url, categoria))
        
        if not urls_to_extract:
            st.warning("⚠️ Selecciona al menos una fuente")
        else:
            progress_bar = st.progress(0)
            status = st.empty()
            noticias = []
            logs = []
            
            async def extract():
                for idx, (nombre, url, categoria) in enumerate(urls_to_extract):
                    status.text(f"📥 Procesando: {nombre} ({idx+1}/{len(urls_to_extract)})")
                    extractor = get_extractor(nombre, url, categoria)
                    noticias_ext, log = await extractor.extract()
                    noticias.extend(noticias_ext)
                    logs.append(log)
                    progress_bar.progress((idx + 1) / len(urls_to_extract))
            
            asyncio.run(extract())
            
            if noticias:
                export_txt(noticias, "output/noticias_vinotinto.txt")
                export_html(noticias, "output/noticias_vinotinto.html")
                
                st.success(f"✅ {len(noticias)} noticias extraídas")
                
                col1, col2 = st.columns(2)
                with col1:
                    with open("output/noticias_vinotinto.txt", "rb") as f:
                        st.download_button("📥 TXT", f, "noticias_vinotinto.txt")
                with col2:
                    with open("output/noticias_vinotinto.html", "rb") as f:
                        st.download_button("📥 HTML", f, "noticias_vinotinto.html")
            else:
                st.info("ℹ️ Sin noticias del día en las fuentes seleccionadas")

# ═════════════════════════════════════════════════════════════════════════════
# TAB 3: MUNDIAL 2026
# ═════════════════════════════════════════════════════════════════════════════

with tab_mundial:
    st.markdown('<div class="vg-titlebar"><h1>🌍 MUNDIAL 2026</h1></div>', unsafe_allow_html=True)
    
    st.warning("⚠️ Contenido temporal disponible hasta el **19 de Julio de 2026**")
    
    # Cargar fuentes
    try:
        sources_mundial = load_sources_mundial()
    except Exception as e:
        st.error(f"❌ Error al cargar Excel: {e}")
        sources_mundial = {}
    
    # Selector de fuentes
    st.markdown("### 📋 FUENTES DEL MUNDIAL")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Fuentes disponibles:**")
        selected_mundial = {}
        if "Mundial Global" in sources_mundial:
            selected_mundial["Mundial Global"] = {}
            
            # Mostrar en columnas para mejor visualización
            cols = st.columns(3)
            fuentes_list = sources_mundial["Mundial Global"]
            
            for idx, (nombre, url) in enumerate(fuentes_list):
                with cols[idx % 3]:
                    selected_mundial["Mundial Global"][nombre] = st.checkbox(nombre, key=f"mundial_{nombre}")
    
    with col2:
        st.markdown("**Información:**")
        if "Mundial Global" in sources_mundial:
            st.info(f"🏆 Total fuentes: {len(sources_mundial['Mundial Global'])}\n\n⏰ Válido hasta: 19/07/2026")
    
    # Botón de extracción
    st.markdown("---")
    if st.button("⚡ EXTRAER NOTICIAS MUNDIAL", key="btn_mundial"):
        urls_to_extract = []
        if "Mundial Global" in selected_mundial:
            for nombre, url in sources_mundial.get("Mundial Global", []):
                if selected_mundial["Mundial Global"].get(nombre, False):
                    urls_to_extract.append((nombre, url, "Mundial Global"))
        
        if not urls_to_extract:
            st.warning("⚠️ Selecciona al menos una fuente")
        else:
            progress_bar = st.progress(0)
            status = st.empty()
            noticias = []
            logs = []
            
            async def extract():
                for idx, (nombre, url, categoria) in enumerate(urls_to_extract):
                    status.text(f"📥 Procesando: {nombre} ({idx+1}/{len(urls_to_extract)})")
                    extractor = get_extractor(nombre, url, categoria)
                    noticias_ext, log = await extractor.extract()
                    noticias.extend(noticias_ext)
                    logs.append(log)
                    progress_bar.progress((idx + 1) / len(urls_to_extract))
            
            asyncio.run(extract())
            
            if noticias:
                export_txt(noticias, "output/noticias_mundial.txt")
                export_html(noticias, "output/noticias_mundial.html")
                
                st.success(f"✅ {len(noticias)} noticias extraídas")
                
                col1, col2 = st.columns(2)
                with col1:
                    with open("output/noticias_mundial.txt", "rb") as f:
                        st.download_button("📥 TXT", f, "noticias_mundial.txt")
                with col2:
                    with open("output/noticias_mundial.html", "rb") as f:
                        st.download_button("📥 HTML", f, "noticias_mundial.html")
            else:
                st.info("ℹ️ Sin noticias del día en las fuentes seleccionadas")

# Footer
st.markdown("---")
st.markdown("<center style='font-size:12px; color:#888;'>⚽ Vinotinto Galáctico News Extractor v2.0</center>", unsafe_allow_html=True)
