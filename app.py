import streamlit as st
import os
import sys
from datetime import datetime

# 1. FIX DE RUTAS (Para que reconozca tu carpeta core y extractors)
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

try:
    from core.excel_reader import ExcelReader
    from core.news_extractor import NewsExtractor
except ImportError as e:
    st.error(f"Error al cargar módulos profesionales: {e}")

# 2. IDENTIDAD VISUAL (Banner y Logo exactos)
st.set_page_config(page_title="BG Extractor News", page_icon="⚽", layout="wide")

# Banner superior (Tamaño original)
if os.path.exists("banner-vinotinto.png"):
    st.image("banner-vinotinto.png", use_container_width=True)

# Logo en el Sidebar (Como lo tenías)
if os.path.exists("Logo.jpg"):
    st.sidebar.image("Logo.jpg", use_container_width=True)

# 3. SIDEBAR: PANEL DE CONTROL Y FILTROS
st.sidebar.title("🎮 PANEL DE MANDO")

# El selector de proyecto para elegir entre tus archivos Excel
modo = st.sidebar.radio("MODO DE TRABAJO:", ["Vinotinto Galáctico", "Mundial 2026"])

if modo == "Vinotinto Galáctico":
    excel_path = "data/Prensa Deportiva.xlsx"
    tema_color = "#7B1630"
else:
    excel_path = "data/Prensa_Mundial.xlsx"
    tema_color = "#1d4ed8"

st.sidebar.markdown("---")

# Botón de Prensa Deportiva (Tu HTML de comprobación)
if st.sidebar.button("📋 ABRIR PANEL DE PRENSA"):
    # Aquí llamamos al HTML que tenías para verificar veracidad
    st.sidebar.info("Abriendo verificador de noticias...")
    # Lógica para abrir tu visualizador de links original

# Filtro de fecha profesional (Tu motor de veracidad)
fecha_verificacion = st.sidebar.date_input("FECHA DE NOTICIAS:", datetime.now())

# 4. CUERPO PRINCIPAL
st.markdown(f"<h1 style='text-align: center; color: {tema_color};'>{modo.upper()}</h1>", unsafe_allow_html=True)

if not os.path.exists(excel_path):
    st.error(f"No se encontró el archivo: {excel_path}")
else:
    # USAMOS TUS CLASES ORIGINALES (Core)
    reader = ExcelReader(excel_path)
    categorias = reader.get_categories()

    # Selección por Secciones (Multiselect)
    st.subheader("📁 SELECCIONAR SECCIONES")
    secciones_sel = st.multiselect("Filtrar por prensa:", categorias)

    if secciones_sel:
        links_totales = []
        for sec in secciones_sel:
            links_totales.extend(reader.get_links_by_category(sec))

        st.markdown(f"**Noticias disponibles en {len(secciones_sel)} secciones:** {len(links_totales)}")
        
        # 5. EL PANEL DE CHECKBOXES (LIBRE DE SALSA DE TOMATE)
        # Los checkboxes vienen DESACTIVADOS (value=False)
        st.markdown("### 🔍 SELECCIÓN MANUAL DE NOTICIAS")
        links_para_extraer = []
        
        col1, col2 = st.columns(2)
        for i, url in enumerate(links_totales):
            with (col1 if i % 2 == 0 else col2):
                # Valor por defecto FALSE: Tú eliges qué quieres, yo no te obligo a nada
                if st.checkbox(f"Noticia {i+1}: {url[:70]}", value=False, key=f"news_{i}"):
                    links_para_extraer.append(url)

        # 6. MESA DE EXTRACCIÓN (Botón original)
        st.markdown("---")
        if st.button(f"🚀 EXTRAER {len(links_para_extraer)} NOTICIAS SELECCIONADAS"):
            if not links_para_extraer:
                st.warning("Debe seleccionar al menos una noticia con el check.")
            else:
                # LLAMADA A TU EXTRACTOR PROFESIONAL (El que filtra fecha, autor y contenido limpio)
                extractor = NewsExtractor()
                bar = st.progress(0)
                
                for idx, noticia_url in enumerate(links_para_extraer):
                    # Usamos tu formato: Título, Subtítulo, Fecha, Fuente y Cuerpo Completo
                    resultado = extractor.extract(noticia_url)
                    
                    if "error" not in resultado:
                        with st.container():
                            st.subheader(f"🗞️ {resultado.get('titulo', 'Sin Título')}")
                            # Mostrar fecha y autor como tenías en la documentación de GitHub
                            st.caption(f"📅 Fecha: {resultado.get('fecha', 'N/A')} | 🖋️ Fuente: {resultado.get('fuente', 'N/A')}")
                            
                            st.write(resultado.get('contenido', 'No se pudo obtener el cuerpo de la noticia.'))
                            st.markdown("---")
                    else:
                        st.error(f"Error en {noticia_url}: {resultado['error']}")
                    
                    bar.progress((idx + 1) / len(links_para_extraer))

st.markdown("<p style='text-align: center; color: gray;'>BG Extractor Pro - Estándar Vinotinto Galáctico</p>", unsafe_allow_html=True)