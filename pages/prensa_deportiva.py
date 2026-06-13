"""
PÁGINA: Panel de Prensa Deportiva
Integra el HTML que ya tienes (Prensa_Deportiva.html)
Se accede como un tab/página en Streamlit
"""

import streamlit as st

st.set_page_config(page_title="Panel de Prensa | Vinotinto Galáctico", page_icon="📰", layout="wide")

# Cargar y mostrar el HTML
try:
    with open("static/Prensa_Deportiva.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    
    st.markdown(html_content, unsafe_allow_html=True)

except FileNotFoundError:
    st.error("""
    ❌ No se encontró el archivo `static/Prensa_Deportiva.html`
    
    **Solución:**
    1. Crea la carpeta `static/` en la raíz del proyecto
    2. Copia el archivo `Prensa_Deportiva.html` en esa carpeta
    3. Recarga la página
    """)

except Exception as e:
    st.error(f"❌ Error al cargar el panel: {e}")

# Footer informativo
st.markdown("""
---
<center style="font-size: 12px; color: #888;">
📌 Este panel es un navegador de accesos directos a las fuentes de prensa deportiva.<br>
Haz clic en cualquier link para abrir la fuente en una pestaña nueva.
</center>
""", unsafe_allow_html=True)
