import streamlit as st

st.set_page_config(page_title="Panel de Prensa", page_icon="🗞️", layout="wide")

panel_css = """
<style>
/* Ocultar elementos de Streamlit que molestan */
[data-testid="stSidebar"] { display: none; }
header { visibility: hidden; }

.pd-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px,1fr)); gap: 20px; margin-top: 1rem; }
.pd-card { background:#1a060e; border:1px solid #4a1524; border-radius:12px; overflow:hidden;
           box-shadow:0 6px 12px rgba(0,0,0,0.3); transition: transform .3s, box-shadow .3s, border-color .3s; }
.pd-card:hover { transform:translateY(-5px); box-shadow:0 10px 20px rgba(122,28,55,0.35); border-color:#a62b4e; }
.pd-head { background:linear-gradient(135deg,#7a1c37 0%,#4a1122 100%);
           padding:12px 16px; font-size:14px; font-weight:700; text-transform:uppercase;
           letter-spacing:.5px; border-bottom:2px solid #ffcc00;
           display:flex; align-items:center; justify-content:space-between; color:#fff; }
.pd-head-ve { background:linear-gradient(135deg,#501023 0%,#7a1c37 100%); }
.pd-badge { background:rgba(255,255,255,0.15); padding:2px 8px; border-radius:20px;
            font-size:11px; color:#ffcc00; }
.pd-list { list-style:none; padding:8px 0; margin:0; }
.pd-list li { border-bottom:1px solid rgba(74,21,36,0.4); margin:0; padding:0; }
.pd-list li:last-child { border-bottom:none; }
.pd-link { display:flex; align-items:center; padding:10px 16px; color:#d0c2c6 !important;
           text-decoration:none !important; font-size:13.5px; font-weight:500;
           transition: background .2s, color .2s, padding-left .2s; }
.pd-link:hover { background:#35101d; color:#ffffff !important; padding-left:22px; }
.pd-link::before { content:"▶"; font-size:9px; color:#ffcc00; margin-right:10px; }
</style>
"""

secciones = [
    {"titulo": "👑 Real Madrid M.", "badge": 8, "ve": False, "links": [
        ("Real Madrid Web Oficial", "https://www.realmadrid.com/es-ES/futbol/primer-equipo-masculino/inicio"),
        ("Diario AS", "https://as.com/futbol/real_madrid/"),
        ("Mundo Deportivo", "https://www.mundodeportivo.com/futbol/real-madrid"),
        ("Defensa Central", "https://defensacentral.com/real_madrid"),
        ("Madridista Real", "https://madridistareal.com/real-madrid/"),
        ("Diario MARCA", "https://www.marca.com/futbol/real-madrid.html?intcmp=MENUESCU&s_kw=realmadrid"),
        ("Diario SPORT", "https://www.sport.es/es/real-madrid/"),
        ("Estadio Deportivo", "https://www.estadiodeportivo.com/futbol/real-madrid/"),
    ]},
    {"titulo": "👑 Real Madrid Fem.", "badge": 4, "ve": False, "links": [
        ("Real Madrid Fem. Oficial", "https://www.realmadrid.com/es-ES/futbol/primer-equipo-femenino/inicio"),
        ("Diario AS – Femenino", "https://as.com/futbol/real_madrid_femenino/"),
        ("Madridista Real – Femenino", "https://madridistareal.com/real-madrid-femenino/"),
        ("Diario MARCA – Liga F", "https://www.marca.com/futbol/futbol-femenino/primera-division.html?intcmp=MENUPROD&s_kw=futbol-femenino-liga-f"),
    ]},
    {"titulo": "🇪🇸 LaLiga EA Sports", "badge": 8, "ve": False, "links": [
        ("LaLiga Web Oficial", "https://www.laliga.com/laliga-easports"),
        ("Diario AS – Primera División", "https://as.com/futbol/primera/"),
        ("Diario MARCA – LaLiga", "https://www.marca.com/futbol/primera-division.html?intcmp=MENUMIGA&s_kw=laliga-ea-sports"),
        ("Mundo Deportivo – LaLiga", "https://www.mundodeportivo.com/futbol/laliga"),
        ("Diario SPORT – LaLiga", "https://www.sport.es/es/laliga/"),
        ("Defensa Central", "https://defensacentral.com/"),
        ("Estadio Deportivo Fútbol", "https://www.estadiodeportivo.com/futbol/"),
        ("Meridiano – Fútbol Español", "https://meridiano.net/futbol/espanol"),
    ]},
    {"titulo": "🇪🇸 Selección España", "badge": 2, "ve": False, "links": [
        ("Diario MARCA – Selección", "https://www.marca.com/futbol/seleccion.html?intcmp=MENUMIGA&s_kw=seleccion-espanola"),
        ("Diario AS – Selección", "https://as.com/futbol/seleccion/"),
    ]},
    {"titulo": "🇪🇸 Selección España Fem.", "badge": 3, "ve": False, "links": [
        ("Diario MARCA – Femenino", "https://www.marca.com/futbol/futbol-femenino.html?intcmp=MENUMIGA&s_kw=futbol-femenino"),
        ("Diario AS – Fútbol Femenino", "https://as.com/futbol/femenino/"),
        ("Mundo Deportivo – Femenino", "https://www.mundodeportivo.com/futbol/femenino"),
    ]},
    {"titulo": "🇻🇪 La Vinotinto", "badge": 6, "ve": True, "links": [
        ("FVF – Federación Venezolana", "https://www.fvf.com.ve/"),
        ("Meridiano – La Vinotinto", "https://meridiano.net/futbol/la-vinotinto"),
        ("Líder en Deportes – Vinotinto", "https://www.liderendeportes.com/seccion/vinotinto/"),
        ("LaVinotinto.com – Selección", "https://www.lavinotinto.com/category/futbol-nacional/la-vinotinto/"),
        ("Balonazos – Fútbol Vinotinto", "https://www.balonazos.com/category/noticias/futbol-vinotinto/"),
        ("LaVinotinto.com – FVF", "https://www.lavinotinto.com/category/futbol-nacional/fvf/"),
    ]},
    {"titulo": "🇻🇪 Liga FUTVE", "badge": 4, "ve": True, "links": [
        ("Meridiano – Fútbol Venezolano", "https://meridiano.net/futbol/futbol-venezolano"),
        ("Líder en Deportes – Liga FUTVE", "https://www.liderendeportes.com/seccion/futbol/futve/"),
        ("LaVinotinto.com – Primera División", "https://www.lavinotinto.com/category/futbol-nacional/primera-division/"),
        ("Balonazos – 1ra División", "https://www.balonazos.com/category/noticias/1ra-division/"),
    ]},
    {"titulo": "🇻🇪 Venezuela Fem.", "badge": 3, "ve": True, "links": [
        ("Líder en Deportes – Femenino", "https://www.liderendeportes.com/seccion/futbol/femenino/"),
        ("LaVinotinto.com – Femenino", "https://www.lavinotinto.com/category/futbol-nacional/futbol-femenino/"),
        ("Balonazos – Femenino", "https://www.balonazos.com/category/noticias/femenino/"),
    ]},
]

st.markdown("<h2 style='text-align:center;color:#fff;'>🗞️ PANEL DE PRENSA</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:#999;'>Abre esta pestaña en una ventana paralela para revisar las noticias mientras se extraen.</p>", unsafe_allow_html=True)

cards_html = ""
for sec in secciones:
    head_class = "pd-head pd-head-ve" if sec["ve"] else "pd-head"
    links_html = "".join(
        f'<li><a class="pd-link" href="{url}" target="_blank">{nombre}</a></li>'
        for nombre, url in sec["links"]
    )
    cards_html += f"""
    <div class="pd-card">
        <div class="{head_class}">
            <span>{sec['titulo']}</span>
            <span class="pd-badge">{sec['badge']}</span>
        </div>
        <ul class="pd-list">{links_html}</ul>
    </div>"""

st.markdown(panel_css + f'<div class="pd-grid">{cards_html}</div>', unsafe_allow_html=True)
