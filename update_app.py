import sys
import codecs

with codecs.open('app.py', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Buscamos y reemplazamos el boton mundial y su logica
import re

content = re.sub(
    r'has_mundial = "Mundial Global" in sources.*?run_mundial = st.button\("🏆 MUNDIAL 2026", type="primary", disabled=not has_mundial, use_container_width=True\)',
    'if st.button("🏆 MUNDIAL 2026", type="primary", use_container_width=True):\n        st.switch_page("pages/2_🏆_Mundial_2026.py")',
    content,
    flags=re.DOTALL
)

content = re.sub(
    r'if run or run_mundial:.*?if run_mundial:.*?else:.*?flat_sources = \[\(cat, f\) for cat, fuentes in selected.items\(\) for f in fuentes\].*?progress = st.progress\(0, text="Iniciando extracción…"\).*?total = len\(flat_sources\).*?status_box = st.empty\(\)',
    '''if run:
    st.session_state.resultado = None
    all_noticias: list[dict] = []
    all_log: list[dict] = []

    # Extraer lo que esté marcado en la barra lateral
    flat_sources = [(cat, f) for cat, fuentes in selected.items() for f in fuentes]
    progress = st.progress(0, text="Iniciando extracción…")
    total = len(flat_sources)
    status_box = st.empty()''',
    content,
    flags=re.DOTALL
)

with codecs.open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Actualizado.")
