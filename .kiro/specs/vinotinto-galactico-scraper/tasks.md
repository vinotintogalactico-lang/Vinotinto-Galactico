# Plan de Implementación: Vinotinto Galáctico Scraper

## Visión General

Refactorizar `VG_Extractor.py` adoptando la arquitectura de adaptadores definida en el diseño técnico. El código existente ya tiene la lectura del Excel, `requests` + `BeautifulSoup` y la generación de salidas; las tareas se enfocan en introducir los modelos de datos, los adaptadores, el filtro temporal, la extracción completa de campos y los tests.

## Tareas

- [x] 1. Definir modelos de datos y jerarquía de excepciones en `VG_Extractor.py`
  - Crear el dataclass `Block` con campos `name: str` y `urls: list[str]`
  - Crear el dataclass `NewsItem` con campos `titulo`, `subtitulos`, `fecha`, `contenido`, `autor`, `fuente`, `link`
  - Definir la jerarquía de excepciones: `VGScraperError`, `ExcelReadError`, `AdapterError`, `ExtractionError`, `DateParseError`
  - _Requisitos: 1.2, 3.1, 3.2_

- [x] 2. Refactorizar la lectura del Excel con `ExcelReader`
  - [x] 2.1 Implementar la clase `ExcelReader` que reemplaza la lógica de `procesar_excel()`
    - Leer `Prensa Deportiva.xlsx` y retornar `list[Block]` preservando el orden exacto
    - Ignorar filas vacías o `nan`
    - Lanzar `ExcelReadError` si el archivo no existe
    - _Requisitos: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [x] 2.2 Escribir test unitario para `ExcelReader`
    - `test_excel_reader_file_not_found`: verifica que se lanza `ExcelReadError`
    - `test_excel_reader_preserves_order`: verifica orden con un Excel de ejemplo en `tests/fixtures/`
    - _Requisitos: 1.2, 1.3_

  - [x] 2.3 Escribir test de propiedad para `ExcelReader`
    - **Propiedad 1: Preservación de orden de bloques y URLs**
    - **Propiedad 2: Filas vacías no afectan el resultado**
    - **Valida: Requisitos 1.3, 1.4, 1.5**

- [x] 3. Implementar la arquitectura de adaptadores
  - [x] 3.1 Implementar `BaseAdapter` (clase abstracta), `StaticAdapter` y `AdapterFactory`
    - `StaticAdapter.fetch_page()` usa `requests` con timeout 10 s y el `User-Agent` existente
    - `AdapterFactory.get_adapter()` retorna `StaticAdapter` por defecto
    - Lanzar `AdapterError` ante timeout o error HTTP
    - _Requisitos: 2.6, 2.7, 6.3_

  - [x] 3.2 Implementar `PlaywrightAdapter`
    - Usar `sync_playwright`, `wait_until="networkidle"`, timeout 30 s
    - Capturar `ImportError` y lanzar `AdapterError` con mensaje de instalación
    - Registrar `realmadrid.com` y `laliga.com` en `JS_DOMAINS` dentro de `AdapterFactory`
    - _Requisitos: 2.7_

  - [x] 3.3 Escribir tests unitarios para adaptadores
    - `test_static_adapter_timeout`: verifica que timeout lanza `AdapterError`
    - `test_playwright_adapter_not_installed`: verifica mensaje de error sin Playwright
    - _Requisitos: 2.7_

- [x] 4. Refactorizar `PortadaParser`
  - [x] 4.1 Implementar la clase `PortadaParser` que reemplaza `buscar_noticias_en_portada()`
    - Ampliar `ARTICLE_PATTERNS` con `/noticia-`, `/news/`, `/futbol/`
    - Agregar `EXCLUDE_PATTERNS` para filtrar redes sociales, `#`, `mailto:`, `/tag/`, `/autor/`
    - Retornar hasta 3 URLs de artículos resolviendo URLs relativas con `urljoin`
    - _Requisitos: 2.1_

  - [x] 4.2 Escribir test unitario para `PortadaParser`
    - Usar `tests/fixtures/sample_portada.html` con enlaces mixtos (válidos, excluidos, relativos)
    - Verificar que retorna solo URLs de artículos y resuelve las relativas
    - _Requisitos: 2.1_

- [x] 5. Implementar `ArticleExtractor` con extracción completa de campos
  - [x] 5.1 Implementar la clase `ArticleExtractor` que reemplaza `extraer_articulo_real()`
    - Título: `<h1>` → `og:title` → `<title>`
    - Subtítulos: `<h2>` dentro del artículo → `<h3>` → lista vacía
    - Fecha: `<time datetime="">` → `article:published_time` → regex en texto
    - Autor: `[rel="author"]` → `.author` / `.byline` → `article:author` → `"No disponible"`
    - Contenido: `<article>` → `.article-body` → todos los `<p>` > 70 chars; **sin truncar**
    - Retornar `None` si contenido < 200 caracteres
    - _Requisitos: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 5.2 Escribir tests unitarios para `ArticleExtractor`
    - `test_article_extractor_no_author`: autor es `"No disponible"` cuando no está en el HTML
    - `test_article_extractor_no_subtitles`: subtítulos es lista vacía cuando no hay `<h2>`
    - Usar `tests/fixtures/sample_article.html`
    - _Requisitos: 3.2, 3.3_

  - [x] 5.3 Escribir tests de propiedad para `ArticleExtractor`
    - **Propiedad 6: Campos completos en NewsItem**
    - **Propiedad 7: Contenido sin truncar**
    - **Propiedad 8: Descarte de noticias con contenido insuficiente**
    - **Valida: Requisitos 3.1, 3.2, 3.4, 3.5**

- [x] 6. Implementar `DateFilter`
  - [x] 6.1 Implementar la clase `DateFilter` con el método `is_today()`
    - Soportar formatos: `DD/MM/YYYY`, `YYYY-MM-DD`, `DD-MM-YYYY`, ISO 8601
    - Aceptar texto relativo: `"hace X horas"`, `"hace X minutos"`, `"hoy"`, `"today"`
    - Soportar texto en español: `"15 de enero de 2025"`
    - Retornar `False` si no puede determinar la fecha (lanzar `DateParseError` internamente)
    - _Requisitos: 2.4, 2.5_

  - [x] 6.2 Escribir tests unitarios para `DateFilter`
    - `test_date_filter_relative_today`: `"hace 2 horas"` se acepta como hoy
    - `test_date_filter_yesterday`: fecha de ayer se rechaza
    - _Requisitos: 2.4, 2.5_

  - [x] 6.3 Escribir test de propiedad para `DateFilter`
    - **Propiedad 4: Filtro temporal estricto**
    - **Valida: Requisitos 2.4, 2.5**

- [x] 7. Implementar `Orchestrator`
  - [x] 7.1 Implementar la clase `Orchestrator` que reemplaza el bucle principal de `procesar_excel()`
    - `process_block()`: respeta límite de 5 noticias, espera 1 s entre requests, captura `AdapterError` por URL sin interrumpir el bloque
    - `run()`: procesa todos los bloques preservando el orden, retorna `dict[str, list[NewsItem]]`
    - Registrar en consola: inicio, nombre de bloque, URL analizada (50 chars), título extraído (50 chars), errores
    - _Requisitos: 2.2, 2.3, 2.6, 2.7, 6.1, 6.3, 7.1, 7.2, 7.3, 7.4, 7.6_

  - [x] 7.2 Escribir tests de propiedad para `Orchestrator`
    - **Propiedad 1: Preservación de orden de bloques y URLs**
    - **Propiedad 3: Límite de noticias por bloque**
    - **Propiedad 5: Continuidad ante errores HTTP**
    - **Valida: Requisitos 2.2, 2.3, 2.7, 6.3**

- [x] 8. Punto de control — Verificar que todos los tests pasan
  - Asegurarse de que todos los tests pasan, consultar al usuario si surgen dudas.

- [x] 9. Refactorizar `TxtWriter`
  - [x] 9.1 Implementar la clase `TxtWriter` que reemplaza `guardar_resultados()` (parte TXT)
    - Incluir encabezado con `FECHA: DD/MM/YYYY`
    - Para cada noticia: número, título, subtítulos (si existen), fecha, contenido completo, autor, fuente, link
    - Omitir bloques sin noticias
    - Incluir al final la sección de instrucciones para JULL: voz de periodista deportiva venezolana, estructura de noticiero largo en el orden de bloques, 4 Shorts adicionales, prohibición de cierres temporales como "mañana" o "hoy"
    - _Requisitos: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_

  - [x] 9.2 Escribir tests unitarios para `TxtWriter`
    - `test_txt_writer_includes_jull_instructions`: verifica que el TXT incluye la sección de instrucciones
    - `test_txt_writer_no_temporal_closings`: verifica que las instrucciones prohíben cierres temporales
    - _Requisitos: 4.6, 4.7_

  - [x] 9.3 Escribir tests de propiedad para `TxtWriter`
    - **Propiedad 9: Campos completos en Prompt_JULL**
    - **Propiedad 10: Omisión de bloques vacíos en salida**
    - **Propiedad 12: Nombres de bloques preservados exactamente**
    - **Valida: Requisitos 4.2, 4.4, 4.5, 6.4**

- [x] 10. Refactorizar `HtmlWriter`
  - [x] 10.1 Implementar la clase `HtmlWriter` que reemplaza `guardar_resultados()` (parte HTML)
    - Incluir `charset=utf-8` y la `Fecha_Actual` en el encabezado
    - Mostrar para cada noticia: título, subtítulos, fecha, contenido completo, autor, fuente y enlace al original
    - Aplicar `text-align: justify` al texto de las noticias
    - Usar color corporativo `#800020` como color principal
    - Omitir bloques sin noticias
    - _Requisitos: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8_

  - [x] 10.2 Escribir tests unitarios para `HtmlWriter`
    - `test_html_writer_utf8`: verifica `charset=utf-8` en el HTML generado
    - `test_html_writer_color_corporativo`: verifica que el HTML contiene `#800020`
    - `test_html_writer_text_justify`: verifica que el CSS incluye `text-align: justify`
    - _Requisitos: 5.3, 5.4, 5.8_

  - [x] 10.3 Escribir tests de propiedad para `HtmlWriter`
    - **Propiedad 10: Omisión de bloques vacíos en salida**
    - **Propiedad 11: Campos completos en HTML**
    - **Propiedad 12: Nombres de bloques preservados exactamente**
    - **Valida: Requisitos 5.2, 5.5, 5.6, 6.4**

- [ ] 11. Crear fixtures de test y configurar el entorno de testing
  - [-] 11.1 Crear los archivos de fixtures en `tests/fixtures/`
    - `sample_portada.html`: página de portada con enlaces mixtos (válidos, excluidos, relativos)
    - `sample_article.html`: artículo completo con todos los campos y uno sin autor ni subtítulos
    - `sample_excel.xlsx`: Excel mínimo con 2 bloques y 2 URLs cada uno, incluyendo filas vacías
  - [ ] 11.2 Crear `tests/conftest.py` con fixtures de `pytest` reutilizables (instancias de clases, mocks de HTTP)
  - [ ] 11.3 Crear `tests/property/strategies.py` con las estrategias de `hypothesis` definidas en el diseño
    - `block_strategy()`, `news_item_strategy_with_random_dates()`, `article_html_strategy()`, `results_strategy()`
    - _Requisitos: todas las propiedades_

- [ ] 12. Cablear todos los componentes en el punto de entrada `main()`
  - [ ] 12.1 Reemplazar el bloque `if __name__ == "__main__"` con una función `main()` que instancie y conecte todos los componentes
    - `ExcelReader` → `Orchestrator(AdapterFactory, PortadaParser, ArticleExtractor, DateFilter)` → `TxtWriter` + `HtmlWriter`
    - Mostrar mensajes de inicio y finalización en consola con los nombres de archivos generados
    - _Requisitos: 7.1, 7.5_

- [ ] 13. Punto de control final — Verificar que todos los tests pasan
  - Asegurarse de que todos los tests pasan, consultar al usuario si surgen dudas.

## Notas

- Las tareas marcadas con `*` son opcionales y pueden omitirse para un MVP más rápido
- Cada tarea referencia los requisitos específicos para trazabilidad
- Los tests de propiedad usan `hypothesis` con `@settings(max_examples=100)`
- Los tests de propiedad deben incluir el tag `# Feature: vinotinto-galactico-scraper, Property N: <texto>`
- El archivo `VG_Extractor.py` existente se refactoriza en su lugar; no se crea un archivo nuevo
