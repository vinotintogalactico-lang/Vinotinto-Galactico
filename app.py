import streamlit as st
import os
import pandas as pd
import requests
from bs4 import BeautifulSoup

# IMPORTANTE: Usamos 'core' porque así se llama tu carpeta en GitHub
try:
    from core.excel_reader import ExcelReader
except ImportError:
    st.error("No se pudo cargar 'core.excel_reader'. Asegúrate de que la carpeta 'core' existe.")

# Configuración de la página
st.set_page_config(page_title="BG Extractor Pro", page_icon="⚽", layout="wide")

# Función de extracción propia para asegurar que funcione sin dependencias externas
def extraer_contenido(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Intentar obtener el título
        titulo = soup.find('h1').text.strip() if soup.find('h1') else "Noticia del día"
        
        # Intentar obtener el texto (párrafos)
        parrafos = soup.find_all('p')
        cuerpo = "\n\n".join([p.text.strip() for p in parrafos if len(p.text.strip()) > 60])
        
        return {"titulo": titulo, "contenido": cuerpo}
    except Exception as e:
        return {"error": str(e)}

# --- BARRA LATERAL ---
st.sidebar.title("⚽ Configuración")

modo = st.sidebar.selectbox(
    "Seleccione el Proyecto:",
    ["Vinotinto Galáctico", "Mundial 2026"]
)

# Definir la ruta del Excel según el modo
if modo == "Vinotinto Galáctico":
    # Tu archivo original tiene un espacio: "Prensa Deportiva.xlsx"
    excel_path = "data/Prensa Deportiva.xlsx"
    color_app = "#7B1630"
else:
    # Tu nuevo archivo
    excel_path = "data/Prensa_Mundial.xlsx"
    color_app = "#1d4ed8"

st.sidebar.info(f"Usando base de datos: {excel_path}")

# --- CUERPO PRINCIPAL ---
st.markdown(f"<h1 style='text-align: center; color: {color_app};'>{modo}</h1>", unsafe_allow_html=True)

if not os.path.exists(excel_path):
    st.error(f"⚠️ El archivo no existe en la carpeta data: {excel_path}")
    st.info("Por favor, sube el archivo Excel a la carpeta 'data' en tu GitHub.")
else:
    try:
        # Cargamos el lector de tu carpeta 'core'
        reader = ExcelReader(excel_path)
        categorias = reader.get_categories()

        col1, col2 = st.columns([1, 2])

        with col1:
            st.subheader("Selección")
            seccion = st.selectbox("Categoría:", categorias)
            links = reader.get_links_by_category(seccion)
            link_final = st.selectbox("Noticia:", links)

        with col2:
            st.subheader("Resultado")
            if st.button("🚀 EXTRAER NOTICIA"):
                with st.spinner('Extrayendo...'):
                    resultado = extraer_contenido(link_final)
                    
                    if "error" in resultado:
                        st.error(f"Error: {resultado['error']}")
                    else:
                        st.text_input("Título:", value=resultado['titulo'])
                        st.text_area("Contenido:", value=resultado['contenido'], height=400)
                        st.success("✅ ¡Listo para copiar!")

    except Exception as e:
        st.error(f"Error al leer el Excel: {e}")

st.markdown("---")
st.caption("BG Extractor - Sistema Multi-Base")