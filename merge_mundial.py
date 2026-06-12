import codecs

with codecs.open('app.py', 'r', encoding='utf-8') as f:
    app_lines = f.readlines()

with codecs.open('pages/2_Mundial_2026.py', 'r', encoding='utf-8') as f:
    mundial_lines = f.readlines()

# Extraer el contenido de Mundial ignorando los imports y configuraciones iniciales
mundial_start = 0
for i, line in enumerate(mundial_lines):
    if "FALLBACK_LINKS =" in line:
        mundial_start = i
        break

mundial_code = "".join(mundial_lines[mundial_start:])
mundial_code = mundial_code.replace('st.switch_page("app.py")', 'st.session_state.current_page = "main"; st.rerun()')

# Encontrar donde empieza la UI principal en app.py
main_start = 0
for i, line in enumerate(app_lines):
    if "# ── SIDEBAR" in line:
        main_start = i
        break

header_code = "".join(app_lines[:main_start])
main_ui_code = "".join(app_lines[main_start:])

# Modificar el header para inicializar el estado
state_init = """
if "current_page" not in st.session_state:
    st.session_state.current_page = "main"

"""

header_code += state_init

# Reemplazar el switch_page en main_ui_code
main_ui_code = main_ui_code.replace(
    'st.switch_page("pages/2_Mundial_2026.py")',
    'st.session_state.current_page = "mundial"; st.rerun()'
)

# Indentar main_ui_code
main_ui_indented = ""
for line in main_ui_code.split('\n'):
    if line.strip() == "":
        main_ui_indented += "\n"
    else:
        main_ui_indented += "    " + line + "\n"

# Indentar mundial_code
mundial_indented = ""
for line in mundial_code.split('\n'):
    if line.strip() == "":
        mundial_indented += "\n"
    else:
        mundial_indented += "    " + line + "\n"

final_code = header_code + "if st.session_state.current_page == 'main':\n" + main_ui_indented + "elif st.session_state.current_page == 'mundial':\n" + mundial_indented

with codecs.open('app.py', 'w', encoding='utf-8') as f:
    f.write(final_code)

print("App merged successfully.")
