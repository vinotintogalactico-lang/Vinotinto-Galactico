import streamlit as st
import pandas as pd
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# 1. ESTÉTICA PROFESIONAL (Centrado de Logo y Banner)
st.set_page_config(page_title="BG Extractor News", page_icon="⚽", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stImage > img { display: block; margin-left: auto; margin-right: auto; border-radius: 10px; }
    .title-panel { text-align: center; font-family: 'Arial'; font-weight: bold; padding: 10px; }
    .stCheckbox { background: #1e2130; padding: 10px; border-radius: 5px; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 2. LOGO Y BANNER CENTRADOS
if os.path.exists("banner-vinotinto.png"):
    st.image("banner-vinotinto.png", use_container_width=True)

col_l1, col_l2, col_l3 = st.columns([1, 1, 1])
with col_l2: # Esto centra el logo perfectamente
    if os.path.exists("Logo.jpg"):
        st.image("Logo.jpg", width=150)

# 3. MOTOR INTERNO (Para evitar errores de Importación)
class PanelExtractor:
    @staticmethod
    def leer_excel(ruta):
        if not os.path.exists(ruta): return None
        df = pd.read_excel(ruta, header=None)
        datos = {}
        cat_actual = "General"
        for _, row in df.iterrows():
            v = str(row[0]).strip()
            if v.startswith("http"):
                if cat_actual not in datos: datos[cat_actual] = []
                datos[cat_actual].append(v)
            elif v != "nan" and len(v) > 2:
                cat_actual = v
        return datos

    @staticmethod
    def extraer_texto(url):
        try:
            h = {'User-Agent': 'Mozilla/5.0'}
            r = requests.get(url, headers=h, timeout=10, verify=False)
            r.encoding = 'utf-8'
            s = BeautifulSoup(r.text, 'html.parser')
            t = s.find('h1').text.strip() if s.find('h1') else "Noticia"
            p = [p.text.strip() for p in s.find_all('p') if len(p.text.strip()) > 60]
            return {"t": t, "c": "\n\n".join(p)}
        except:
            return None

# 4. CONFIGURACIÓN DEL PANEL (Sidebar)
st.sidebar.header("🕹️ CONTROL DE MANDO")
proyecto = st.sidebar.radio("PROYECTO ACTIVO:", ["Vinotinto Galáctico", "Mundial 2026"])

if proyecto == "Vinotinto Galáctico":
    excel_path, color = "data/Prensa Deportiva.xlsx", "#7B1630"
else:
    excel_path, color = "data/Prensa_Mundial.xlsx", "#1d4ed8"

fecha_noticia = st.sidebar.date_input("FECHA DE NOTICIAS:", datetime.now())
st.markdown(f"<h1 class='title-panel' style='color: {color};'>{proyecto.upper()}</h1>", unsafe_allow_html=True)

# 5. PANEL DE TRABAJO MASIVO
datos = PanelExtractor.leer_excel(excel_path)

if datos:
    categorias = list(datos.keys())
    
    col_izq, col_der = st.columns([1, 2])
    
    with col_izq:
        st.subheader("📂 SECCIONES")
        secciones_sel = st.multiselect("Seleccione Categorías:", categorias, default=categorias[0] if categorias else [])
        
        links_mostrar = []
        for s in secciones_sel:
            links_mostrar.extend(datos[s])
        
        st.write(f"Noticias encontradas: {len(links_mostrar)}")
        
        # EL PANEL DE CHECKBOXES (Lo que tú pediste)
        st.markdown("### ✅ SELECCIÓN DE ENLACES")
        links_finales = []
        for i, url in enumerate(links_mostrar):
            if st.checkbox(f"Noticia {i+1}: {url[:50]}...", value=True, key=f"chk_{i}"):
                links_finales.append(url)

    with col_der:
        st.subheader("📝 MESA DE REDACCIÓN")
        if st.button("🚀 INICIAR EXTRACCIÓN MASIVA"):
            if not links_finales:
                st.warning("Seleccione al menos una noticia.")
            else:
                progress = st.progress(0)
                for i, url in enumerate(links_finales):
                    with st.expander(f"PROCESANDO: {url}", expanded=True):
                        res = PanelExtractor.extraer_texto(url)
                        if res:
                            st.write(f"**TITULAR:** {res['t']}")
                            st.text_area("CUERPO:", res['c'], height=200, key=f"txt_{i}")
                        else:
                            st.error("Error al extraer este enlace.")
                    progress.progress((i + 1) / len(links_finales))
                st.success("✅ PROCESO FINALIZADO")

else:
    st.error(f"Archivo no encontrado en: {excel_path}")

st.markdown("---")
st.markdown("<p style='text-align: center;'>BG EXTRACTOR PRO - PANEL DE PRODUCCIÓN YOUTUBE</p>", unsafe_allow_html=True)