import streamlit as st
import pandas as pd
import os
from utils.excel_reader import ExcelReader
from utils.news_extractor import NewsExtractor

# Configuración de la página
st.set_page_config(page_title="BG Extractor - News", page_icon="⚽", layout="wide")

# --- BARRA LATERAL (SIDEBAR) ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/a/a4/FIFA_World_Cup_2026_Logo.png", width=100)
st.sidebar.title("Configuración de Extracción")

# AQUÍ ELIGES QUÉ BASE DE DATOS USAR
opcion_base = st.sidebar.selectbox(
    "Seleccione el modo de trabajo:",
    ["Vinotinto Galáctico (Fútbol)", "Mundial 2026"]
)

# Definir la ruta del archivo según la opción seleccionada
if opcion_base == "Vinotinto Galáctico (Fútbol)":
    archivo_excel = "data/Prensa_Deportiva.xlsx"
    color_titulo = "#7B1630"  # Color Vinotinto
else:
    archivo_excel = "data/Prensa_Mundial.xlsx"
    color_titulo = "#1d4ed8"  # Color Azul Mundial

st.sidebar.markdown(f"**Base de datos activa:** \n`{archivo_excel}`")

# --- CUERPO PRINCIPAL ---
st.markdown(f"<h1 style='text-align: center; color: {color_titulo};'>{opcion_base}</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Extractor de noticias automático para YouTube</p>", unsafe_allow_html=True)

# Verificar si el archivo existe antes de continuar
if not os.path.exists(archivo_excel):
    st.error(f"⚠️ Error: No se encuentra el archivo {archivo_excel} en la carpeta 'data/'. Por favor súbelo a GitHub.")
else:
    try:
        # Cargar los datos del Excel
        reader = ExcelReader(archivo_excel)
        categorias = reader.get_categories()

        col1, col2 = st.columns([1, 2])

        with col1:
            st.subheader("1. Selección")
            categoria_seleccionada = st.selectbox("Seleccione una categoría/sección:", categorias)
            
            links = reader.get_links_by_category(categoria_seleccionada)
            link_seleccionado = st.selectbox("Seleccione la noticia:", links)

        with col2:
            st.subheader("2. Resultado de Extracción")
            
            if st.button("🚀 Extraer Noticia"):
                with st.spinner('Extrayendo contenido...'):
                    extractor = NewsExtractor(link_seleccionado)
                    resultado = extractor.extract()

                    if "error" in resultado:
                        st.error(f"No se pudo extraer la noticia: {resultado['error']}")
                    else:
                        # Título de la noticia
                        st.markdown(f"### {resultado['titulo']}")
                        
                        # Contenido formateado para leer fácil
                        st.text_area("Contenido Extraído:", value=resultado['contenido'], height=400)
                        
                        # Botón para copiar (ayuda visual)
                        st.success("✅ ¡Noticia extraída con éxito!")
                        st.info("Copia el texto de arriba para tu guion de YouTube.")

    except Exception as e:
        st.error(f"Ocurrió un error inesperado: {e}")

# Pie de página
st.markdown("---")
st.markdown(f"<p style='text-align: center; color: gray;'>BG Extractor - Modo: {opcion_base}</p>", unsafe_allow_html=True)