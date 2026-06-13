import streamlit as st
import pandas as pd
import os
import requests
from bs4 import BeautifulSoup
from PIL import Image

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="BG Extractor News", page_icon="⚽", layout="wide")

# 2. IDENTIDAD VISUAL (Banner y Logo de tu canal)
# Buscamos tus archivos originales banner-vinotinto.png y Logo.jpg
if os.path.exists("banner-vinotinto.png"):
    st.image("banner-vinotinto.png", use_container_width=True)

col_logo, col_vacio = st.columns([1, 5])
with col_logo:
    if os.path.exists("Logo.jpg"):
        st.image("Logo.jpg", width=120)

# 3. LÓGICA DE LECTURA DE EXCEL (Integrada para evitar ImportError)
def cargar_datos_excel(ruta):
    if not os.path.exists(ruta):
        return None
    try:
        # Leemos el Excel tal como lo tienes estructurado (una columna con secciones y links)
        df = pd.read_excel(ruta, header=None)
        datos = {}
        seccion_actual = "General"
        for index, row in df.iterrows():
            valor = str(row[0]).strip()
            if valor.startswith("http"):
                if seccion_actual not in datos:
                    datos[seccion_actual] = []
                datos[seccion_actual].append(valor)
            elif valor != "nan" and len(valor) > 2:
                seccion_actual = valor
        return datos
    except Exception as e:
        st.error(f"Error al leer el archivo Excel: {e}")
        return None

# 4. LÓGICA DE EXTRACCIÓN DE NOTICIAS
def extraer_noticia_mundial(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Buscamos el título principal
        titulo = soup.find('h1').text.strip() if soup.find('h1') else "Noticia sin título"
        
        # Buscamos los párrafos de texto (limpiando basura publicitaria)
        parrafos = [p.text.strip() for p in soup.find_all('p') if len(p.text.strip()) > 60]
        cuerpo = "\n\n".join(parrafos)
        
        return {"titulo": titulo, "contenido": cuerpo}
    except Exception as e:
        return {"error": str(e)}

# 5. PANEL DE CONTROL (Sidebar)
st.sidebar.title("⚽ Configuración")
st.sidebar.markdown("---")

# Selector de Proyecto para que no se mezcle lo de Vinotinto con lo del Mundial
proyecto = st.sidebar.radio(
    "Seleccione el Proyecto:",
    ["Vinotinto Galáctico", "Mundial 2026"]
)

# Definimos las rutas de los archivos según el proyecto
if proyecto == "Vinotinto Galáctico":
    archivo_excel = "data/Prensa Deportiva.xlsx"  # Tu archivo original
    color_titulo = "#7B1630"
else:
    archivo_excel = "data/Prensa_Mundial.xlsx"  # El nuevo archivo del Mundial
    color_titulo = "#1d4ed8"

st.sidebar.info(f"Trabajando en modo: {proyecto}")

# 6. CUERPO DE LA APLICACIÓN
st.markdown(f"<h1 style='text-align: center; color: {color_titulo};'>{proyecto}</h1>", unsafe_allow_html=True)
st.markdown("---")

datos_extractor = cargar_datos_excel(archivo_excel)

if datos_extractor is None:
    st.warning(f"⚠️ No se encontró el archivo: {archivo_excel} en la carpeta 'data/'.")
    st.info("Por favor, asegúrate de subir el archivo Excel a GitHub dentro de la carpeta 'data'.")
else:
    col_izq, col_der = st.columns([1, 2])
    
    with col_izq:
        st.subheader("📁 Categorías")
        secciones = list(datos_extractor.keys())
        seccion_sel = st.selectbox("Elija la Sección:", secciones)
        
        links = datos_extractor[seccion_sel]
        link_sel = st.selectbox("Elija el enlace de noticia:", links)

    with col_der:
        st.subheader("📝 Contenido Extraído")
        if st.button("🚀 EXTRAER NOTICIA"):
            with st.spinner('Procesando contenido...'):
                resultado = extraer_noticia_mundial(link_sel)
                
                if "error" in resultado:
                    st.error(f"No se pudo extraer: {resultado['error']}")
                else:
                    st.success("¡Extracción completa!")
                    st.text_input("Título:", value=resultado['titulo'])
                    st.text_area("Contenido para el video:", value=resultado['contenido'], height=450)
                    st.info("💡 Puedes copiar este texto para el guion de tu canal.")

# 7. PIE DE PÁGINA
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>BG Extractor - Sistema Vinotinto Galáctico</p>", unsafe_allow_html=True)