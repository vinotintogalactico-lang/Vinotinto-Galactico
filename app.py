import streamlit as st
import pandas as pd
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# --- 1. ESTÉTICA Y DISEÑO DE PANEL (CSS PERSONALIZADO) ---
st.set_page_config(page_title="BG Extractor Pro", page_icon="⚽", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    /* Centrar logo y ajustar banner */
    [data-testid="stSidebarNav"] { background-image: none; }
    .sidebar-img { display: block; margin-left: auto; margin-right: auto; width: 150px; border-radius: 10px; }
    .banner-img { width: 100%; border-radius: 5px; margin-bottom: 20px; }
    .noticia-box { background-color: #1e2130; padding: 20px; border-radius: 10px; border-left: 5px solid #7B1630; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SIDEBAR: IDENTIDAD Y CONTROL ---
if os.path.exists("Logo.jpg"):
    st.sidebar.image("Logo.jpg", use_container_width=True)

st.sidebar.title("🎮 CONTROL DE MANDO")

# Selector de Proyecto
proyecto = st.sidebar.radio("MODO DE TRABAJO:", ["Vinotinto Galáctico", "Mundial 2026"])

if proyecto == "Vinotinto Galáctico":
    excel_path = "data/Prensa Deportiva.xlsx"
    tema_color = "#7B1630"
else:
    excel_path = "data/Prensa_Mundial.xlsx"
    tema_color = "#1d4ed8"

st.sidebar.markdown("---")

# Botón Verificador (Panel de Prensa original)
if st.sidebar.button("📋 ABRIR VERIFICADOR"):
    st.sidebar.info("Panel de Verificación Activo. Compruebe los enlaces en su ventana de prensa.")

# Filtro de fecha (Motor de veracidad)
fecha_filtro = st.sidebar.date_input("EXTRAER NOTICIAS DESDE:", datetime.now())

# --- 3. CLASES DE MOTOR (INTEGRADAS PARA EVITAR IMPORT ERROR) ---
class EngineReader:
    @staticmethod
    def cargar(ruta):
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

def motor_extractor(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        # verify=False para evitar el error de SSL en sitios como Telemundo
        r = requests.get(url, headers=headers, timeout=10, verify=False)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Extracción siguiendo tus requisitos de GitHub: Título, Fecha, Autor, Cuerpo
        titulo = soup.find('h1').text.strip() if soup.find('h1') else "Noticia sin Título"
        
        # Intento de autor y fecha (heurístico)
        autor = "Redacción"
        for meta in soup.find_all('meta'):
            if meta.get('name') == 'author': autor = meta.get('content')
            
        parrafos = [p.text.strip() for p in soup.find_all('p') if len(p.text.strip()) > 65]
        cuerpo = "\n\n".join(parrafos)
        
        return {"t": titulo, "a": autor, "c": cuerpo, "url": url}
    except Exception as e:
        return {"error": str(e)}

# --- 4. CUERPO PRINCIPAL DEL PANEL ---
if os.path.exists("banner-vinotinto.png"):
    st.image("banner-vinotinto.png", use_container_width=True)

st.markdown(f"<h1 style='text-align: center; color: {tema_color};'>{proyecto.upper()}</h1>", unsafe_allow_html=True)

db = EngineReader.cargar(excel_path)

if db:
    col_menu, col_trabajo = st.columns([1, 2])
    
    with col_menu:
        st.subheader("📂 PRENSA Y SECCIONES")
        secciones = st.multiselect("Filtrar por medios:", list(db.keys()))
        
        links_pool = []
        for s in secciones:
            links_pool.extend(db[s])
        
        if links_pool:
            st.markdown(f"**Enlaces cargados:** {len(links_pool)}")
            # SELECCIÓN MANUAL (Papas SIN salsa: valor inicial False)
            st.write("Seleccione las noticias para procesar:")
            links_seleccionados = []
            for i, link in enumerate(links_pool):
                if st.checkbox(f"{i+1}. {link[:60]}...", value=False, key=f"news_{i}"):
                    links_seleccionados.append(link)

    with col_trabajo:
        st.subheader("📝 MESA DE REDACCIÓN")
        if st.button("🚀 INICIAR EXTRACCIÓN AUTOMATIZADA"):
            if not links_seleccionados:
                st.warning("⚠️ Seleccione al menos una noticia en el menú izquierdo.")
            else:
                progress = st.progress(0)
                for idx, url in enumerate(links_seleccionados):
                    with st.expander(f"PROCESANDO: {url}", expanded=True):
                        res = motor_extractor(url)
                        if "error" not in res:
                            st.markdown(f"### {res['t']}")
                            st.caption(f"🖋️ Fuente/Autor: {res['a']} | 🔗 [Ver Original]({res['url']})")
                            st.text_area("Cuerpo de la Noticia:", res['c'], height=300, key=f"area_{idx}")
                        else:
                            st.error(f"Error de conexión en este link.")
                    progress.progress((idx + 1) / len(links_seleccionados))
                st.success("✅ PRODUCCIÓN FINALIZADA")
else:
    st.error(f"Base de datos no encontrada: {excel_path}")

st.markdown("---")
st.caption("BG EXTRACTOR PRO - ESTÁNDAR DE CALIDAD VINOTINTO GALÁCTICO")