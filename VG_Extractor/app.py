import asyncio
import base64
import logging
import os
import subprocess
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import streamlit as st

# ── Instalar Playwright Chromium automáticamente (necesario en Streamlit Cloud) ──
@st.cache_resource(show_spinner=False)
def _install_playwright():
    try:
        subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=True, capture_output=True
        )
    except Exception:
        pass  # Si ya está instalado, no pasa nada

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

# ── PANEL DE PRENSA ───────────────────────────────────────────────────────────
def _render_panel_prensa():
    """Renderiza el panel de accesos directos de prensa integrado en la app."""
    panel_css = """
    <style>
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
    .pd-list { list-style:none; padding:8px 0; }
    .pd-list li { border-bottom:1px solid rgba(74,21,36,0.4); }
    .pd-list li:last-child { border-bottom:none; }
    .pd-link { display:flex; align-items:center; padding:10px 16px; color:#d0c2c6;
               text-decoration:none; font-size:13.5px; font-weight:500;
               transition: background .2s, color .2s, padding-left .2s; }
    .pd-link:hover { background:#35101d; color:#fff; padding-left:22px; }
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


# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;600&display=swap');

/* ─── BANNER (ocupa todo el ancho del área principal) ─── */
.vg-banner-wrap {
    margin: -1rem -1rem 0 -1rem;
    overflow: hidden;
    max-height: 260px;
    position: relative;
    background: #0d0d0d;
}
.vg-banner-wrap img {
    width: 100%;
    display: block;
    object-fit: cover;
    object-position: center center;
    max-height: 260px;
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
div[data-testid="stButton"] button {
    background: linear-gradient(135deg, #7a1a2e, #c0392b) !important;
    color: white !important; border: none !important;
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 1.2rem !important; letter-spacing: 3px !important;
    padding: .75rem 1.5rem !important; border-radius: 6px !important;
    width: 100% !important;
    box-shadow: 0 4px 15px rgba(192,57,43,0.4) !important;
    transition: all 0.2s ease !important;
}
div[data-testid="stButton"] button:hover {
    box-shadow: 0 6px 20px rgba(192,57,43,0.7) !important;
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

# ── BARRA DE TÍTULO + BOTÓN EXTRAER (en el área principal) ───────────────────
col_title, col_btn = st.columns([4, 1])

with col_title:
    st.markdown(f"""
    <div style="padding:.4rem 0 .2rem 0;">
        <div style="font-family:'Bebas Neue',sans-serif;font-size:2.2rem;
                    color:#fff;letter-spacing:3px;line-height:1;">
            NEWS EXTRACTOR
        </div>
        <div style="background:#7a1a2e;color:#fff;font-size:.72rem;
                    padding:.2rem .7rem;border-radius:20px;letter-spacing:1px;
                    margin-top:.4rem;display:inline-block;">
            HOY: {date.today().strftime('%d / %m / %Y')}
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_btn:
    # Pequeño espaciado para alinear verticalmente con el título
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    run = st.button("⚡ EXTRAER NOTICIAS", disabled=total_sel == 0, use_container_width=True)

st.markdown("<hr style='border-color:#2a2a2a;margin-top:.5rem;'>", unsafe_allow_html=True)

# ── EXTRACCIÓN ────────────────────────────────────────────────────────────────
if "resultado" not in st.session_state:
    st.session_state.resultado = None

if run:
    st.session_state.resultado = None
    all_noticias: list[dict] = []
    all_log: list[dict] = []

    progress = st.progress(0, text="Iniciando extracción…")
    status_box = st.empty()

    flat_sources = [(cat, f) for cat, fuentes in selected.items() for f in fuentes]
    total = len(flat_sources)

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
        else:
            cats_disp = sorted({n["categoria"] for n in noticias})
            cat_filter = st.multiselect("Filtrar por categoría", cats_disp, default=cats_disp)
            for n in [x for x in noticias if x["categoria"] in cat_filter]:
                body_preview = n.get("body", "")[:400]
                if len(n.get("body", "")) > 400:
                    body_preview += "…"

                subtitle_html = f"<div class='nc-subtitle'>{n['subtitle']}</div>" if n.get('subtitle') else ""
                author_html = f"<div class='nc-byline'>✍ {n['author']}</div>" if n.get('author') else ""

                html_str = (
                    f"<div class='news-card'>"
                    f"<div class='nc-meta'>"
                    f"<span class='nc-cat'>{n.get('categoria','')}</span>"
                    f"<span>{n.get('fuente','')}</span>"
                    f"<span>{n.get('date','')}</span>"
                    f"<a href='{n.get('url','')}' target='_blank' style='color:#e74c3c'>🔗 Ver original</a>"
                    f"</div>"
                    f"<h3>{n.get('title','')}</h3>"
                    f"{subtitle_html}{author_html}"
                    f"<div class='nc-body'>{body_preview}</div>"
                    f"</div>"
                )
                st.markdown(html_str, unsafe_allow_html=True)

    with tab_log:
        for entry in log:
            icon = "✅" if entry["estado"] == "Correcto" else ("⚠️" if "sin" in entry["estado"].lower() else "❌")
            err = f" — `{entry['error']}`" if entry.get("error") else ""
            st.markdown(f"{icon} **{entry['fuente']}** · Encontradas: `{entry['encontradas']}` · Extraídas: `{entry['extraidas']}` · {entry['estado']}{err}")

    with tab_prensa:
        _render_panel_prensa()

else:
    # Estado vacío — Logo + Panel de Prensa directamente visible
    logo_center = f'<img src="{logo_src}" style="width:100px;border-radius:12px;box-shadow:0 6px 20px rgba(0,0,0,0.6);">' if logo_src else '<div style="font-size:4rem;">⚽</div>'
    st.markdown(f"""
    <div style="text-align:center; padding: 2rem 0 1rem 0; color: #555;">
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

    st.markdown("---")
    st.markdown("### 🗞️ Panel de Prensa — Accesos directos")
    _render_panel_prensa()