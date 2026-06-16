import os, time
os.environ['TZ'] = 'America/Caracas'
if hasattr(time, 'tzset'):
    time.tzset()

import asyncio, base64, json, logging, sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import streamlit as st
import streamlit.components.v1 as components

@st.cache_resource(show_spinner=False)
def _install_playwright():
    try:
        os.system(f"{sys.executable} -m playwright install chromium")
    except Exception as e:
        print(f"Error instalando playwright: {e}")

_install_playwright()
Path("output").mkdir(exist_ok=True)
logging.basicConfig(level=logging.INFO)

st.set_page_config(page_title="VG · Extractor de Noticias", page_icon="⚽", layout="wide")

# ════════════════════════════════════════════════════════════
# CSS
# ════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;600&display=swap');
[data-testid="stSidebarNav"] { display: none !important; }
section[data-testid="stSidebar"] > div:first-child { padding-top: 0.5rem; }
.vg-banner-wrap { margin: -1rem -1rem 0 -1rem; overflow: hidden; position: relative; background: #0d0d0d; height: 160px; }
.vg-banner-wrap img { width: 100%; height: 100%; display: block; object-fit: cover; object-position: center 30%; }
div[data-testid="stButton"] button { font-family: 'Bebas Neue', sans-serif !important; font-size: 1.2rem !important; letter-spacing: 3px !important; border: none !important; border-radius: 6px !important; width: 100% !important; padding: .7rem 1rem !important; transition: all .2s ease !important; color: white !important; }
.cat-label { font-family: 'Bebas Neue', sans-serif; font-size: .95rem; letter-spacing: 2px; padding: .3rem 0 .1rem 0; border-bottom: 1px solid #2a2a2a; margin-top: .8rem; margin-bottom: .3rem; }
.cat-vg  { color: #e05263; }
.news-card { background: #161b22; border: 1px solid #21262d; border-radius: 10px; padding: 1.4rem 1.6rem; margin-bottom: 1.2rem; }
.news-card-title { font-family: 'Bebas Neue', sans-serif; font-size: 1.4rem; letter-spacing: 1px; line-height: 1.25; margin-bottom: .5rem; }
.news-card-title a { text-decoration: none; color: #fff; }
.news-meta { display: flex; flex-wrap: wrap; gap: .5rem; font-size: .78rem; margin-bottom: .8rem; }
.news-meta span { background: #21262d; border-radius: 20px; padding: .2rem .65rem; color: #aaa; }
.news-meta span.highlight { color: #fff; font-weight: 600; }
.news-body { font-size: .93rem; color: #ccc; line-height: 1.75; border-top: 1px solid #21262d; padding-top: .8rem; }
</style>
""", unsafe_allow_html=True)

def _b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

try:
    banner_html = f'<div class="vg-banner-wrap"><img src="data:image/png;base64,{_b64("banner-vinotinto.png")}" alt="banner"></div>'
except: banner_html = ""
try:
    logo_src = f"data:image/jpeg;base64,{_b64('Logo.jpg')}"
except: logo_src = ""

if "modo" not in st.session_state: st.session_state.modo = "vg"
if "resultado" not in st.session_state: st.session_state.resultado = None

if banner_html: st.markdown(banner_html, unsafe_allow_html=True)
st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

modo = st.session_state.modo
col_vg, col_mun = st.columns(2)
with col_vg:
    if st.button("⚽  VINOTINTO GALÁCTICO", use_container_width=True, key="btn_vg"):
        st.session_state.modo = "vg"; st.session_state.resultado = None; st.rerun()
with col_mun:
    if st.button("🌍  MUNDIAL 2026", use_container_width=True, key="btn_mun"):
        st.session_state.modo = "mundial"; st.session_state.resultado = None; st.rerun()

accent = "#e05263" if modo == "vg" else "#4caf50"
emoji_modo = "⚽" if modo == "vg" else "🌍"
titulo_modo = "VINOTINTO GALÁCTICO" if modo == "vg" else "MUNDIAL 2026"

st.markdown(f"<hr style='border-color:#2a2a2a;margin:.6rem 0 1rem 0;'>", unsafe_allow_html=True)

if modo == "vg":
    from core.excel_reader import load_sources
    from core.txt_exporter import export_txt
    from core.html_exporter import export_html
    from extractores.factory import get_extractor
    CATEGORY_ICONS = {"Real Madrid Masculino": "👑", "Real Madrid Femenino": "👑", "LaLiga": "🇪🇸", "Vinotinto Masculina": "🇻🇪"}
    cat_css = "cat-vg"
else:
    from mundial.core.excel_reader import load_sources
    from mundial.core.txt_exporter import export_txt
    from mundial.core.html_exporter import export_html
    from mundial.extractores.factory import get_extractor
    CATEGORY_ICONS = {"Digital": "💻"}
    cat_css = "cat-mun"

sources = load_sources()
with st.sidebar:
    if logo_src: st.markdown(f'<div style="overflow:hidden;width:88%;margin:.5rem auto;border-radius:50%;aspect-ratio:1/1;"><img src="{logo_src}" style="width:100%;transform:scale(1.7);"></div>', unsafe_allow_html=True)
    selected = {}
    for cat, fuentes in sources.items():
        st.markdown(f'<div class="cat-label {cat_css}">{CATEGORY_ICONS.get(cat, "📌")} {cat}</div>', unsafe_allow_html=True)
        for f in fuentes:
            if st.checkbox(f["nombre"], key=f["url"]):
                selected.setdefault(cat, []).append(f)

total_sel = sum(len(v) for v in selected.values())

# BARRA ACCIÓN
col_title, col_prensa, col_extraer = st.columns([3, 1, 1])
with col_title:
    st.markdown(f"""
    <div style="padding:.4rem 0 .2rem 0;">
      <div style="font-family:'Bebas Neue',sans-serif;font-size:2rem; color:#fff;letter-spacing:3px;line-height:1;">
        {emoji_modo} NEWS EXTRACTOR · {titulo_modo}
      </div>
      <div style="background:{accent};color:#fff;font-size:.72rem; padding:.15rem .65rem;border-radius:20px;letter-spacing:1px; display:inline-block;margin-top:.3rem;">
        HOY: {date.today().strftime("%d / %m / %Y")}
      </div>
    </div>""", unsafe_allow_html=True)

with col_prensa:
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    if modo == "vg":
        f_path = Path("Prensa Deportiva/Prensa_Deportiva.html")
        if f_path.exists():
            data_p = base64.b64encode(f_path.read_bytes()).decode()
            st.markdown(f'<a href="data:text/html;base64,{data_p}" target="_blank" style="text-decoration:none;"><div style="background:linear-gradient(135deg,#7a1a2e,#c0392b);color:white;padding:10px;border-radius:6px;text-align:center;font-family:Bebas Neue;font-size:1.05rem;box-shadow:0 4px 15px rgba(0,0,0,0.3);cursor:pointer;">🗞️ PRENSA DEPORTIVA</div></a>', unsafe_allow_html=True)

with col_extraer:
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    run = st.button("⚡ EXTRAER NOTICIAS", disabled=total_sel == 0, use_container_width=True)

if run:
    all_noticias, all_log = [], []
    progress = st.progress(0, text="Iniciando extracción…")
    flat = [(cat, f) for cat, fuentes in selected.items() for f in fuentes]
    for i, (cat, f) in enumerate(flat):
        ext = get_extractor(f["nombre"], f["url"], cat)
        noticias, log = asyncio.run(ext.extract())
        all_noticias.extend(noticias); all_log.append(log)
        progress.progress((i+1)/len(flat))
    
    st.session_state.resultado = {"noticias": all_noticias, "log": all_log, "txt_path": export_txt(all_noticias, all_log), "html_path": export_html(all_noticias, all_log)}
    st.rerun()

if st.session_state.resultado:
    res = st.session_state.resultado
    tabs = st.tabs([f"📰 Noticias ({len(res['noticias'])})", "📋 Informe"])
    with tabs[0]:
        for n in res["noticias"]:
            st.markdown(f"""<div class="news-card"><div class="news-card-title"><a href="{n['url']}" target="_blank">{n['title']}</a></div><div class="news-meta"><span>📡 {n.get('fuente','')}</span><span>📅 {n.get('date','')}</span></div><div class="news-body">{n['body'][:600]}...</div></div>""", unsafe_allow_html=True)
    with tabs[1]:
        for l in res["log"]:
            icon = "✅" if l["estado"]=="Correcto" else "❌"
            st.write(f"{icon} **{l['fuente']}**: {l['estado']} ({l['extraidas']} noticias)")