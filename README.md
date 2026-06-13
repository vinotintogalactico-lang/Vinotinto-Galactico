# ⚽ VINOTINTO GALÁCTICO — NEWS EXTRACTOR

Extractor de noticias deportivas para producción de contenido en YouTube.

---

## Requisitos previos

- Python 3.11 o superior
- pip

---

## Instalación

```bash
# 1. Entra en la carpeta del proyecto
cd VG_Extractor

# 2. (Recomendado) Crea un entorno virtual
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows

# 3. Instala las dependencias Python
pip install -r requirements.txt

# 4. Instala los navegadores de Playwright (solo la primera vez)
playwright install chromium
```

---

## Configuración del Excel

Coloca tu archivo en:

```
VG_Extractor/data/Prensa Deportiva.xlsx
```

El Excel solo tiene una sola columna separado por secciones y cada seccion tiene las urls de donde extraer las noticias

Las categorías reconocidas son:

- Real Madrid Masculino
- Real Madrid Femenino
- LaLiga
- Selección Española Masculina
- Selección Española Femenina
- Vinotinto Masculina
- Vinotinto Femenina
- Liga FUTVE

Puedes añadir categorías propias; aparecerán al final de la lista.

---

## Ejecución

```bash
streamlit run app.py
```

Abre tu navegador en: **http://localhost:8501**

---

## Flujo de uso

1. En el panel lateral, marca las fuentes que quieras procesar.
2. Pulsa **⚡ EXTRAER NOTICIAS**.
3. El sistema abre cada URL, detecta hasta 3 noticias del día de hoy y extrae el contenido limpio.
4. Al terminar puedes descargar:
   - `noticias.txt` → archivo listo para alimentar el prompt de guiones
   - `noticias.html` → auditoría visual

---

## Estructura del proyecto

```
VG_Extractor/
├── app.py                    ← Interfaz Streamlit
├── requirements.txt
├── data/
│   └── Prensa Deportiva.xlsx ← Tu Excel (¡no incluido en el repo!)
├── core/
│   ├── excel_reader.py       ← Lee y valida el Excel
│   ├── article_parser.py     ← Extrae y limpia el contenido
│   ├── date_validator.py     ← Valida fechas (solo noticias de hoy)
│   ├── txt_exporter.py       ← Genera noticias.txt
│   └── html_exporter.py      ← Genera noticias.html
├── extractores/
│   ├── generic.py            ← Extractor base (Playwright)
│   ├── factory.py            ← Selecciona el extractor según el dominio
│   ├── realmadrid.py
│   ├── as_.py
│   ├── marca.py
│   ├── mundodeportivo.py
│   └── meridiano.py
├── output/
│   ├── noticias.txt          ← Se genera al extraer
│   └── noticias.html         ← Se genera al extraer
└── logs/
```

---

## Reglas del sistema

- **El Excel es la única fuente de verdad.** No se exploran dominios ni se descubren URLs nuevas.
- Solo se extraen **noticias del día actual**.
- **Máximo 3 noticias por fuente.**
- Los duplicados entre fuentes distintas se conservan (la consolidación la hace el prompt de guiones).
- El contenido extraído elimina publicidad, redes sociales, noticias relacionadas, newsletters, comentarios y widgets externos.

---

## Agregar soporte específico para un nuevo dominio

1. Crea `extractores/mi_fuente.py` heredando de `GenericExtractor`.
2. Sobrescribe `_get_article_links()` con los selectores CSS del sitio.
3. Añade la entrada en `extractores/factory.py` → `_DOMAIN_MAP`.
