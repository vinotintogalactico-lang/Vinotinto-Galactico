import re

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

# Remove set_page_config as it might conflict if it's a subpage (Streamlit allows it but better to omit or change)
content = re.sub(r'st\.set_page_config\(.*?\)', '', content)

# Change Excel loading
content = content.replace(
    'sources = _load_sources()',
    'sources = load_sources(Path("data/Prensa_Mundial.xlsx"))'
)

# Replace colors
content = content.replace('#7a1a2e', '#ff004d')
content = content.replace('#c0392b', '#00ff85')

# Change title
content = content.replace('NEWS EXTRACTOR', 'MUNDIAL 2026')

# Change logo to World Cup
content = content.replace(
    'logo_src = f"data:image/jpeg;base64,{logo_b64}"',
    'logo_src = "https://upload.wikimedia.org/wikipedia/en/thumb/4/4b/2026_FIFA_World_Cup_logo.svg/1200px-2026_FIFA_World_Cup_logo.svg.png"'
)
content = content.replace('logo_b64 = _b64("Logo.jpg")', 'logo_b64 = ""')

# Disable "Prensa Deportiva" button section since it's for VG
content = re.sub(r'with col_btn_prensa:.*?with col_btn_extraer:', 'with col_btn_extraer:', content, flags=re.DOTALL)
content = re.sub(r'col_title, col_btn_prensa, col_btn_extraer = st\.columns\(\[3, 1, 1\]\)', 'col_title, col_btn_extraer = st.columns([3, 1])', content)

# Remove tabs "Panel de Prensa"
content = content.replace(', "🗞️ Panel de Prensa"', '')
content = re.sub(r'with tab_prensa:.*?_render_panel_prensa\(\)', '', content, flags=re.DOTALL)

with open("pages/2_🏆_Mundial_2026.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Página del Mundial creada exitosamente.")
