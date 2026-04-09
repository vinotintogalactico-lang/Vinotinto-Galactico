# Documento de Requisitos

## Introducción

El sistema "Vinotinto Galáctico Scraper" es una herramienta de extracción y presentación de noticias deportivas. Lee una lista de fuentes web organizadas por bloques temáticos desde un archivo Excel (`Prensa Deportiva.xlsx`), extrae las noticias del día actual de cada fuente, y genera dos archivos de salida: un `.txt` estructurado como prompt para el personaje periodístico JULL, y un `.html` con estilo de web deportiva para revisión visual.

El sistema ya cuenta con un archivo base (`VG_Extractor.py`) que implementa la lógica inicial. Estos requisitos formalizan y amplían ese comportamiento para garantizar fidelidad, calidad y robustez.

---

## Glosario

- **Extractor**: El sistema principal (`VG_Extractor.py`) responsable de leer fuentes, extraer noticias y generar los archivos de salida.
- **Bloque**: Categoría temática de noticias (ej. REAL MADRID, VINOTINTO, LALIGA). Cada bloque agrupa un conjunto de URLs fuente.
- **Fuente**: URL de una sección o portada de un medio deportivo verificado por el usuario.
- **Noticia**: Artículo periodístico con título, subtítulos, fecha, contenido completo, autor, fuente y link.
- **Excel_Fuentes**: Archivo `Prensa Deportiva.xlsx` que contiene los bloques y sus URLs en el orden definido por el usuario.
- **Prompt_JULL**: Archivo de texto (`PROMPT_PARA_JULL.txt`) que contiene las noticias estructuradas como insumo para el personaje periodístico JULL.
- **Revision_HTML**: Archivo visual (`REVISION_VISUAL.html`) con las noticias organizadas por bloque, con estilo de web deportiva.
- **JULL**: Personaje periodístico con voz de periodista deportiva venezolana, cercana y fluida, que consume el Prompt_JULL para generar un noticiero largo y 4 Shorts.
- **Fecha_Actual**: La fecha del día en que se ejecuta el Extractor, en formato `DD/MM/YYYY`.

---

## Requisitos

### Requisito 1: Lectura del archivo de fuentes

**User Story:** Como operador del sistema, quiero que el Extractor lea el archivo Excel con los bloques y fuentes verificadas, para que la extracción respete el orden y la estructura definidos por el usuario.

#### Criterios de Aceptación

1. WHEN el Extractor se ejecuta, THE Extractor SHALL leer el archivo `Prensa Deportiva.xlsx` desde el directorio de trabajo actual.
2. IF el archivo `Prensa Deportiva.xlsx` no existe en el directorio de trabajo, THEN THE Extractor SHALL mostrar un mensaje de error descriptivo y detener la ejecución sin generar archivos de salida.
3. THE Extractor SHALL preservar el orden de los bloques exactamente como aparecen en el Excel_Fuentes, sin reordenarlos ni renombrarlos.
4. THE Extractor SHALL preservar el orden de las URLs dentro de cada bloque exactamente como aparecen en el Excel_Fuentes.
5. IF una fila del Excel_Fuentes está vacía o contiene el valor `nan`, THEN THE Extractor SHALL ignorar esa fila y continuar con la siguiente.

---

### Requisito 2: Extracción de noticias por bloque

**User Story:** Como operador del sistema, quiero que el Extractor obtenga las noticias más recientes de cada fuente verificada, para que el contenido generado sea actual y relevante.

#### Criterios de Aceptación

1. WHEN el Extractor procesa una URL de portada, THE Extractor SHALL buscar los enlaces a artículos individuales dentro de esa página.
2. THE Extractor SHALL extraer un máximo de 5 noticias por bloque, contando el total acumulado de todas las fuentes del bloque.
3. WHEN se alcanza el límite de 5 noticias en un bloque, THE Extractor SHALL dejar de procesar fuentes adicionales de ese bloque.
4. THE Extractor SHALL aplicar un filtro temporal para incluir únicamente noticias publicadas en la Fecha_Actual.
5. IF una noticia no contiene una fecha verificable o su fecha no corresponde a la Fecha_Actual, THEN THE Extractor SHALL descartar esa noticia.
6. WHILE se procesan fuentes de un bloque, THE Extractor SHALL esperar al menos 1 segundo entre cada solicitud HTTP para respetar los servidores de origen.
7. IF una solicitud HTTP a una fuente falla o supera el tiempo de espera de 10 segundos, THEN THE Extractor SHALL registrar el error en consola y continuar con la siguiente fuente del bloque.

---

### Requisito 3: Extracción de datos completos por noticia

**User Story:** Como operador del sistema, quiero que cada noticia extraída contenga todos sus campos requeridos, para que el Prompt_JULL tenga información suficiente para generar el noticiero.

#### Criterios de Aceptación

1. WHEN el Extractor extrae una noticia, THE Extractor SHALL obtener los siguientes campos: título, subtítulos, fecha de publicación, contenido completo e íntegro, autor, nombre de la fuente (medio) y URL del artículo.
2. IF el campo autor no está disponible en el artículo, THEN THE Extractor SHALL asignar el valor `"No disponible"` a ese campo.
3. IF el campo subtítulos no está disponible en el artículo, THEN THE Extractor SHALL omitir ese campo en la salida sin generar error.
4. THE Extractor SHALL extraer el contenido completo del artículo sin truncarlo en el Prompt_JULL.
5. IF el contenido extraído de una noticia tiene menos de 200 caracteres, THEN THE Extractor SHALL descartar esa noticia por considerarse incompleta.

---

### Requisito 4: Generación del archivo Prompt_JULL

**User Story:** Como operador del sistema, quiero que el Extractor genere un archivo `.txt` estructurado con las noticias del día, para que JULL pueda usarlo como insumo para producir el noticiero.

#### Criterios de Aceptación

1. WHEN el Extractor completa la extracción, THE Extractor SHALL generar el archivo `PROMPT_PARA_JULL.txt` en el directorio de trabajo actual.
2. THE Extractor SHALL organizar el contenido del Prompt_JULL en el mismo orden de bloques que aparece en el Excel_Fuentes.
3. THE Extractor SHALL incluir en el encabezado del Prompt_JULL la Fecha_Actual en formato `DD/MM/YYYY`.
4. THE Extractor SHALL incluir para cada noticia: número de noticia dentro del bloque, título, subtítulos (si existen), fecha, contenido completo, autor, fuente y link.
5. IF un bloque no contiene noticias del día actual, THEN THE Extractor SHALL omitir ese bloque del Prompt_JULL sin generar error.
6. THE Prompt_JULL SHALL incluir al final una sección de instrucciones para JULL que especifique: voz de periodista deportiva venezolana cercana y fluida, estructura de noticiero largo en el orden de bloques definido, y generación de 4 Shorts adicionales.
7. THE Prompt_JULL SHALL indicar explícitamente que JULL no debe usar cierres temporales como "mañana" o "hoy".

---

### Requisito 5: Generación del archivo Revision_HTML

**User Story:** Como operador del sistema, quiero que el Extractor genere un archivo `.html` con estilo de web deportiva, para poder revisar visualmente las noticias extraídas antes de usarlas.

#### Criterios de Aceptación

1. WHEN el Extractor completa la extracción, THE Extractor SHALL generar el archivo `REVISION_VISUAL.html` en el directorio de trabajo actual.
2. THE Extractor SHALL organizar el contenido del Revision_HTML en el mismo orden de bloques que aparece en el Excel_Fuentes.
3. THE Revision_HTML SHALL mostrar el texto de las noticias con alineación justificada.
4. THE Revision_HTML SHALL aplicar un estilo visual de web deportiva con los colores corporativos del proyecto (vino tinto `#800020` como color principal).
5. THE Revision_HTML SHALL mostrar para cada noticia: título, subtítulos (si existen), fecha, contenido completo, autor, fuente y un enlace al artículo original.
6. IF un bloque no contiene noticias del día actual, THEN THE Extractor SHALL omitir ese bloque del Revision_HTML sin generar error.
7. THE Revision_HTML SHALL incluir la Fecha_Actual en el encabezado de la página.
8. THE Revision_HTML SHALL ser un archivo HTML válido con codificación UTF-8 para soportar caracteres en español.

---

### Requisito 6: Fidelidad a los bloques y fuentes verificadas

**User Story:** Como operador del sistema, quiero que el Extractor use únicamente las fuentes definidas en el Excel_Fuentes, para garantizar que el contenido proviene de medios verificados.

#### Criterios de Aceptación

1. THE Extractor SHALL procesar únicamente las URLs que estén registradas en el Excel_Fuentes.
2. THE Extractor SHALL respetar los siguientes bloques en el orden indicado: REAL MADRID, REAL MADRID FEMENINO, LALIGA, SELECCIÓN ESPAÑOLA, SELECCIÓN ESPAÑOLA FEMENINO, VENEZUELA, LIGA FUTVE, VINOTINTO, VENEZUELA FEMENINO.
3. IF el Extractor encuentra una URL en el Excel_Fuentes que no responde o devuelve un error HTTP, THEN THE Extractor SHALL registrar el fallo en consola con la URL afectada y continuar con la siguiente fuente.
4. THE Extractor SHALL mantener el nombre de cada bloque exactamente como aparece en el Excel_Fuentes, sin modificaciones de formato ni capitalización.

---

### Requisito 7: Registro de ejecución en consola

**User Story:** Como operador del sistema, quiero ver el progreso de la extracción en consola, para poder monitorear el proceso y detectar errores rápidamente.

#### Criterios de Aceptación

1. WHEN el Extractor inicia, THE Extractor SHALL mostrar un mensaje de inicio en consola.
2. WHEN el Extractor comienza a procesar un bloque, THE Extractor SHALL mostrar el nombre del bloque en consola.
3. WHEN el Extractor analiza una URL fuente, THE Extractor SHALL mostrar los primeros 50 caracteres de la URL en consola.
4. WHEN el Extractor extrae una noticia exitosamente, THE Extractor SHALL mostrar los primeros 50 caracteres del título en consola.
5. WHEN el Extractor completa la generación de los archivos de salida, THE Extractor SHALL mostrar los nombres de los archivos generados en consola.
6. IF ocurre cualquier error durante la extracción de una fuente, THEN THE Extractor SHALL mostrar un mensaje de error descriptivo en consola sin interrumpir el proceso general.
