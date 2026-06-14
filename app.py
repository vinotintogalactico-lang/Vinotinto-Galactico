import os
import time

# Forzar zona horaria de Venezuela para todo el servidor (solo afecta Linux/Streamlit)
os.environ['TZ'] = 'America/Caracas'
if hasattr(time, 'tzset'):
    time.tzset()

import asyncio
import base64
import logging
import subprocess
import sys
from datetime import datetime, date
from pathlib import Path
from urllib.parse import urlparse

import streamlit as st

# ── Instalar Playwright Chromium automáticamente (necesario en Streamlit Cloud) ──
@st.cache_resource(show_spinner=False)
def _install_playwright():
    try:
        os.system(f"{sys.executable} -m playwright install chromium")
    except Exception as e:
        print(f"Error instalando playwright: {e}")

_install_playwright()

# Crear carpeta output si no existe (en el servidor)
Path("output").mkdir(exist_ok=True)

from core.excel_reader import load_sources
from core.txt_exporter import export_txt
from core.html_exporter import export_html
from extractores.factory import get_extractor

logging.basicConfig(level=logging.INFO)

CATEGORY_ICONS = {
    "Real Madrid Masculino":      "👑",
    "Real Madrid Femenino":       "👑",
    "LaLiga":                     "🇪🇸",
    "Selección Española Masculina": "🇪🇸",
    "Selección Española Femenina":  "🇪🇸",
    "Vinotinto Masculina":        "🇻🇪",
    "Vinotinto Femenina":         "🇻🇪",
    "Liga FUTVE":                 "🇻🇪",
}

st.set_page_config(page_title="Vinotinto Galáctico · Extractor", page_icon="⚽", layout="wide")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;600&display=swap');

/* ─── BANNER (ocupa todo el ancho del área principal) ─── */
.vg-banner-wrap {
    margin: -1rem auto 0 auto;
    max-width: 1080px;
    position: relative;
    background: #0d0d0d;
    display: flex;
    justify-content: center;
}
.vg-banner-wrap img {
    width: 100%;
    height: 25vw;
    max-height: 300px;
    min-height: 180px;
    object-fit: cover;
    object-position: center center;
    display: block;
}
/* Sombra inferior para que el banner no corte bruscamente */
.vg-banner-wrap::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 50px;
    background: linear-gradient(to bottom, transparent, #0d0d0d);
}

/* ─── BARRA DE TÍTULO (debajo del banner) ─── */
.vg-titlebar {
    background: linear-gradient(135deg, #0d0d0d 0%, #1a0810 50%, #0d0d0d 100%);
    border-bottom: 3px solid #c0392b;
    padding: .8rem 1.5rem;
    margin: 0 -1rem 1.5rem -1rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
}
.vg-titlebar h1 {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.2rem; color: #fff; letter-spacing: 3px; margin: 0;
}
.vg-titlebar .date-badge {
    background: #7a1a2e; color: #fff; font-size: .72rem;
    padding: .2rem .7rem; border-radius: 20px; letter-spacing: 1px; margin-top: .3rem;
    display: inline-block;
}

/* ─── CATEGORÍAS (sidebar) ─── */
.cat-label {
    font-family: 'Bebas Neue', sans-serif; font-size: 1rem;
    letter-spacing: 2px; color: #c0392b;
    padding: .3rem 0 .1rem 0; border-bottom: 1px solid #2a2a2a;
    margin-top: .8rem; margin-bottom: .3rem;
}

/* ─── BOTÓN EXTRAER (ajuste fino para columna derecha) ─── */
/* Botón Secundario (Vinotinto) - Extraer Noticias */
div[data-testid="stButton"] button[kind="secondary"] {
    background: linear-gradient(135deg, #7a1a2e, #c0392b) !important;
    border: none !important;
    border-radius: 6px !important;
    width: 100% !important;
    box-shadow: 0 4px 15px rgba(192,57,43,0.4) !important;
    transition: all 0.2s ease !important;
    padding: 0.6rem 0.5rem !important;
}
div[data-testid="stButton"] button[kind="secondary"] p {
    color: white !important;
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 16px !important;
    font-weight: 400 !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
    margin: 0 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}
div[data-testid="stButton"] button[kind="secondary"]:hover {
    box-shadow: 0 6px 20px rgba(192,57,43,0.7) !important;
    transform: translateY(-1px);
}

/* Botón Primario (Verde Mundial) */
div[data-testid="stButton"] button[kind="primary"] {
    background: linear-gradient(135deg, #009e4f, #00733a) !important;
    border: none !important;
    border-radius: 6px !important;
    width: 100% !important;
    box-shadow: 0 4px 15px rgba(0,158,79,0.4) !important;
    transition: all 0.2s ease !important;
    padding: 0.6rem 0.5rem !important;
}
div[data-testid="stButton"] button[kind="primary"] p {
    color: white !important;
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 16px !important;
    font-weight: 400 !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
    margin: 0 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}
div[data-testid="stButton"] button[kind="primary"]:hover {
    box-shadow: 0 6px 20px rgba(0,158,79,0.7) !important;
    transform: translateY(-1px);
}

/* ─── TARJETAS DE NOTICIAS ─── */
.news-card {
    background: #161616; border: 1px solid #2a2a2a;
    border-left: 4px solid #7a1a2e; border-radius: 4px;
    padding: 1.2rem 1.5rem; margin-bottom: 1.2rem;
}
.news-card .nc-meta { font-size: .72rem; color: #888; margin-bottom: .4rem; display: flex; gap: .8rem; flex-wrap: wrap; }
.news-card .nc-cat { color: #c0392b; font-weight: 600; }
.news-card h3 { font-size: 1.05rem; color: #eee; margin: .3rem 0; }
.news-card .nc-subtitle { color: #aaa; font-size: .9rem; font-style: italic; margin-bottom: .5rem; }
.news-card .nc-byline { font-size: .78rem; color: #666; margin-bottom: .8rem; }
.news-card .nc-body { font-size: .88rem; color: #c8c8c8; line-height: 1.7; }
</style>
""", unsafe_allow_html=True)

# ── Cargar imágenes en base64 ─────────────────────────────────────────────────
def _b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

try:
    banner_b64 = _b64("banner-vinotinto.png")
    banner_mime = "image/png"
    banner_html = f'<img src="data:{banner_mime};base64,{banner_b64}" alt="Vinotinto Galáctico">'
except Exception:
    banner_html = ""

try:
    logo_b64 = _b64("Logo.jpg")
    logo_src = f"data:image/jpeg;base64,{logo_b64}"
except Exception:
    logo_src = ""

# ── BANNER (ancho completo, como YouTube) ────────────────────────────────────
if banner_html:
    st.markdown(f'<div class="vg-banner-wrap">{banner_html}</div>', unsafe_allow_html=True)

# ── CARGA DE FUENTES (necesaria antes del sidebar y del botón) ────────────────
@st.cache_data(show_spinner=False)
def _load_sources():
    return load_sources()

try:
    sources = _load_sources()
    excel_ok = True
except Exception as exc:
    sources = {}
    excel_ok = False
    excel_error = str(exc)


if "current_page" not in st.session_state:
    st.session_state.current_page = "main"

if st.session_state.current_page == 'main':
    # ── SIDEBAR (solo checkboxes + logo) ─────────────────────────────────────────
    with st.sidebar:
        if logo_src:
            st.markdown(
                f'<div style="overflow:hidden;width:90%;margin:0.5rem auto 1rem auto;'
                f'border-radius:50%;aspect-ratio:1/1;">'
                f'<img src="{logo_src}" style="width:100%;transform:scale(1.7);'
                f'transform-origin:center center;display:block;" alt="Logo"></div>',
                unsafe_allow_html=True
            )

        st.markdown("## 📰 Fuentes")

        if not excel_ok:
            st.error(f"❌ Error al leer el Excel:\n\n{excel_error}")
            st.stop()

        selected: dict[str, list[dict]] = {}

        for cat, fuentes in sources.items():
            icon = CATEGORY_ICONS.get(cat, "📌")
            st.markdown(f'<div class="cat-label">{icon} {cat}</div>', unsafe_allow_html=True)

            cat_key = cat.replace(" ", "_")
            todo_key = f"todo_{cat_key}"

            fuentes_keys = []
            for idx, f in enumerate(fuentes):
                url_slug = urlparse(f["url"]).netloc.replace(".", "_")
                path_slug = urlparse(f["url"]).path.strip("/").replace("/", "_")
                chk_key = f"chk_{cat_key}_{url_slug}_{path_slug}_{idx}"
                fuentes_keys.append((f, chk_key))

            def toggle_all(tk=todo_key, fk=[k for _, k in fuentes_keys]):
                if tk in st.session_state:
                    val = st.session_state[tk]
                    for key in fk:
                        st.session_state[key] = val

            for f, k in fuentes_keys:
                if st.checkbox(f["nombre"], key=k):
                    selected.setdefault(cat, []).append(f)

            st.checkbox("🔳 Seleccionar todo", key=todo_key, on_change=toggle_all)

        st.markdown("---")
        total_sel = sum(len(v) for v in selected.values())
        st.caption(f"**{total_sel}** fuente(s) seleccionada(s)")

    # ── BARRA DE TÍTULO + BOTONES (en el área principal) ───────────────────
    col_title, col_btn_mundial, col_btn_prensa, col_btn_extraer = st.columns([1.5, 0.9, 1.2, 1.2])

    with col_title:
        st.markdown(f"""
        <div style="padding:.4rem 0 .2rem 0;">
            <div style="font-family:'Bebas Neue',sans-serif;font-size:2.2rem;
                        color:#fff;letter-spacing:3px;line-height:1;">
                NEWS EXTRACTOR
            </div>
            <div style="background:#7a1a2e;color:#fff;font-size:.72rem;
                        padding:.2rem .7rem;border-radius:20px;letter-spacing:1px;
                        display:inline-block;margin-top:.3rem;box-shadow:0 2px 8px rgba(0,0,0,0.4);">
                HOY: {date.today().strftime("%d / %m / %Y")}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Buscar el HTML para el botón
    paths = [
        Path("Prensa_Deportiva.html"),
        Path("Prensa Deportiva/Prensa_Deportiva.html"),
        Path("Prensa Deportiva/Prensa_Deportiva.html").resolve(),
        Path("VG_Extractor/Prensa Deportiva/Prensa_Deportiva.html"),
        Path("../Prensa Deportiva/Prensa_Deportiva.html")
    ]

    html_content = None
    for p in paths:
        if p.exists():
            try:
                html_content = p.read_bytes()
                break
            except Exception:
                pass

    with col_btn_mundial:
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        if st.button("🏆 MUNDIAL 2026", type="primary", use_container_width=True):
            st.session_state.current_page = "mundial"; st.rerun()

    with col_btn_prensa:
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        if html_content:
            import json
            import streamlit.components.v1 as components
            html_str = html_content.decode('utf-8', errors='replace')
            html_json = json.dumps(html_str)

            button_html = f"""
            <style>
            @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&display=swap');
            body {{ margin: 0; padding: 0; background: transparent; overflow: hidden; display: flex; align-items: center; justify-content: center; height: 100%; }}
            button {{
                background: linear-gradient(135deg, #7a1a2e, #c0392b);
                color: white; 
                border: none; 
                padding: 0.6rem 0.5rem;
                margin: 0;
                font-family: 'Bebas Neue', sans-serif; 
                font-size: 16px; 
                font-weight: 400;
                letter-spacing: 1px; 
                border-radius: 6px; 
                cursor: pointer;
                width: 100%; 
                height: 100%;
                box-shadow: 0 4px 15px rgba(192,57,43,0.4);
                transition: all 0.2s ease;
                box-sizing: border-box;
                text-transform: uppercase;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }}
            button:hover {{ box-shadow: 0 6px 20px rgba(192,57,43,0.7); transform: translateY(-1px); }}
            </style>
            <button onclick='openPanel()'>🗞️ PRENSA DEPORTIVA</button>
            <script>
            function openPanel() {{
                var content = {html_json};
                var newWin = window.open("", "_blank");
                if (newWin) {{
                    newWin.document.open();
                    newWin.document.write(content);
                    newWin.document.close();
                }} else {{
                    alert("Por favor habilita las ventanas emergentes (pop-ups) para ver la prensa.");
                }}
            }}
            </script>
            """
            components.html(button_html, height=75)
        else:
            st.markdown(
                f'<div style="display:block; background:#161616; border: 1px solid #2a2a2a; '
                f'color:#666; padding:0.6rem; text-align:center; border-radius:6px; '
                f'font-family:\'Bebas Neue\',sans-serif; font-size:1.1rem; letter-spacing:1px;">'
                f'❌ SIN HTML</div>', 
                unsafe_allow_html=True
            )

    with col_btn_extraer:
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        run = st.button("⚡ EXTRAER NOTICIAS", type="secondary", disabled=total_sel == 0, use_container_width=True)

    st.markdown("<hr style='border-color:#2a2a2a;margin-top:.5rem;'>", unsafe_allow_html=True)

    # ── EXTRACCIÓN ────────────────────────────────────────────────────────────────
    if "resultado" not in st.session_state:
        st.session_state.resultado = None

    if run:
        st.session_state.resultado = None
        all_noticias: list[dict] = []
        all_log: list[dict] = []

        # Extraer lo que esté marcado en la barra lateral
        flat_sources = [(cat, f) for cat, fuentes in selected.items() for f in fuentes]
        progress = st.progress(0, text="Iniciando extracción…")
        total = len(flat_sources)
        status_box = st.empty()

        async def run_all():
            for i, (cat, f) in enumerate(flat_sources):
                status_box.info(f"🔍 Procesando: **{f['nombre']}** — {cat}")
                extractor = get_extractor(f["nombre"], f["url"], cat)
                noticias, log = await extractor.extract()
                all_noticias.extend(noticias)
                all_log.append(log)
                progress.progress((i + 1) / total, text=f"{i+1}/{total} fuentes procesadas")

        asyncio.run(run_all())
        progress.empty()
        status_box.empty()

        txt_path = export_txt(all_noticias, all_log)
        html_path = export_html(all_noticias, all_log)

        st.session_state.resultado = {
            "noticias": all_noticias,
            "log": all_log,
            "txt_path": txt_path,
            "html_path": html_path,
        }

    # ── RESULTADOS ────────────────────────────────────────────────────────────────
    import streamlit.components.v1 as components

    def _render_panel_prensa():
        paths = [
            Path("Prensa_Deportiva.html"),
            Path("Prensa Deportiva/Prensa_Deportiva.html"),
            Path("Prensa Deportiva/Prensa_Deportiva.html").resolve(),
            Path("VG_Extractor/Prensa Deportiva/Prensa_Deportiva.html"),
            Path("../Prensa Deportiva/Prensa_Deportiva.html")
        ]

        html_content = None
        for p in paths:
            if p.exists():
                try:
                    html_content = p.read_text(encoding="utf-8")
                    break
                except Exception:
                    pass

        if html_content:
            components.html(html_content, height=800, scrolling=True)
        else:
            st.error("No se encontró el archivo Prensa_Deportiva.html. Por favor, asegúrate de haberlo subido a GitHub junto con los demás archivos.")

    if st.session_state.resultado:
        res = st.session_state.resultado
        noticias = res["noticias"]
        log = res["log"]
        txt_path: Path = res["txt_path"]
        html_path: Path = res["html_path"]

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("📰 Noticias extraídas", len(noticias))
        k2.metric("✅ Fuentes con noticias", sum(1 for l in log if l["estado"] == "Correcto"))
        k3.metric("🕳️ Sin noticias hoy", sum(1 for l in log if "sin noticias" in l["estado"].lower()))
        k4.metric("❌ Errores", sum(1 for l in log if l["estado"] == "Error"))

        st.markdown("---")

        col1, col2 = st.columns(2)
        if txt_path.exists():
            col1.download_button("📥 Descargar noticias.txt", data=txt_path.read_bytes(),
                                 file_name="noticias.txt", mime="text/plain")
        if html_path.exists():
            col2.download_button("🌐 Descargar noticias.html", data=html_path.read_bytes(),
                                 file_name="noticias.html", mime="text/html")

        st.markdown("---")
        tab_news, tab_log, tab_prensa = st.tabs([f"📰 Noticias ({len(noticias)})", "📋 Informe de control", "🗞️ Panel de Prensa"])

        with tab_news:
            if not noticias:
                st.warning("No se encontraron noticias del día en las fuentes seleccionadas.")
                st.info("No se encontraron noticias con los filtros actuales en las fuentes seleccionadas.")
            for n in noticias:
                with st.container():
                    n_title = n.get("title", "Sin título")
                    n_url = n.get("url", "#")
                    n_imagen = n.get("imagen")
                    n_fuente = n.get("fuente", "")
                    n_categoria = n.get("categoria", "")
                    n_date = n.get("date", "")
                    n_author = n.get("author", "")
                    n_body = n.get("body", "")

                    cols = st.columns([1, 4])
                    if n_imagen:
                        cols[0].image(n_imagen, use_container_width=True)

                    with cols[1]:
                        st.markdown(f"#### [{n_title}]({n_url})")
                        st.markdown(f"<div style='color:#c0392b; font-size:1.05rem; font-weight:600; margin-bottom:0.4rem; font-family:sans-serif;'>📌 Fuente: {n_fuente} &nbsp;|&nbsp; Categoría: {n_categoria} &nbsp;|&nbsp; Fecha: {n_date} &nbsp;|&nbsp; Autor: {n_author}</div>", unsafe_allow_html=True)
                        resumen = n_body[:400] + ('...' if len(n_body) > 400 else '')
                        st.markdown(f"<div style='font-size:0.95rem; color:#ddd; line-height:1.5;'>{resumen}</div>", unsafe_allow_html=True)
                    st.markdown("---")

        with tab_log:
            for entry in log:
                icon = "✅" if entry["estado"] == "Correcto" else ("⚠️" if "sin" in entry["estado"].lower() else "❌")
                err = f" — `{entry['error']}`" if entry.get("error") else ""
                st.markdown(f"{icon} **{entry['fuente']}** · Encontradas: `{entry['encontradas']}` · Extraídas: `{entry['extraidas']}` · {entry['estado']}{err}")

        with tab_prensa:
            _render_panel_prensa()

    else:
        # Estado vacío — Logo en lugar de la pelota fea
        logo_center = f'<img src="{logo_src}" style="width:100px;border-radius:12px;box-shadow:0 6px 20px rgba(0,0,0,0.6);">' if logo_src else '<div style="font-size:4rem;">⚽</div>'
        st.markdown(f"""
        <div style="text-align:center; padding: 4rem 0; color: #555;">
            {logo_center}
            <div style="font-family:'Bebas Neue',sans-serif; font-size:1.6rem;
                        letter-spacing:3px; color:#7a1a2e; margin-top:1rem;">
                SELECCIONA LAS FUENTES Y PULSA EXTRAER
            </div>
            <div style="font-size:.9rem; margin-top:.5rem; color:#666;">
                Solo se extraerán noticias del día de hoy · Máximo 3 por fuente
            </div>
        </div>
        """, unsafe_allow_html=True)
elif st.session_state.current_page == 'mundial':
    FALLBACK_LINKS = [
        'https://www.telemundodeportes.com/copa-mundial-fifa-2026', 'https://www.tudn.com/mundial-2026', 
        'https://www.tvazteca.com/aztecadeportes/', 'https://televen.com/elnoticiero/copa-mundial-de-la-fifa-2026/', 
        'https://noticias.caracoltv.com/golcaracol/mundial-2026', 'https://www.noticiasrcn.com/deportes', 
        'https://www.tycsports.com/mundial', 'https://mitelefe.com/deportes/', 'https://www.directvsports.com/',  
        'https://elcanaldelfutbol.com/', 'https://www.chilevision.cl/deportes', 'https://www.t13.cl/deportes', 
        'https://latinanoticias.pe/deportes', 'https://www.rtve.es/play/deportes/', 
        'https://www.liderendeportes.com/noticias/futbol/mundial-2026/', 'https://meridiano.net/futbol/futbol-internacional/', 
        'https://www.winsports.co/futbol-internacional/', 'https://www.futbolred.com/futbol-internacional', 
        'https://www.record.com.mx/futbol', 'https://www.mediotiempo.com/futbol', 'https://www.foxsports.com.mx/', 
        'https://www.ole.com.ar/mundial/mundial-2026', 'https://www.elgrafico.com.ar/', 'https://redgol.cl/mundial/', 
        'https://www.alairelibre.cl/noticias/deportes/futbol/mundial/', 'https://depor.com/futbol-internacional/', 
        'https://libero.pe/futbol-internacional/', 'https://www.elpais.com.uy/ovacion/futbol', 
        'https://studiofutbol.com.ec/', 'https://www.diez.hn/', 
        'https://www.marca.com/futbol/mundial.html', 'https://as.com/futbol/mundial/', 
        'https://www.mundodeportivo.com/futbol/mundial', 'https://www.sport.es/es/', 
        'https://www.relevo.com/futbol/', 'https://espndeportes.espn.com/futbol/',  
        'https://www.infobae.com/deportes/', 'https://www.clarosports.com/futbol/mundial/', 
        'https://www.eltiempo.com/deportes/futbol-internacional', 'https://www.latercera.com/canal/el-deportivo/', 
        'https://www.eluniversal.com.mx/deportes/'
    ]

    def _friendly_name(u: str) -> str:
        domain = urlparse(u).netloc.replace("www.", "")
        return domain.split(".")[0].title()

    sources_dict = {"Mundial Global": [{"nombre": _friendly_name(url), "url": url} for url in FALLBACK_LINKS]}

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;600&display=swap');

    /* Fondo general */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        background: #080808 !important;
    }
    [data-testid="stSidebar"] {
        background: #0a0a0a !important;
        border-right: 1px solid #1a1a1a;
    }

    /* Banner */
    .wc-hero {
        background: linear-gradient(160deg, #0a0a0a 0%, #0d1f15 50%, #0a0a0a 100%);
        border-bottom: 2px solid #00ff85;
        padding: 1.5rem 2rem 1rem;
        margin: -1rem -1rem 1.5rem -1rem;
        display: flex;
        align-items: center;
        gap: 1.5rem;
    }
    .wc-hero img.wc-logo {
        height: 80px;
        width: auto;
        filter: drop-shadow(0 0 10px rgba(0,255,133,0.5));
    }
    .wc-hero .wc-title {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 3rem;
        color: #fff;
        letter-spacing: 4px;
        line-height: 1;
        text-shadow: 0 0 20px rgba(0,255,133,0.3);
    }
    .wc-hero .wc-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: .85rem;
        color: #00ff85;
        letter-spacing: 2px;
        margin-top: .3rem;
    }

    /* Sidebar labels */
    .wc-cat-label {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.2rem;
        letter-spacing: 2px;
        color: #00ff85;
        padding: .4rem 0 .1rem 0;
        border-bottom: 1px solid #1e1e1e;
        margin-top: .8rem;
        margin-bottom: .3rem;
    }

    /* Checkbox select all */
    .sel-all { margin-bottom: 1rem; }

    /* Botón extraer */
    div[data-testid="stButton"] button {
        background: linear-gradient(135deg, #00b050, #00803a) !important;
        border: none !important;
        border-radius: 6px !important;
        width: 100% !important;
        box-shadow: 0 4px 20px rgba(0,255,133,0.35) !important;
        transition: all 0.2s ease !important;
        padding: 0.65rem 0.5rem !important;
    }
    div[data-testid="stButton"] button p {
        color: #fff !important;
        font-family: 'Bebas Neue', sans-serif !important;
        font-size: 18px !important;
        letter-spacing: 2px !important;
        margin: 0 !important;
    }
    div[data-testid="stButton"] button:hover {
        box-shadow: 0 6px 30px rgba(0,255,133,0.6) !important;
        transform: translateY(-2px) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    LOGO_URL = "https://upload.wikimedia.org/wikipedia/en/4/4b/2026_FIFA_World_Cup_logo.svg"

    st.markdown(f"""
    <div class="wc-hero">
        <img class="wc-logo" src="{LOGO_URL}" alt="FIFA World Cup 2026">
        <div>
            <div class="wc-title">MUNDIAL 2026</div>
            <div class="wc-subtitle">EXTRACTOR DE PRENSA GLOBAL</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── SIDEBAR ───────────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("## 📰 Fuentes del Mundial")

        selected = []
        fuentes_list = sources_dict["Mundial Global"]

        def toggle_block(block_id, start_idx, end_idx):
            val = st.session_state[f"wc_todo_block_{block_id}"]
            for i in range(start_idx, end_idx):
                st.session_state[f"wc_chk_{i}"] = val

        block_size = 10
        num_blocks = (len(fuentes_list) + block_size - 1) // block_size

        for b in range(num_blocks):
            start = b * block_size
            end = min(start + block_size, len(fuentes_list))
            
            # Nombre del bloque (A, B, C...)
            block_letter = chr(65 + b)
            st.markdown(f"**Bloque {block_letter} ({start+1} - {end})**")
            
            # Checkbox para seleccionar todo el bloque
            st.checkbox(f"🔳 Seleccionar todas", 
                        key=f"wc_todo_block_{b}", 
                        on_change=toggle_block, 
                        args=(b, start, end))
            
            for idx in range(start, end):
                f = fuentes_list[idx]
                if st.checkbox(f["nombre"], key=f"wc_chk_{idx}"):
                    selected.append(f)
            
            if b < num_blocks - 1:
                st.markdown("<hr style='margin: 0.5rem 0; border-color:#2a2a2a;'>", unsafe_allow_html=True)

        st.markdown("---")
        st.caption(f"**{len(selected)}** fuente(s) seleccionada(s)")


    # ── BARRA DE BOTONES ──────────────────────────────────────────────────────────
    col_info, col_volver, col_btn = st.columns([2.5, 1, 1])
    with col_info:
        st.markdown('<p style="color:#888; font-size:.9rem; margin-top:.5rem;">Selecciona las fuentes en el panel izquierdo y extrae las noticias globales del Mundial 2026.</p>', unsafe_allow_html=True)
    with col_volver:
        if st.button("⬅️ VOLVER", key="back_btn_top", use_container_width=True):
            st.session_state.current_page = "main"
            st.rerun()
    with col_btn:
        run = st.button("⚡ EXTRAER NOTICIAS", disabled=len(selected) == 0, use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── EXTRACCIÓN ────────────────────────────────────────────────────────────────
    if "wc_resultado" not in st.session_state:
        st.session_state.wc_resultado = None

    if run:
        st.session_state.wc_resultado = None
        all_noticias: list[dict] = []
        all_log: list[dict] = []

        total = len(selected)
        progress = st.progress(0, text="Iniciando extracción del Mundial…")
        status_box = st.empty()

        async def run_all():
            for i, f in enumerate(selected):
                status_box.info(f"🔍 **{f['nombre']}**")
                extractor = get_extractor(f["nombre"], f["url"], "Mundial Global")
                noticias, log = await extractor.extract()
                all_noticias.extend(noticias)
                all_log.append(log)
                progress.progress((i + 1) / total, text=f"{i+1}/{total} fuentes procesadas")

        asyncio.run(run_all())
        progress.empty()
        status_box.empty()

        txt_path = export_txt(all_noticias, all_log)
        html_path = export_html(all_noticias, all_log)

        st.session_state.wc_resultado = {
            "noticias": all_noticias,
            "log": all_log,
            "txt_path": txt_path,
            "html_path": html_path,
        }

    # ── RESULTADOS ────────────────────────────────────────────────────────────────
    if st.session_state.wc_resultado:
        res = st.session_state.wc_resultado
        noticias = res["noticias"]
        log = res["log"]
        txt_path: Path = res["txt_path"]
        html_path: Path = res["html_path"]

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("📰 Extraídas", len(noticias))
        k2.metric("✅ Exitosas", sum(1 for l in log if l["estado"] == "Correcto"))
        k3.metric("⚠️ Vacías", sum(1 for l in log if "sin noticias" in l["estado"].lower()))
        k4.metric("❌ Errores", sum(1 for l in log if l["estado"] == "Error"))

        st.markdown("<hr>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        if txt_path.exists():
            col1.download_button("📥 Descargar .txt", data=txt_path.read_bytes(),
                                 file_name="mundial_noticias.txt", mime="text/plain")
        if html_path.exists():
            col2.download_button("🌐 Descargar .html", data=html_path.read_bytes(),
                                 file_name="mundial_noticias.html", mime="text/html")

        st.markdown("<hr>", unsafe_allow_html=True)

        tab_news, tab_log = st.tabs([f"📰 Noticias ({len(noticias)})", "📋 Informe de control"])

        with tab_news:
            if not noticias:
                st.warning("No se encontraron noticias del día en las fuentes seleccionadas.")
            for n in noticias:
                st.markdown(f"#### [{n.get('title', 'Sin título')}]({n.get('url', '#')})")
                st.markdown(f"<div style='color:#00ff85; font-size:1.05rem;'>📌 Fuente: {n.get('fuente','')} | 📅 {n.get('date','')}</div>", unsafe_allow_html=True)
                resumen = n.get("body", "")[:400] + ('...' if len(n.get("body", "")) > 400 else '')
                st.markdown(f"<div style='color:#ddd;'>{resumen}</div>", unsafe_allow_html=True)
                st.markdown("---")

        with tab_log:
            for entry in log:
                estado = entry.get("estado", "")
                if estado == "Correcto":
                    icon = "✅"
                elif "sin" in estado.lower():
                    icon = "⚠️"
                else:
                    icon = "❌"
                err = f" — `{entry['error']}`" if entry.get("error") else ""
                st.markdown(f"{icon} **{entry['fuente']}** · Encontradas: `{entry['encontradas']}` · Extraídas: `{entry['extraidas']}` · {estado}{err}")
    else:
        st.markdown(f"""
        <div style="text-align:center; padding: 2rem 0; color: #555;">
            <img src="{LOGO_URL}" style="width:120px; filter: drop-shadow(0 0 15px rgba(0,255,133,0.5));">
            <h2 style="color:#00ff85; font-family:'Bebas Neue', sans-serif; letter-spacing:2px;">LISTO PARA EXTRAER</h2>
            <p>Marca las fuentes en el menú izquierdo y pulsa el botón verde.</p>
        </div>
        """, unsafe_allow_html=True)

