import streamlit as st

# Configuración principal de la aplicación (solo se puede llamar una vez y debe ser el primer comando)
st.set_page_config(
    page_title="Extractor de Noticias VG",
    page_icon="⚽",
    layout="wide"
)

# Definición de las páginas del menú lateral
pages = [
    st.Page("pages/vg.py", title="Vinotinto Galáctico", icon="⚽"),
    st.Page("pages/mundial.py", title="Mundial 2026", icon="🌍")
]

# Inicializar y ejecutar la navegación
pg = st.navigation(pages)
pg.run()
