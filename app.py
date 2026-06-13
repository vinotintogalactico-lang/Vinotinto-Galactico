import streamlit as st
import os
# Importamos tus clases originales desde tu carpeta 'core'
from core.excel_reader import ExcelReader
from core.news_extractor import NewsExtractor

# 1. CONFIGURACIÓN DE PÁGINA (Manteniendo tu estilo)
st.set_page_config(page_title="BG Extractor News", page_icon="⚽", layout="wide")

# --- AQUÍ VA TU IDENTIDAD VISUAL ---
# He dejado los espacios para que el código busque tus imágenes donde ya las tienes
# Si usas rutas locales (ej: assets/banner.png), asegúrate de que el nombre coincida
col_logo, col_banner = st.columns([1, 4])

with col_logo:
    # Si tienes un logo lo cargamos aquí (estoy usando una lógica que no rompe si no existe)
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", width=150)

with col_banner:
    # Aquí es donde va tu banner principal del canal
    if os.path.exists("assets/banner.png"):
        st.image("assets/banner.png", use_container_width=True)
    else:
        # Título alternativo si el banner no se encuentra
        st.markdown("<h1 style='text-align: center;'>BG EXTRACTOR - PRO</h1>", unsafe_allow_html=True)

# 2. PANEL DE CONTROL (Sidebar)
st.sidebar.title("⚽ Configuración")
st.sidebar.markdown("---")

# Selector de base de datos para que elijas qué trabajar hoy
modo_trabajo = st.sidebar.radio(
    "Selecciona el proyecto:",
    ["Vinotinto Galáctico", "Mundial 2026"]
)

# Definimos la ruta del Excel según lo que elijas
if modo_trabajo == "Vinotinto Galáctico":
    ruta_excel = "data/Prensa Deportiva.xlsx"
else:
    ruta_excel = "data/Prensa_Mundial.xlsx"

st.sidebar.success(f"Modo activo: {modo_trabajo}")

# 3. LÓGICA DE EXTRACCIÓN (Usando tus clases de la carpeta 'core')
if not os.path.exists(ruta_excel):
    st.error(f"Falta el archivo: {ruta_excel}. Por favor, súbelo a la carpeta 'data'.")
else:
    try:
        # Inicializamos tu lector de Excel
        reader = ExcelReader(ruta_excel)
        categorias = reader.get_categories()

        st.markdown("---")
        c1, c2 = st.columns([1, 2])

        with c1:
            st.subheader("📁 Navegación")
            categoria_seleccionada = st.selectbox("Sección:", categorias)
            
            links = reader.get_links_by_category(categoria_seleccionada)
            link_noticia = st.selectbox("Seleccione la noticia:", links)

        with c2:
            st.subheader("📝 Extractor")
            if st.button("🚀 INICIAR EXTRACCIÓN"):
                with st.spinner('Procesando noticia...'):
                    # Usamos tu extractor original
                    extractor = NewsExtractor(link_noticia)
                    resultado = extractor.extract()

                    if "error" in resultado:
                        st.error(f"Error: {resultado['error']}")
                    else:
                        st.text_input("Título de la Noticia:", value=resultado['titulo'])
                        st.text_area("Contenido para el Guion:", value=resultado['contenido'], height=450)
                        st.balloons()

    except Exception as e:
        st.error(f"Hubo un problema al cargar los archivos core: {str(e)}")

# Pie de página profesional
st.markdown("---")
st.caption(f"© Vinotinto Galáctico - Sistema de Extracción Automatizado - {modo_trabajo}")