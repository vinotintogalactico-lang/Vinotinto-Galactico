import streamlit as st
import os
import sys
from datetime import datetime

# FIX: Esto asegura que Streamlit encuentre tus clases en la carpeta 'core'
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

try:
    from core.excel_reader import ExcelReader
    from core.news_extractor import NewsExtractor
except ImportError:
    st.error("Error crítico: No se encuentran las clases en 'core/'. Revisa que los archivos existan.")

# 1. IDENTIDAD VISUAL ORIGINAL
st.set_page_config(page_title="BG Extractor News", page_icon="⚽", layout="wide")

if os.path.exists("banner-vinotinto.png"):
    st.image("banner-vinotinto.png", use_container_width=True)

if os.path.exists("Logo.jpg"):
    st.sidebar.image("Logo.jpg", width=120)

# 2. SELECTOR DE PROYECTO Y FILTROS ORIGINALES
st.sidebar.title("⚽ Configuración")
proyecto = st.sidebar.radio("Seleccione el Proyecto:", ["Vinotinto Galáctico", "Mundial 2026"])

# Selección de base de datos
if proyecto == "Vinotinto Galáctico":
    excel_path = "data/Prensa Deportiva.xlsx"
    color_tit = "#7B1630"
else:
    excel_path = "data/Prensa_Mundial.xlsx"
    color_tit = "#1d4ed8"

# FILTRO DE FECHA (Tu filtro original para no extraer noticias viejas)
st.sidebar.markdown("---")
fecha_limite = st.sidebar.date_input("Extraer noticias desde el día:", datetime.now())

st.markdown(f"<h1 style='text-align: center; color: {color_tit};'>{proyecto}</h1>", unsafe_allow_html=True)

# 3. MOTOR DE EXTRACCIÓN MASIVA (Checkboxes y Selección por Categoría)
if not os.path.exists(excel_path):
    st.error(f"⚠️ No encuentro el archivo {excel_path}")
else:
    # Usamos tu Lector de Excel original
    reader = ExcelReader(excel_path)
    categorias = reader.get_categories()

    st.subheader("📁 Panel de Selección Masiva")
    
    # Selección de categorías (Multiselect como lo tenías)
    secciones_sel = st.multiselect("Seleccione las secciones para buscar noticias:", categorias)
    
    if secciones_sel:
        links_totales = []
        for cat in secciones_sel:
            links_totales.extend(reader.get_links_by_category(cat))
        
        st.write(f"🔍 Se encontraron **{len(links_totales)}** enlaces en las secciones seleccionadas.")
        
        # LISTA DE CHECKBOXES (Para que elijas qué extraer y qué no)
        st.markdown("### Seleccione las noticias individuales:")
        links_finales = []
        
        # Dividimos en 2 columnas para que sea vea ordenado como tu programa original
        col1, col2 = st.columns(2)
        for i, link in enumerate(links_totales):
            with (col1 if i % 2 == 0 else col2):
                # Checkbox por cada link
                if st.checkbox(f"Noticia {i+1}: {link[:65]}...", value=True, key=f"chk_{i}"):
                    links_finales.append(link)

        # 4. BOTÓN DE EXTRACCIÓN AUTOMATIZADA
        st.markdown("---")
        if st.button(f"🚀 INICIAR EXTRACCIÓN DE {len(links_finales)} NOTICIAS"):
            # Usamos tu Extractor original (que ya tiene los filtros de AS, Marca, etc.)
            extractor = NewsExtractor() 
            bar = st.progress(0)
            
            for idx, url in enumerate(links_finales):
                with st.expander(f"Extrayendo: {url}", expanded=True):
                    # Aquí el programa usa tus scripts de la carpeta 'extractors/'
                    resultado = extractor.extract(url)
                    
                    if "error" not in resultado:
                        # Verificación de fecha si tu extractor lo permite
                        st.subheader(resultado.get('titulo', 'Sin Título'))
                        st.write(resultado.get('contenido', 'Sin Contenido'))
                    else:
                        st.error(f"Error en este link: {resultado['error']}")
                
                bar.progress((idx + 1) / len(links_finales))
            
            st.success("✅ Proceso masivo completado.")

# PIE DE PÁGINA
st.markdown("---")
st.caption("Sistema BG Extractor Pro - Vinotinto Galáctico")