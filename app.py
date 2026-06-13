import streamlit as st
import os
from datetime import datetime
# Mantenemos tus importaciones originales exactas
from core.excel_reader import ExcelReader
from core.news_extractor import NewsExtractor

# 1. CONFIGURACIÓN E IDENTIDAD VISUAL (Tu Banner y Logo originales)
st.set_page_config(page_title="BG Extractor News", page_icon="⚽", layout="wide")

if os.path.exists("banner-vinotinto.png"):
    st.image("banner-vinotinto.png", use_container_width=True)

# 2. SELECTOR DE PROYECTO (Único cambio para no romper nada)
st.sidebar.title("⚽ Configuración")
proyecto = st.sidebar.radio("Seleccione el Proyecto:", ["Vinotinto Galáctico", "Mundial 2026"])

if proyecto == "Vinotinto Galáctico":
    excel_path = "data/Prensa Deportiva.xlsx"
    color_tit = "#7B1630"
else:
    excel_path = "data/Prensa_Mundial.xlsx"
    color_tit = "#1d4ed8"

st.markdown(f"<h1 style='text-align: center; color: {color_tit};'>{proyecto}</h1>", unsafe_allow_html=True)

# 3. LÓGICA ORIGINAL DE EXTRACCIÓN (Checkboxes y Filtros)
if not os.path.exists(excel_path):
    st.error(f"No se encuentra el archivo {excel_path}")
else:
    reader = ExcelReader(excel_path)
    categorias = reader.get_categories()
    
    # Filtro de fecha (Como lo tenías originalmente)
    fecha_filtro = st.sidebar.date_input("Filtrar noticias desde:", datetime.now())

    st.subheader("📁 Selección Masiva de Noticias")
    
    # Aquí restauramos tu lógica de selección por secciones
    seleccion_seccion = st.multiselect("Seleccione las secciones a extraer:", categorias)
    
    todos_los_links = []
    if seleccion_seccion:
        for cat in seleccion_seccion:
            links = reader.get_links_by_category(cat)
            todos_los_links.extend(links)
        
        st.write(f"Total de noticias encontradas en estas secciones: {len(todos_los_links)}")
        
        # Checkboxes para selección individual (Tu automatización original)
        links_seleccionados = []
        col1, col2 = st.columns(2)
        for i, link in enumerate(todos_los_links):
            with (col1 if i % 2 == 0 else col2):
                if st.checkbox(f"Noticia {i+1}: {link[:60]}...", value=True, key=f"link_{i}"):
                    links_seleccionados.append(link)

        if st.button("🚀 INICIAR EXTRACCIÓN AUTOMÁTICA"):
            extractor = NewsExtractor() # Tu clase original
            progreso = st.progress(0)
            
            for idx, link in enumerate(links_seleccionados):
                with st.expander(f"Extrayendo: {link}"):
                    # Aquí el extractor usará tus scripts de 'extractores/' (AS, Marca, etc.)
                    resultado = extractor.extract(link)
                    
                    if "error" not in resultado:
                        st.subheader(resultado.get('titulo', 'Sin Título'))
                        st.write(resultado.get('contenido', 'Sin Contenido'))
                        st.markdown("---")
                    else:
                        st.error(f"No se pudo extraer de este sitio: {link}")
                
                progreso.progress((idx + 1) / len(links_seleccionados))
            
            st.success(f"Proceso finalizado. {len(links_seleccionados)} noticias procesadas.")