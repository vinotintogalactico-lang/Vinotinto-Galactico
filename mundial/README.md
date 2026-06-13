# 🌍 Mundial 2026 — News Extractor

Extractor de noticias del Mundial 2026 para el canal **Vinotinto Galáctico**.  
Basado en la misma arquitectura de `Vinotinto-Galactico` pero especializado en prensa del Mundial.

---

## Estructura del proyecto

```
mundial/
├── app_mundial.py              ← Streamlit principal (ejecutar esto)
├── requirements.txt
├── crear_excel_mundial.py      ← Solo si necesitas regenerar el Excel
├── data/
│   └── Prensa_Mundial2026.xlsx ← 41 fuentes en 3 categorías
├── output/
│   ├── mundial_noticias.txt    ← Se genera al extraer
│   └── mundial_noticias.html   ← Se genera al extraer
├── core/
│   ├── article_parser.py       ← Igual que VG
│   ├── content_filter.py       ← Filtro adaptado al Mundial
│   ├── date_validator.py       ← Igual que VG
│   ├── excel_reader.py         ← Lee Prensa_Mundial2026.xlsx
│   ├── html_exporter.py        ← Tema verde/dorado Mundial
│   └── txt_exporter.py         ← Para el prompt del avatar
└── extractores/
    ├── factory.py              ← Mapea dominios a extractores
    ├── generic.py              ← Base (igual que VG)
    ├── as_.py                  ← AS.com (igual que VG)
    ├── marca.py                ← Marca.com (igual que VG)
    ├── mundodeportivo.py       ← Mundo Deportivo (igual que VG)
    ├── meridiano.py            ← Meridiano (igual que VG)
    ├── sport.py                ← Sport.es (igual que VG)
    ├── ole.py                  ← Ole.com.ar ← NUEVO
    ├── tycsports.py            ← TyC Sports ← NUEVO
    ├── espndeportes.py         ← ESPN Deportes ← NUEVO
    ├── infobae.py              ← Infobae ← NUEVO
    ├── depor.py                ← Depor.com ← NUEVO
    └── relevo.py               ← Relevo.com ← NUEVO
```

---

## Categorías (41 fuentes)

| Categoría | Fuentes | Países |
|-----------|---------|--------|
| 📺 TV / Canal | 16 | Telemundo, TUDN, Azteca, Televen, Caracol, RCN, TyC, Telefe, DirecTV, Canal del Fútbol, Chilevision, Canal 13, Latina, RTVE, Fox Sports MX, Claro Sports |
| 📰 Prensa Escrita | 17 | Meridiano, Record, Olé, El Gráfico, RedGol, Depor, Libero, El País UY, Diez, Marca, AS, Mundo Deportivo, Sport, Relevo, El Tiempo CO, La Tercera, El Universal MX |
| 💻 Digital | 8 | Líder en Deportes, Win Sports, Futbol Red, Mediotiempo, Al Aire Libre, Studio Fútbol, ESPN Deportes, Infobae |

---

## Cómo correr

```bash
# 1. Instalar dependencias
pip install -r requirements.txt
playwright install chromium

# 2. Ejecutar
streamlit run app_mundial.py
```

---

## Fusión con Vinotinto Galáctico (Fase 2)

Para unir ambos extractores en un solo frontend, se crea un `app_home.py` con:
- Botón ⚽ **VINOTINTO GALÁCTICO** → carga `app.py`
- Botón 🌍 **MUNDIAL 2026** → carga `app_mundial.py`

Ambos comparten `core/` y `extractores/` para no duplicar código.
