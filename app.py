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

/* BANNER — proporciones YouTube 16:9 recortado a 1/3 alto */
.vg-banner-wrap {
    margin: -1rem -1rem 0 -1rem;
    overflow: hidden; position: relative; background: #0d0d0d;
    height: 160px;
}
.vg-banner-wrap img {
    width: 100%; height: 100%; display: block;
    object-fit: cover; object-position: center 30%;
}
.vg-banner-wrap::after {
    content: ''; position: absolute; bottom: 0; left: 0; right: 0;
    height: 40px; background: linear-gradient(transparent, #0e1117);
}

/* BOTONES MODO */
div[data-testid="stButton"] button {
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 1.2rem !important; letter-spacing: 3px !important;
    border: none !important; border-radius: 6px !important;
    width: 100% !important; padding: .7rem 1rem !important;
    transition: all .2s ease !important; color: white !important;
}

/* CATEGORÍAS SIDEBAR */
.cat-label {
    font-family: 'Bebas Neue', sans-serif; font-size: .95rem;
    letter-spacing: 2px; padding: .3rem 0 .1rem 0;
    border-bottom: 1px solid #2a2a2a;
    margin-top: .8rem; margin-bottom: .3rem;
}
.cat-vg  { color: #e05263; }
.cat-mun { color: #4caf50; }

/* TARJETA NOTICIA */
.news-card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 10px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1.2rem;
}
.news-card-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.4rem; letter-spacing: 1px;
    line-height: 1.25; margin-bottom: .5rem;
}
.news-card-title a { text-decoration: none; color: #fff; }
.news-card-title a:hover { color: var(--accent-color); }
.news-meta {
    display: flex; flex-wrap: wrap; gap: .5rem;
    font-size: .78rem; margin-bottom: .8rem;
}
.news-meta span {
    background: #21262d; border-radius: 20px;
    padding: .2rem .65rem; color: #aaa;
}
.news-meta span.highlight { color: #fff; font-weight: 600; }
.news-body {
    font-size: .93rem; color: #ccc; line-height: 1.75;
    border-top: 1px solid #21262d; padding-top: .8rem;
}
.news-divider { border: none; border-top: 1px solid #21262d; margin: 0; }
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════
def _b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

try:
    banner_b64  = _b64("banner-vinotinto.png")
    banner_html = f'<img src="data:image/png;base64,{banner_b64}" alt="banner">'
except Exception:
    banner_html = ""

try:
    logo_b64 = _b64("Logo.jpg")
    logo_src = f"data:image/jpeg;base64,{logo_b64}"
except Exception:
    logo_src = ""

# Leer el HTML de prensa deportiva una sola vez
prensa_html_content = None
for _p in [Path("Prensa Deportiva/Prensa_Deportiva.html"), Path("Prensa_Deportiva.html")]:
    if _p.exists():
        try:
            prensa_html_content = _p.read_bytes().decode("utf-8", errors="replace")
        except Exception:
            pass
        break

# ════════════════════════════════════════════════════════════
# ESTADO
# ════════════════════════════════════════════════════════════
if "modo" not in st.session_state:
    st.session_state.modo = "vg"
if "resultado" not in st.session_state:
    st.session_state.resultado = None

# ════════════════════════════════════════════════════════════
# BANNER
# ════════════════════════════════════════════════════════════
if banner_html:
    st.markdown(f'<div class="vg-banner-wrap">{banner_html}</div>', unsafe_allow_html=True)
st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# BOTONES DE MODO
# ════════════════════════════════════════════════════════════
modo = st.session_state.modo
col_vg, col_mun = st.columns(2)
with col_vg:
    if st.button("⚽  VINOTINTO GALÁCTICO", use_container_width=True, key="btn_vg"):
        st.session_state.modo = "vg"
        st.session_state.resultado = None
        st.rerun()
with col_mun:
    if st.button("🌍  MUNDIAL 2026", use_container_width=True, key="btn_mun"):
        st.session_state.modo = "mundial"
        st.session_state.resultado = None
        st.rerun()

modo   = st.session_state.modo
accent = "#e05263" if modo == "vg" else "#4caf50"

# Colores de los dos botones de modo
if modo == "vg":
    vg_bg, vg_sh  = "linear-gradient(135deg,#7a1a2e,#c0392b)", "0 4px 15px rgba(192,57,43,.6)"
    mu_bg, mu_sh  = "#1a1a1a", "none"
    vg_bo, mu_bo  = "none", "1px solid #444"
else:
    vg_bg, vg_sh  = "#1a1a1a", "none"
    mu_bg, mu_sh  = "linear-gradient(135deg,#1a3d1a,#2e7d32)", "0 4px 15px rgba(46,125,50,.6)"
    vg_bo, mu_bo  = "1px solid #444", "none"

st.markdown(f"""<style>
/* Botón VG */
div[data-testid="stColumn"]:nth-of-type(1) button[kind="secondary"]{{
    background:{vg_bg} !important;
    border:{vg_bo} !important;
    box-shadow:{vg_sh} !important;
    color:white !important;
}}
/* Botón Mundial */
div[data-testid="stColumn"]:nth-of-type(2) button[kind="secondary"]{{
    background:{mu_bg} !important;
    border:{mu_bo} !important;
    box-shadow:{mu_sh} !important;
    color:white !important;
}}
</style>""", unsafe_allow_html=True)

st.markdown("<hr style='border-color:#2a2a2a;margin:.6rem 0 1rem 0;'>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# IMPORTS SEGÚN MODO
# ════════════════════════════════════════════════════════════
if modo == "vg":
    from core.excel_reader   import load_sources
    from core.txt_exporter   import export_txt
    from core.html_exporter  import export_html
    from extractores.factory import get_extractor
    CATEGORY_ICONS = {
        "Real Madrid Masculino":       "👑",
        "Real Madrid Femenino":        "👑",
        "LaLiga":                      "🇪🇸",
        "Selección Española Masculina": "🇪🇸",
        "Selección Española Femenina":  "🇪🇸",
        "Vinotinto Masculina":         "🇻🇪",
        "Vinotinto Femenina":          "🇻🇪",
        "Liga FUTVE":                  "🇻🇪",
    }
    cat_css = "cat-vg"
else:
    from mundial.core.excel_reader   import load_sources
    from mundial.core.txt_exporter   import export_txt
    from mundial.core.html_exporter  import export_html
    from mundial.extractores.factory import get_extractor
    CATEGORY_ICONS = {
        "📺 TV / Canal":     "📺",
        "📰 Prensa Escrita": "📰",
        "💻 Digital":        "💻",
    }
    cat_css = "cat-mun"

# ════════════════════════════════════════════════════════════
# CARGAR FUENTES (cacheado por modo)
# ════════════════════════════════════════════════════════════
@st.cache_data(show_spinner=False)
def _load_vg():
    from core.excel_reader import load_sources as ls; return ls()

@st.cache_data(show_spinner=False)
def _load_mundial():
    from mundial.core.excel_reader import load_sources as ls; return ls()

try:
    sources  = _load_vg() if modo == "vg" else _load_mundial()
    excel_ok = True
except Exception as exc:
    sources, excel_ok, excel_error = {}, False, str(exc)

# ════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════
with st.sidebar:
    if logo_src:
        st.markdown(
            f'<div style="overflow:hidden;width:88%;margin:.5rem auto 1rem;'
            f'border-radius:50%;aspect-ratio:1/1;">'
            f'<img src="{logo_src}" style="width:100%;transform:scale(1.7);'
            f'transform-origin:center;display:block;" alt="Logo"></div>',
            unsafe_allow_html=True
        )
    st.markdown(f"## {'⚽ VG · Fuentes' if modo=='vg' else '🌍 MUNDIAL · Fuentes'}")

    if not excel_ok:
        st.error(f"❌ Error al leer el Excel:\n\n{excel_error}"); st.stop()

    selected: dict[str, list[dict]] = {}

    for cat, fuentes in sources.items():
        icon = CATEGORY_ICONS.get(cat, "📌")
        st.markdown(f'<div class="cat-label {cat_css}">{icon} {cat}</div>', unsafe_allow_html=True)
        cat_key  = cat.replace(" ","_").replace("/","_")
        todo_key = f"todo_{modo}_{cat_key}"
        fuentes_keys = []
        for idx, f in enumerate(fuentes):
            slug = urlparse(f["url"]).netloc.replace(".","_") + "_" + str(idx)
            chk_key = f"chk_{modo}_{cat_key}_{slug}"
            fuentes_keys.append((f, chk_key))

        def toggle_all(tk=todo_key, fk=[k for _,k in fuentes_keys]):
            v = st.session_state[tk]
            for k in fk: st.session_state[k] = v

        for f, k in fuentes_keys:
            if st.checkbox(f["nombre"], key=k):
                selected.setdefault(cat, []).append(f)
        st.checkbox("🔳 Seleccionar todo", key=todo_key, on_change=toggle_all)

    st.markdown("---")
    total_sel = sum(len(v) for v in selected.values())
    st.caption(f"**{total_sel}** fuente(s) seleccionada(s)")

# ════════════════════════════════════════════════════════════
# BARRA TÍTULO + BOTONES ACCIÓN
# ════════════════════════════════════════════════════════════
titulo_modo = "VINOTINTO GALÁCTICO" if modo == "vg" else "MUNDIAL 2026"
emoji_modo  = "⚽" if modo == "vg" else "🌍"

# Columnas: título | prensa deportiva (solo VG) | extraer
col_title, col_prensa, col_extraer = st.columns([3, 1, 1])

with col_title:
    st.markdown(f"""
    <div style="padding:.4rem 0 .2rem 0;">
      <div style="font-family:'Bebas Neue',sans-serif;font-size:2rem;
                  color:#fff;letter-spacing:3px;line-height:1;">
        {emoji_modo} NEWS EXTRACTOR · {titulo_modo}
      </div>
      <div style="background:{accent};color:#fff;font-size:.72rem;
                  padding:.15rem .65rem;border-radius:20px;letter-spacing:1px;
                  display:inline-block;margin-top:.3rem;">
        HOY: {date.today().strftime("%d / %m / %Y")}
      </div>
    </div>""", unsafe_allow_html=True)

with col_prensa:
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    if modo == "vg":
        # Ruta exacta según tu captura de carpetas
        path_html = Path("Prensa Deportiva/Prensa_Deportiva.html")
        if path_html.exists():
            import base64
            # Leemos el archivo y lo convertimos en un link "data"
            encoded_html = base64.b64encode(path_html.read_bytes()).decode()
            # Este código crea un botón real que abre el HTML en una pestaña nueva
            btn_code = f'''
            <a href="data:text/html;base64,{encoded_html}" target="_blank" style="text-decoration: none;">
                <div style="background: linear-gradient(135deg,#7a1a2e,#c0392b); color: white; 
                padding: 10px; border-radius: 6px; text-align: center; font-family: 'Bebas Neue', sans-serif;
                letter-spacing: 1px; box-shadow: 0 4px 15px rgba(192,57,43,.4); cursor: pointer;">
                    🗞️ PRENSA DEPORTIVA
                </div>
            </a>
            '''
            st.markdown(btn_code, unsafe_allow_html=True)
        else:
            st.error("Archivo no encontrado en la carpeta Prensa Deportiva")

st.markdown("<hr style='border-color:#2a2a2a;margin-top:.5rem;'>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# EXTRACCIÓN
# ════════════════════════════════════════════════════════════
if run:
    st.session_state.resultado = None
    all_noticias, all_log = [], []
    progress   = st.progress(0, text="Iniciando extracción…")
    status_box = st.empty()
    flat  = [(cat, f) for cat, fuentes in selected.items() for f in fuentes]
    total = len(flat)

    async def run_all():
        for i, (cat, f) in enumerate(flat):
            status_box.info(f"🔍 **{f['nombre']}** — {cat}")
            ext = get_extractor(f["nombre"], f["url"], cat)
            noticias, log = await ext.extract()
            all_noticias.extend(noticias)
            all_log.append(log)
            progress.progress((i+1)/total, text=f"{i+1}/{total} fuentes procesadas")

    asyncio.run(run_all())
    progress.empty(); status_box.empty()

    txt_path  = export_txt(all_noticias, all_log)
    html_path = export_html(all_noticias, all_log)
    st.session_state.resultado = {
        "noticias": all_noticias, "log": all_log,
        "txt_path": txt_path, "html_path": html_path, "modo": modo,
    }

# ════════════════════════════════════════════════════════════
# RESULTADOS
# ════════════════════════════════════════════════════════════
if st.session_state.resultado:
    res      = st.session_state.resultado
    noticias = res["noticias"]
    log      = res["log"]

    k1,k2,k3,k4 = st.columns(4)
    k1.metric("📰 Noticias extraídas",   len(noticias))
    k2.metric("✅ Fuentes con noticias", sum(1 for l in log if l["estado"]=="Correcto"))
    k3.metric("🕳️ Sin noticias hoy",     sum(1 for l in log if "sin noticias" in l["estado"].lower()))
    k4.metric("❌ Errores",              sum(1 for l in log if l["estado"]=="Error"))

    st.markdown("---")
    c1,c2 = st.columns(2)
    tp, hp = Path(res["txt_path"]), Path(res["html_path"])
    if tp.exists():
        c1.download_button("📥 Descargar noticias.txt",  data=tp.read_bytes(),
                           file_name="noticias.txt",  mime="text/plain")
    if hp.exists():
        c2.download_button("🌐 Descargar noticias.html", data=hp.read_bytes(),
                           file_name="noticias.html", mime="text/html")

    st.markdown("---")
    tabs_labels = [f"📰 Noticias ({len(noticias)})", "📋 Informe de control"]
    tab_objs = st.tabs(tabs_labels)

    # ── TAB NOTICIAS ────────────────────────────────────────
    with tab_objs[0]:
        if not noticias:
            st.warning("No se encontraron noticias del día en las fuentes seleccionadas.")
        for n in noticias:
            fuente   = n.get("fuente","")
            categoria= n.get("categoria","")
            fecha    = n.get("date","")
            autor    = n.get("author","") or "Redacción"
            titulo   = n.get("title","Sin título")
            url      = n.get("url","#")
            body     = n.get("body","")
            resumen  = body[:450] + ("…" if len(body)>450 else "")

            st.markdown(f"""
<div class="news-card">
  <div class="news-card-title" style="--accent-color:{accent}">
    <a href="{url}" target="_blank">{titulo}</a>
  </div>
  <div class="news-meta">
    <span class="highlight">📡 {fuente}</span>
    <span>{categoria}</span>
    <span>📅 {fecha}</span>
    <span>✍ {autor}</span>
    <span><a href="{url}" target="_blank" style="color:#4caf50;text-decoration:none;">🔗 Ver noticia</a></span>
  </div>
  <div class="news-body">{resumen}</div>
</div>""", unsafe_allow_html=True)

    # ── TAB INFORME ─────────────────────────────────────────
    with tab_objs[1]:
        for entry in log:
            icon = "✅" if entry["estado"]=="Correcto" else (
                   "⚠️" if "sin" in entry["estado"].lower() else "❌")
            err = f" — `{entry['error']}`" if entry.get("error") else ""
            st.markdown(
                f"{icon} **{entry['fuente']}** · "
                f"Encontradas:`{entry['encontradas']}` · "
                f"Extraídas:`{entry['extraidas']}` · "
                f"{entry['estado']}{err}"
            )


else:
    # ── PANTALLA DE BIENVENIDA ───────────────────────────────
    logo_html = (f'<img src="{logo_src}" style="width:110px;border-radius:12px;'
                 f'box-shadow:0 6px 20px rgba(0,0,0,.6);">'
                 if logo_src else '<div style="font-size:4rem;">⚽</div>')
    desc = ("Solo se extraerán noticias del día de hoy · Máximo 3 por fuente"
            if modo=="vg" else
            "41 fuentes · TV · Prensa · Digital · Solo noticias de hoy")
    st.markdown(f"""
    <div style="text-align:center;padding:3rem 0;color:#555;">
        {logo_html}
        <div style="font-family:'Bebas Neue',sans-serif;font-size:1.7rem;
                    letter-spacing:3px;color:{accent};margin-top:1.2rem;">
            SELECCIONA LAS FUENTES Y PULSA EXTRAER
        </div>
        <div style="font-size:.9rem;margin-top:.5rem;color:#666;">{desc}</div>
    </div>""", unsafe_allow_html=True)
