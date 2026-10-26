import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=120, bottom=120, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def set_table_borders(table, color="CBD5E1", sz="4", val="single"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(f'''
        <w:tblBorders {nsdecls("w")}>
            <w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
            <w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
            <w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
            <w:insideV w:val="none"/>
            <w:left w:val="none"/>
            <w:right w:val="none"/>
        </w:tblBorders>
    ''')
    tblPr.append(borders)

def add_callout_box(doc, title, content_paragraphs, border_color="6366F1", bg_color="F8FAFC"):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    
    cell = table.cell(0, 0)
    cell.width = Inches(6.8)
    set_cell_background(cell, bg_color)
    set_cell_margins(cell, top=140, bottom=140, left=180, right=180)
    
    # Border: thick left border or full box
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(f'''
        <w:tcBorders {nsdecls("w")}>
            <w:top w:val="single" w:sz="4" w:space="0" w:color="{border_color}"/>
            <w:bottom w:val="single" w:sz="4" w:space="0" w:color="{border_color}"/>
            <w:left w:val="single" w:sz="24" w:space="0" w:color="{border_color}"/>
            <w:right w:val="single" w:sz="4" w:space="0" w:color="{border_color}"/>
        </w:tcBorders>
    ''')
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(4)
    run_title = p.add_run(title)
    run_title.bold = True
    run_title.font.name = "Arial"
    run_title.font.size = Pt(11)
    run_title.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A) if border_color == "2563EB" else RGBColor(0x43, 0x38, 0xCA)
    
    for text, is_bold_prefix, prefix in content_paragraphs:
        p2 = cell.add_paragraph()
        p2.paragraph_format.space_before = Pt(2)
        p2.paragraph_format.space_after = Pt(3)
        p2.paragraph_format.line_spacing = 1.15
        if is_bold_prefix and prefix:
            r_pre = p2.add_run(prefix)
            r_pre.bold = True
            r_pre.font.name = "Arial"
            r_pre.font.size = Pt(9.5)
            r_pre.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
        r_txt = p2.add_run(text)
        r_txt.font.name = "Arial"
        r_txt.font.size = Pt(9.5)
        r_txt.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)
    
    # Space after table
    p_spacer = doc.add_paragraph()
    p_spacer.paragraph_format.space_before = Pt(0)
    p_spacer.paragraph_format.space_after = Pt(4)

def build_docx(filename="documento_ingenieria_integrieval.docx"):
    doc = Document()
    
    # Set page margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.85)
        section.bottom_margin = Inches(0.85)
        section.left_margin = Inches(0.85)
        section.right_margin = Inches(0.85)
        
        # Header & Footer
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("IntegriEval — Especificación Formal de Ingeniería de Software | Versión 2.1.0")
        hrun.font.name = "Arial"
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)
        
        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        frun = fp.add_run("IntegriEval System — Confidencial / Uso Académico")
        frun.font.name = "Arial"
        frun.font.size = Pt(8.5)
        frun.font.color.rgb = RGBColor(0x94, 0xA3, 0xB8)

    # Styles
    COLOR_PRIMARY = RGBColor(0x25, 0x63, 0xEB)    # Royal Blue
    COLOR_SECONDARY = RGBColor(0x43, 0x38, 0xCA)  # Indigo
    COLOR_DARK = RGBColor(0x0F, 0x17, 0x2A)       # Dark Slate
    COLOR_MUTED = RGBColor(0x47, 0x55, 0x69)      # Slate 600

    def add_heading_1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(16)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.bold = True
        run.font.name = "Arial"
        run.font.size = Pt(15)
        run.font.color.rgb = COLOR_PRIMARY
        return p

    def add_heading_2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.bold = True
        run.font.name = "Arial"
        run.font.size = Pt(12)
        run.font.color.rgb = COLOR_SECONDARY
        return p

    def add_heading_3(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(9)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.bold = True
        run.font.name = "Arial"
        run.font.size = Pt(10.5)
        run.font.color.rgb = COLOR_DARK
        return p

    def add_body(text, space_after=5):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.line_spacing = 1.15
        run = p.add_run(text)
        run.font.name = "Arial"
        run.font.size = Pt(10)
        run.font.color.rgb = COLOR_DARK
        return p

    def add_bullet(bold_prefix, text):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.15
        if bold_prefix:
            r1 = p.add_run(bold_prefix + " ")
            r1.bold = True
            r1.font.name = "Arial"
            r1.font.size = Pt(9.5)
            r1.font.color.rgb = COLOR_DARK
        r2 = p.add_run(text)
        r2.font.name = "Arial"
        r2.font.size = Pt(9.5)
        r2.font.color.rgb = COLOR_DARK
        return p

    # ─────────────────────────────────────────────────────────────
    # PORTADA
    # ─────────────────────────────────────────────────────────────
    p_pre = doc.add_paragraph()
    p_pre.paragraph_format.space_before = Pt(40)
    
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_t = p_title.add_run("IntegriEval")
    r_t.bold = True
    r_t.font.name = "Arial"
    r_t.font.size = Pt(28)
    r_t.font.color.rgb = COLOR_PRIMARY
    
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(24)
    r_s = p_sub.add_run("Sistema Semi-Automatizado de Evaluación de Integridad Académica, Detección de IA y Verificación Oral Flash")
    r_s.font.name = "Arial"
    r_s.font.size = Pt(13)
    r_s.font.color.rgb = COLOR_SECONDARY
    
    # Metadata Box
    tbl_meta = doc.add_table(rows=4, cols=1)
    tbl_meta.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_meta.autofit = False
    meta_rows = [
        "Documento de Especificación Formal de Ingeniería de Software",
        "Asignatura / Proyecto: Proyecto de Ingeniería de Software / Taller de Título",
        "Fecha: Agosto 2026   |   Versión: 2.1.0",
        "Entorno: Educación Superior / Cátedras Universitarias"
    ]
    for i, row_text in enumerate(meta_rows):
        cell = tbl_meta.cell(i, 0)
        cell.width = Inches(6.0)
        set_cell_background(cell, "EFF6FF" if i == 0 else "F8FAFC")
        set_cell_margins(cell, top=80, bottom=80, left=140, right=140)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(row_text)
        r.font.name = "Arial"
        r.font.size = Pt(10 if i == 0 else 9.5)
        r.bold = (i == 0)
        r.font.color.rgb = COLOR_PRIMARY if i == 0 else COLOR_MUTED
    
    set_table_borders(tbl_meta, color="93C5FD", sz="6", val="single")

    p_spacer = doc.add_paragraph()
    p_spacer.paragraph_format.space_before = Pt(120)
    
    # Author info table
    tbl_auth = doc.add_table(rows=1, cols=2)
    tbl_auth.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_auth.autofit = False
    
    cell_l = tbl_auth.cell(0, 0)
    cell_l.width = Inches(3.4)
    p_l = cell_l.paragraphs[0]
    r_l1 = p_l.add_run("Equipo de Desarrollo:\n")
    r_l1.bold = True
    r_l1.font.size = Pt(10.5)
    r_l2 = p_l.add_run("Sebastian Cisternas\nBenjamin Sobarzo\n")
    r_l2.font.size = Pt(10)
    r_l3 = p_l.add_run("Facultad de Ingeniería")
    r_l3.font.size = Pt(9)
    r_l3.font.color.rgb = COLOR_MUTED
    
    cell_r = tbl_auth.cell(0, 1)
    cell_r.width = Inches(3.4)
    p_r = cell_r.paragraphs[0]
    p_r.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r_r1 = p_r.add_run("Repositorio Oficial:\n")
    r_r1.bold = True
    r_r1.font.size = Pt(10.5)
    r_r2 = p_r.add_run("github.com/blosttt/IntegriEval\n\nAgosto, 2026")
    r_r2.font.size = Pt(10)
    r_r2.font.color.rgb = COLOR_MUTED
    
    doc.add_page_break()

    # ─────────────────────────────────────────────────────────────
    # SECCIÓN 1: DEFINICIÓN DEL PROBLEMA (10%)
    # ─────────────────────────────────────────────────────────────
    add_heading_1("1. Definición Clara del Problema (10%)")
    
    add_heading_2("1.1 Contexto y Antecedentes")
    add_body(
        "La proliferación y democratización de los Modelos de Lenguaje Grande (LLMs) como GPT-4, Claude y Gemini, entre otros, ha alterado irreversiblemente los mecanismos de evaluación en la educación superior. En la dinámica actual, los estudiantes cargan sus informes de laboratorio, ensayos y proyectos semestrales a través del LMS institucional (Canvas, Moodle, Blackboard)."
    )
    add_body(
        "Los equipos docentes deben enfrentarse a la revisión de cientos de páginas escritas en formato digital (PDF/Word), careciendo de instrumentos confiables y pedagógicamente justos para validar si el contenido refleja las competencias reales del estudiante o si fue generado íntegramente por un sistema de IA sin apropiación de conocimiento."
    )
    
    add_heading_2("1.2 Articulación del Problema")
    add_body("El problema central se descompone en tres dimensiones críticas:")
    add_bullet("1. Inviabilidad de los Detectores Estadísticos de 'Caja Negra':", "Las soluciones comerciales (ej. Turnitin AI, GPTZero) clasifican textos mediante métricas opacas de perplejidad y ráfaga léxica. Investigaciones recientes han comprobado que poseen una alta tasa de falsos positivos (castigando a estudiantes no nativos o redacciones formales rigurosas) y falsos negativos (eludibles con reescritura básica). Una sanción disciplinaria sustentada únicamente en un porcentaje estadístico carece de validez jurídica y ética.")
    add_bullet("2. Inviabilidad Logística de la Interrogación Universal:", "La defensa oral presencial es el método más certero para acreditar autoría; no obstante, interrogar oralmente al 100% de los estudiantes en cursos masivos (60 a 200 alumnos) resulta humanamente imposible para el cuerpo docente.")
    add_bullet("3. Sobrecarga Cognitiva y Temporal:", "Los docentes dedican hasta 25 horas semanales a la corrección mecánica de informes contrastándolos con la pauta y la bibliografía del curso.")

    add_heading_2("1.3 Percepción de las Partes Interesadas (Stakeholders)")
    
    # Stakeholder table
    stk_headers = ["Stakeholder", "Percepción y Dolores Identificados", "Expectativa y Validación de Relevancia"]
    stk_rows = [
        ["Docentes", "\"No sé si el alumno aprendió o si un LLM hizo el trabajo. No puedo interrogar a 100 alumnos ni acusar a nadie sin pruebas tangibles.\"", "Requieren una herramienta que entregue notas preliminares justificadas, pools de preguntas y gestione citas solo para casos sospechosos o aleatorios."],
        ["Ayudantes", "\"Revisar 80 PDFs idénticos es agotador y dilata la entrega de retroalimentación semanas enteras.\"", "Desean subida masiva en lote y extracción de resúmenes estructurados en Markdown."],
        ["Estudiantes", "\"Es frustrante que un detector te acuse injustamente. Si hay dudas, prefiero que me hagan preguntas sobre mi propio trabajo.\"", "Exigen un proceso transparente, sin fricción de cuentas adicionales y derecho a defensa oral."],
        ["Dirección de Carrera", "\"Debemos resguardar el prestigio institucional y evitar sanciones arbitrarias que deriven en litigios.\"", "Validan la necesidad de trazabilidad auditable y defensas orales fundamentadas en evidencia."]
    ]
    
    tbl_stk = doc.add_table(rows=len(stk_rows) + 1, cols=3)
    tbl_stk.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_stk.autofit = False
    col_widths_stk = [Inches(1.5), Inches(2.6), Inches(2.7)]
    
    for c_idx, head in enumerate(stk_headers):
        cell = tbl_stk.cell(0, c_idx)
        cell.width = col_widths_stk[c_idx]
        set_cell_background(cell, "1E3A8A")
        set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
        p = cell.paragraphs[0]
        r = p.add_run(head)
        r.bold = True
        r.font.name = "Arial"
        r.font.size = Pt(9)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        
    for r_idx, row in enumerate(stk_rows):
        for c_idx, val in enumerate(row):
            cell = tbl_stk.cell(r_idx + 1, c_idx)
            cell.width = col_widths_stk[c_idx]
            set_cell_background(cell, "F8FAFC" if r_idx % 2 == 1 else "FFFFFF")
            set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
            p = cell.paragraphs[0]
            p.paragraph_format.line_spacing = 1.1
            r = p.add_run(val)
            r.font.name = "Arial"
            r.font.size = Pt(8.5)
            if c_idx == 0:
                r.bold = True
            r.font.color.rgb = COLOR_DARK
            
    set_table_borders(tbl_stk, color="CBD5E1", sz="4", val="single")
    
    doc.add_page_break()

    # ─────────────────────────────────────────────────────────────
    # SECCIÓN 2: OBJETIVOS SMART Y MATRIZ (25%)
    # ─────────────────────────────────────────────────────────────
    add_heading_1("2. Objetivos Específicos y Matriz de Trazabilidad (25%)")
    
    add_heading_2("2.1 Objetivo General")
    add_callout_box(
        doc,
        "Objetivo General del Proyecto",
        [
            ("Desarrollar un MVP de plataforma web que asista al docente en la detección de uso de IA en informes académicos y en la verificación del aprendizaje real del estudiante, mediante un flujo que integra análisis automatizado del PDF, generación de preguntas flash personalizadas y soporte para validación oral focalizada, sin reemplazar el criterio docente como autoridad final en la evaluación.", False, "")
        ],
        border_color="2563EB",
        bg_color="EFF6FF"
    )
    
    add_heading_2("2.2 Objetivos Específicos (Criterios SMART)")
    
    # OE1
    add_callout_box(
        doc,
        "OE1: Módulo de Ingesta Masiva y Gestión de Nómina sin Cuentas",
        [
            ("Implementar un módulo de ingesta masiva de trabajos académicos en formato PDF y gestión de nóminas estudiantiles mediante archivo CSV, eliminando la necesidad de que los estudiantes creen cuentas o contraseñas en la plataforma.", True, "Enunciado: "),
            ("El sistema permite cargar una nómina de estudiantes vía CSV (nombre, correo) y subir múltiples PDFs asociados a cada estudiante para su análisis posterior.", True, "Específico (S): "),
            ("El sistema procesa correctamente archivos CSV con hasta 200 estudiantes y lotes de hasta 100 PDFs en una sola operación, con tasa de éxito >= 98% en la conversión a texto estructurado.", True, "Medible (M): "),
            ("Implementado con tecnologías open-source: FastAPI para el backend, SQLite para persistencia, y pymupdf4llm para extracción de texto desde PDFs.", True, "Alcanzable (A): "),
            ("Elimina la fricción de registro para los estudiantes (validado en testimonios como una barrera de adopción) y estructura el texto de los informes para su posterior procesamiento por el motor de análisis.", True, "Relevante (R): "),
            ("Completado al final del Sprint 1 (Fase de Ingesta).", True, "Temporizado (T): ")
        ],
        border_color="6366F1",
        bg_color="F8FAFC"
    )

    # OE2
    add_callout_box(
        doc,
        "OE2: Motor de Análisis Contextualizado y Detección de IA",
        [
            ("Desarrollar un motor de análisis asistido por IA generativa que evalúe los informes estudiantiles contrastándolos con la pauta de corrección y los materiales de la asignatura, generando una calificación preliminar fundamentada y un índice de probabilidad de uso de IA.", True, "Enunciado: "),
            ("El sistema procesa cada PDF, extrae su contenido en Markdown, y mediante un LLM (Claude 3.5 Sonnet) evalúa: (1) cumplimiento de pauta, (2) coherencia con materiales del curso, (3) probabilidad de generación por IA (0-100%).", True, "Específico (S): "),
            ("Tiempo de respuesta <= 15 segundos por informe en procesamiento asíncrono, entregando un desglose JSON con: nota preliminar (1-7), feedback cualitativo, y puntaje de detección de IA. Precisión objetivo >= 75% en pruebas controladas con textos conocidos (humanos vs. IA).", True, "Medible (M): "),
            ("Implementado mediante workers asíncronos en FastAPI con integración a la API de Anthropic, y un motor de contingencia (Mock Engine) que opera sin conexión a internet.", True, "Alcanzable (A): "),
            ("Aborda directamente la imposibilidad del docente de detectar uso de IA y entrega una evaluación cualitativa justificada, superando a los detectores de 'caja negra'.", True, "Relevante (R): "),
            ("Completado al final del Sprint 2 (Fase de Análisis).", True, "Temporizado (T): ")
        ],
        border_color="6366F1",
        bg_color="F8FAFC"
    )

    # OE3
    add_callout_box(
        doc,
        "OE3: Generación de Preguntas Flash y Despacho con Supervisión Docente",
        [
            ("Diseñar un sistema interactivo que permita al docente revisar, editar y aprobar un banco de preguntas personalizadas generadas automáticamente a partir del contenido del informe, y despachar las evaluaciones flash a los estudiantes mediante enlaces seguros de un solo uso vía correo electrónico.", True, "Enunciado: "),
            ("El sistema genera automáticamente 20 preguntas (opción múltiple y breve) basadas en conceptos clave extraídos del informe. El docente puede editar, eliminar, añadir preguntas propias, y seleccionar 10 para el test final. El despacho se realiza por correo electrónico con token UUIDv4 de un solo uso.", True, "Específico (S): "),
            ("100% de las preguntas generadas están asociadas al contenido específico del informe del estudiante. El enlace de acceso tiene vigencia de 48 horas. El despacho de correos maneja hasta 500 estudiantes por curso sin costo adicional.", True, "Medible (M): "),
            ("Implementado con panel interactivo en Next.js (frontend), FastAPI (backend), y servicio de correo asíncrono con aiosmtplib usando Gmail SMTP gratuito.", True, "Alcanzable (A): "),
            ("Aborda el problema central de la verificación de aprendizaje real y asegura el paradigma Human-in-the-Loop al requerir la aprobación docente antes del despacho.", True, "Relevante (R): "),
            ("Completado al final del Sprint 3 (Fase de Reactivos y Despacho).", True, "Temporizado (T): ")
        ],
        border_color="6366F1",
        bg_color="F8FAFC"
    )

    # OE4
    add_callout_box(
        doc,
        "OE4: Evaluación Flash en Tiempo Real y Ruteo Automatizado de Defensas Orales",
        [
            ("Construir una interfaz de examinación en tiempo real para que los estudiantes respondan las preguntas flash, y un algoritmo que designe citas de defensa presencial exclusivamente para estudiantes con rendimientos atípicos o selección aleatoria de control.", True, "Enunciado: "),
            ("El estudiante accede al test mediante enlace tokenizado, responde 10 preguntas con temporizador por reactivo (60 segundos), y recibe un puntaje de coherencia inmediato. El sistema agenda defensas orales para tres grupos: (1) puntaje < 50% (posible falta de comprensión), (2) puntaje >= 95% (control de integridad), (3) 10% aleatorio del curso (muestreo de calidad).", True, "Específico (S): "),
            ("Latencia de conexión WebSocket <= 100ms. Temporizador estricto por pregunta (60s). El ruteo agenda al 100% de los estudiantes que cumplen las condiciones en el primer bloque horario disponible del profesor.", True, "Medible (M): "),
            ("Implementado con WebSockets sobre Starlette/FastAPI y frontend reactivo con Tailwind CSS. La lógica de ruteo considera la disponibilidad horaria del docente definida en su perfil.", True, "Alcanzable (A): "),
            ("Focaliza el tiempo presencial del docente únicamente en defensas necesarias, resolviendo la inviabilidad logística de interrogar a todo el curso.", True, "Relevante (R): "),
            ("Completado al final del Sprint 4 (Fase de Examinación y Ruteo).", True, "Temporizado (T): ")
        ],
        border_color="6366F1",
        bg_color="F8FAFC"
    )

    # OE5
    add_callout_box(
        doc,
        "OE5: Validación Integral y Cierre con Control Docente",
        [
            ("Implementar un módulo de auditoría y cierre de calificaciones que permita al profesor registrar los acuerdos de las defensas orales, ajustar manualmente la nota final, y dejar constancia de todas las acciones realizadas, manteniendo la decisión final bajo control exclusivo del docente.", True, "Enunciado: "),
            ("El docente accede a un panel donde visualiza: (1) nota preliminar del OE2, (2) puntaje del flash test del OE4, (3) resultado de la defensa oral. Puede confirmar la nota sugerida, modificarla manualmente, o dejarla en estado 'pendiente' para revisión posterior.", True, "Específico (S): "),
            ("100% de las calificaciones finales son confirmadas explícitamente por el docente antes de quedar registradas. El sistema genera un audit log con timestamp y usuario para cada acción crítica (cambio de nota, registro de defensa, decisión final). Tiempo de respuesta de la API <= 200ms.", True, "Medible (M): "),
            ("Módulo de auditoría estructurado en SQLAlchemy con tablas de logs inmutable. Panel administrativo con métricas de uso y trazabilidad.", True, "Alcanzable (A): "),
            ("Aborda el requisito ético fundamental del proyecto: la herramienta es un asistente, no un reemplazo del profesor. El docente mantiene la autoridad final sobre la evaluación.", True, "Relevante (R): "),
            ("Completado al final del Sprint 5 (Fase de Verificación y Cierre).", True, "Temporizado (T): ")
        ],
        border_color="6366F1",
        bg_color="F8FAFC"
    )

    # ─────────────────────────────────────────────────────────────
    # MATRIZ DE TRAZABILIDAD
    # ─────────────────────────────────────────────────────────────
    add_heading_2("2.3 Matriz de Trazabilidad Problema vs. Objetivos")
    
    mat_headers = ["Dimensión del Problema", "Causa Raíz", "Objetivo(s)", "Entregable Concreto"]
    mat_rows = [
        ["Falsos positivos de detectores IA", "Dependencia exclusiva de métricas estadísticas (perplejidad, burstiness) sin validar comprensión humana.", "OE2, OE3", "Evaluación contextualizada con pauta y materiales del curso; generación de preguntas personalizadas basadas en el contenido específico del informe."],
        ["Imposibilidad logística de interrogar a todos", "Restricción de horas de atención del docente en cursos masivos (60-200 alumnos).", "OE4", "Ruteo automático: solo defienden oralmente quienes tengan score < 50% (posible falta de comprensión), >= 95% (control de integridad), o 10% aleatorio (muestreo)."],
        ["Fricción de adopción tecnológica", "Estudiantes se resisten a crear cuentas y recordar contraseñas para una evaluación puntual.", "OE1, OE3", "Acceso sin login: nómina por CSV y enlace con token seguro de un solo uso enviado por correo electrónico."],
        ["Evaluación sin contexto de la asignatura", "La IA evalúa de forma aislada sin conocer la materia, pauta ni bibliografía del curso.", "OE2", "Módulo de Materiales que inyecta syllabus, guías y rúbricas como contexto en el prompt del LLM."],
        ["Pérdida de control y autoridad del docente", "Sistemas 100% automáticos sin intervención humana (falta de Human-in-the-Loop).", "OE3, OE5", "Editor interactivo de preguntas donde el docente aprueba el pool antes del despacho; panel de cierre con confirmación explícita de nota final."],
        ["Presupuesto cero para el MVP", "Costos prohibitivos de APIs transaccionales y servidores de pago en etapa de prototipo.", "OE3", "Despacho con Gmail SMTP gratuito (aiosmtplib) y arquitectura SQLite/FastAPI de costo cero."],
        ["Docente no puede probar el uso indebido de IA", "Falta de evidencia objetiva y trazable para respaldar decisiones académicas.", "OE2, OE5", "Desglose JSON del análisis con secciones sospechosas del informe; audit log inmutable de todas las acciones docentes."],
        ["Tiempo excesivo en corrección mecánica", "Docentes dedican hasta 25 horas semanales a revisar informes contra pauta.", "OE2, OE4", "Automatización del análisis preliminar (nota y feedback), focalizando el tiempo docente solo en defensas orales necesarias."]
    ]

    tbl_mat = doc.add_table(rows=len(mat_rows) + 1, cols=4)
    tbl_mat.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_mat.autofit = False
    col_widths_mat = [Inches(1.6), Inches(1.8), Inches(0.9), Inches(2.5)]
    
    for c_idx, head in enumerate(mat_headers):
        cell = tbl_mat.cell(0, c_idx)
        cell.width = col_widths_mat[c_idx]
        set_cell_background(cell, "1E3A8A")
        set_cell_margins(cell, top=100, bottom=100, left=100, right=100)
        p = cell.paragraphs[0]
        r = p.add_run(head)
        r.bold = True
        r.font.name = "Arial"
        r.font.size = Pt(8.5)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        
    for r_idx, row in enumerate(mat_rows):
        for c_idx, val in enumerate(row):
            cell = tbl_mat.cell(r_idx + 1, c_idx)
            cell.width = col_widths_mat[c_idx]
            set_cell_background(cell, "F8FAFC" if r_idx % 2 == 1 else "FFFFFF")
            set_cell_margins(cell, top=70, bottom=70, left=90, right=90)
            p = cell.paragraphs[0]
            p.paragraph_format.line_spacing = 1.1
            r = p.add_run(val)
            r.font.name = "Arial"
            r.font.size = Pt(8)
            if c_idx in [0, 2]:
                r.bold = True
            r.font.color.rgb = COLOR_DARK
            
    set_table_borders(tbl_mat, color="CBD5E1", sz="4", val="single")

    add_heading_2("2.4 Resumen de Contribución de Objetivos")
    
    con_headers = ["Objetivo", "Contribución Principal", "Impacto Esperado"]
    con_rows = [
        ["OE1", "Elimina barreras de adopción (sin cuentas) y estructura los datos.", "Alta adopción por parte de estudiantes; base técnica para el resto del sistema."],
        ["OE2", "Detecta uso de IA y evalúa con contexto de la asignatura.", "Reduce falsos positivos; entrega evidencia justificada al docente."],
        ["OE3", "Genera preguntas personalizadas; mantiene control docente.", "Verifica aprendizaje real; asegura Human-in-the-Loop."],
        ["OE4", "Focaliza defensas orales solo en casos necesarios.", "Escalabilidad a cursos masivos; uso eficiente del tiempo docente."],
        ["OE5", "Garantiza que la decisión final sea del profesor.", "Confianza en la herramienta; cumplimiento ético y legal."]
    ]
    tbl_con = doc.add_table(rows=len(con_rows) + 1, cols=3)
    tbl_con.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_con.autofit = False
    col_widths_con = [Inches(1.2), Inches(2.9), Inches(2.7)]
    
    for c_idx, head in enumerate(con_headers):
        cell = tbl_con.cell(0, c_idx)
        cell.width = col_widths_con[c_idx]
        set_cell_background(cell, "1E3A8A")
        set_cell_margins(cell, top=100, bottom=100, left=100, right=100)
        p = cell.paragraphs[0]
        r = p.add_run(head)
        r.bold = True
        r.font.name = "Arial"
        r.font.size = Pt(8.5)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        
    for r_idx, row in enumerate(con_rows):
        for c_idx, val in enumerate(row):
            cell = tbl_con.cell(r_idx + 1, c_idx)
            cell.width = col_widths_con[c_idx]
            set_cell_background(cell, "F8FAFC" if r_idx % 2 == 1 else "FFFFFF")
            set_cell_margins(cell, top=70, bottom=70, left=90, right=90)
            p = cell.paragraphs[0]
            p.paragraph_format.line_spacing = 1.1
            r = p.add_run(val)
            r.font.name = "Arial"
            r.font.size = Pt(8)
            if c_idx == 0:
                r.bold = True
            r.font.color.rgb = COLOR_DARK
            
    set_table_borders(tbl_con, color="CBD5E1", sz="4", val="single")

    doc.add_page_break()

    # ─────────────────────────────────────────────────────────────
    # SECCIÓN 3: ANÁLISIS DE REQUERIMIENTOS (45%)
    # ─────────────────────────────────────────────────────────────
    add_heading_1("3. Análisis de Requerimientos y Fundamentación (45%)")
    
    add_heading_2("3.1 Bases Teóricas y Metodológicas")
    add_bullet("Teoría de la Evaluación Auténtica (Grant Wiggins):", "Establece que la asimilación del conocimiento se evidencia cuando el estudiante puede explicar, defender y aplicar sus decisiones metodológicas frente a preguntas directas. IntegriEval traslada el foco desde '¿el texto fue generado por una máquina?' hacia '¿el estudiante domina los conceptos plasmados en su entrega?'.")
    add_bullet("Limitaciones Documentadas en Detectores de IA (Weber-Wulff et al., 2023):", "Los clasificadores binarios presentan precisiones inferiores al 70% en entornos universitarios. IntegriEval emplea la IA como asistente de lectura y generador de preguntas supervisado por humanos (Human-in-the-Loop).")

    add_heading_2("3.2 Requerimientos Funcionales (RF)")
    rfs = [
        ("RF01 - Gestión de Asignaturas:", "El sistema permite al docente crear y gestionar asignaturas indicando nombre y periodo."),
        ("RF02 - Carga Masiva de Nómina (CSV):", "Ingesta de archivos CSV con nombres y correos institucionales de alumnos sin requerir contraseñas."),
        ("RF03 - Configuración de Parámetros:", "Definición de pauta/prompt libre, rigor (strict/medium/lax), tamaño de pool y umbrales."),
        ("RF04 - Materiales de Apoyo:", "Subida de syllabus y guías en PDF/DOCX convertidos a Markdown para contexto del LLM."),
        ("RF05 - Subida Masiva de Trabajos:", "Carga en lote de PDFs con auto-asociación heurística o manual por estudiante."),
        ("RF06 - Conversión Estructurada a Markdown:", "Extracción de alta fidelidad con pymupdf4llm preservando títulos y tablas."),
        ("RF07 - Evaluación Asíncrona con IA:", "Cálculo de nota preliminar, feedback cualitativo y porcentaje de detección de IA."),
        ("RF08 - Gestión del Pool de Preguntas:", "Edición de alternativas, agregado de reactivos propios y selección aleatoria/manual de 10 preguntas."),
        ("RF09 - Despacho Asíncrono por Correo:", "Envío de invitación con token UUIDv4 (vigencia 48h) vía Gmail SMTP (aiosmtplib)."),
        ("RF10 - Flash Test WebSocket en Tiempo Real:", "Examinación cronometrada por pregunta, protección contra caídas y feedback final."),
        ("RF11 - Ruteo y Agendamiento Automático:", "Agendamiento en el primer bloque libre del profesor para alumnos convocados a oficina."),
        ("RF12 - Cierre de Cita y Ajuste de Calificación:", "Registro de acuerdos presenciales y actualización de la nota final del alumno.")
    ]
    for rf_title, rf_desc in rfs:
        add_bullet(rf_title, rf_desc)

    add_heading_2("3.3 Requerimientos No Funcionales (RNF)")
    rnfs = [
        ("RNF1 (Rendimiento):", "Soporte de 100 conexiones WebSocket concurrentes con latencia <= 50ms."),
        ("RNF2 (Seguridad):", "Tokens de examen UUIDv4 de alta entropía y contraseñas de docentes protegidas con bcrypt (factor >= 12)."),
        ("RNF3 (Resiliencia):", "Mecanismo de fallback automático a Mock Engine en caso de desconexión con la API de Anthropic."),
        ("RNF4 (Usabilidad):", "Interfaz Next.js + Tailwind CSS adaptada a accesibilidad WCAG 2.1 AA con tema oscuro de alto contraste."),
        ("RNF5 (Costo Cero):", "Operatividad 100% sustentada en tecnologías de código abierto (SQLite, FastAPI, Gmail SMTP).")
    ]
    for rnf_title, rnf_desc in rnfs:
        add_bullet(rnf_title, rnf_desc)

    add_heading_2("3.4 Evaluación Crítica de Alternativas Técnicas")
    
    alt_headers = ["Dimensión", "Alternativas Evaluadas", "Selección", "Justificación Técnica"]
    alt_rows = [
        ["Acceso Alumno", "1. Cuenta y Password.\n2. SSO Institucional.\n3. Token vía Email.", "Token vía Email", "Elimina fricción de registro; el docente no gestiona claves y el token valida posesión del correo oficial."],
        ["Estrategia de Integridad", "1. Detectores de caja negra.\n2. Proctored Browser.\n3. Flash Test Contextual.", "Flash Test Contextual", "Evita falsos positivos evaluando la autoría real en tiempo real mediante preguntas del propio trabajo."],
        ["Conversión PDF", "1. Texto plano (pypdf).\n2. OCR Tesseract.\n3. pymupdf4llm.", "pymupdf4llm", "Conserva jerarquía de encabezados, tablas y listas con 40% menos de ruido léxico para el LLM."],
        ["Servicio de Email", "1. SaaS de pago (SendGrid).\n2. Servidor Postfix VPS.\n3. Gmail SMTP asíncrono.", "Gmail SMTP (aiosmtplib)", "Cero costo para el MVP con hasta 500 correos diarios mediante contraseña de aplicación."]
    ]
    tbl_alt = doc.add_table(rows=len(alt_rows) + 1, cols=4)
    tbl_alt.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_alt.autofit = False
    col_widths_alt = [Inches(1.4), Inches(1.8), Inches(1.3), Inches(2.3)]
    
    for c_idx, head in enumerate(alt_headers):
        cell = tbl_alt.cell(0, c_idx)
        cell.width = col_widths_alt[c_idx]
        set_cell_background(cell, "1E3A8A")
        set_cell_margins(cell, top=100, bottom=100, left=100, right=100)
        p = cell.paragraphs[0]
        r = p.add_run(head)
        r.bold = True
        r.font.name = "Arial"
        r.font.size = Pt(8.5)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        
    for r_idx, row in enumerate(alt_rows):
        for c_idx, val in enumerate(row):
            cell = tbl_alt.cell(r_idx + 1, c_idx)
            cell.width = col_widths_alt[c_idx]
            set_cell_background(cell, "F8FAFC" if r_idx % 2 == 1 else "FFFFFF")
            set_cell_margins(cell, top=70, bottom=70, left=90, right=90)
            p = cell.paragraphs[0]
            p.paragraph_format.line_spacing = 1.1
            r = p.add_run(val)
            r.font.name = "Arial"
            r.font.size = Pt(8)
            if c_idx in [0, 2]:
                r.bold = True
            r.font.color.rgb = COLOR_DARK
            
    set_table_borders(tbl_alt, color="CBD5E1", sz="4", val="single")

    doc.add_page_break()

    # ─────────────────────────────────────────────────────────────
    # SECCIÓN 4: PLANIFICACIÓN Y PRODUCT BACKLOG (20%)
    # ─────────────────────────────────────────────────────────────
    add_heading_1("4. Planificación del Proyecto y Product Backlog (20%)")
    
    add_heading_2("4.1 Resumen de Épicas y Estimación de Esfuerzo (61 Story Points)")
    
    bk_headers = ["Épica", "Historias de Usuario", "Prioridad MoSCoW", "Story Points"]
    bk_rows = [
        ["ÉPICA 1: Gestión Académica y Nómina Sin Cuentas (OE1)", "US-01, US-02", "Must Have", "8 SP"],
        ["ÉPICA 2: Ingesta Masiva, Conversión a Markdown y Materiales (OE1)", "US-03, US-04", "Must Have", "13 SP"],
        ["ÉPICA 3: Motor de Evaluación Contextual y Detección IA (OE2)", "US-05, US-06", "Must / Should", "11 SP"],
        ["ÉPICA 4: Gestión Interactiva del Pool de Preguntas (OE3)", "US-07", "Must Have", "8 SP"],
        ["ÉPICA 5: Motor de Despacho y Flash Test en Tiempo Real (OE3/OE4)", "US-08, US-09", "Must Have", "13 SP"],
        ["ÉPICA 6: Agenda de Defensas y Cierre de Calificaciones (OE4/OE5)", "US-10, US-11", "Must Have", "8 SP"],
        ["TOTAL GENERAL DEL BACKLOG", "11 Historias Refinadas", "-", "61 SP"]
    ]
    tbl_bk = doc.add_table(rows=len(bk_rows) + 1, cols=4)
    tbl_bk.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_bk.autofit = False
    col_widths_bk = [Inches(2.8), Inches(1.5), Inches(1.3), Inches(1.2)]
    
    for c_idx, head in enumerate(bk_headers):
        cell = tbl_bk.cell(0, c_idx)
        cell.width = col_widths_bk[c_idx]
        set_cell_background(cell, "1E3A8A")
        set_cell_margins(cell, top=100, bottom=100, left=100, right=100)
        p = cell.paragraphs[0]
        r = p.add_run(head)
        r.bold = True
        r.font.name = "Arial"
        r.font.size = Pt(8.5)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        
    for r_idx, row in enumerate(bk_rows):
        is_total = (r_idx == len(bk_rows) - 1)
        for c_idx, val in enumerate(row):
            cell = tbl_bk.cell(r_idx + 1, c_idx)
            cell.width = col_widths_bk[c_idx]
            set_cell_background(cell, "EFF6FF" if is_total else ("F8FAFC" if r_idx % 2 == 1 else "FFFFFF"))
            set_cell_margins(cell, top=70, bottom=70, left=90, right=90)
            p = cell.paragraphs[0]
            p.paragraph_format.line_spacing = 1.1
            r = p.add_run(val)
            r.font.name = "Arial"
            r.font.size = Pt(8.5 if is_total else 8)
            if is_total or c_idx == 0:
                r.bold = True
            r.font.color.rgb = COLOR_PRIMARY if is_total else COLOR_DARK
            
    set_table_borders(tbl_bk, color="CBD5E1", sz="4", val="single")

    add_heading_2("4.2 Historias de Usuario Representativas y Criterios de Aceptación (Gherkin)")
    
    # US-02
    add_callout_box(
        doc,
        "US-02: Importación de Estudiantes vía CSV (Épica 1 — 5 SP | MUST HAVE)",
        [
            ("Docente o ayudante de cátedra.", True, "Como: "),
            ("Subir un archivo CSV con la lista de mis alumnos (nombre y correo).", True, "Quiero: "),
            ("Registrar a toda la sección en segundos sin que ellos deban crear una cuenta.", True, "Para: "),
            ("Criterios de Aceptación (Gherkin):", True, ""),
            ("• Dado un archivo CSV con formato Nombre,Correo con codificación UTF-8 BOM.\n• Cuando el docente lo sube en la pestaña '2. Estudiantes'.\n• Entonces el backend procesa las filas, descarta correos duplicados en el curso e informa el total de alumnos creados.", False, "")
        ],
        border_color="6366F1",
        bg_color="F8FAFC"
    )

    # US-05
    add_callout_box(
        doc,
        "US-05: Análisis Automatizado de Pauta y Detección de IA (Épica 3 — 8 SP | MUST HAVE)",
        [
            ("Profesor evaluador.", True, "Como: "),
            ("Que la IA analice cada trabajo contra la pauta y los materiales de clase.", True, "Quiero: "),
            ("Obtener una nota preliminar justificada, desglose por rúbrica y porcentaje de probabilidad de IA.", True, "Para: "),
            ("Criterios de Aceptación (Gherkin):", True, ""),
            ("• Dado un informe PDF en estado 'processing'.\n• Cuando la IA completa el análisis con Claude 3.5 Sonnet.\n• Entonces el estado cambia a 'done', persistiendo nota, feedback cualitativo y desglose en BD.", False, "")
        ],
        border_color="6366F1",
        bg_color="F8FAFC"
    )

    # US-08
    add_callout_box(
        doc,
        "US-08: Despacho Asíncrono de Flash Test por Correo (Épica 5 — 5 SP | MUST HAVE)",
        [
            ("Sistema evaluador.", True, "Como: "),
            ("Enviar un correo HTML institucional con un enlace tokenizado de un solo uso.", True, "Quiero: "),
            ("Que el estudiante acceda a rendir su Flash Test seguro sin iniciar sesión.", True, "Para: "),
            ("Criterios de Aceptación (Gherkin):", True, ""),
            ("• Dado un set de 10 preguntas aprobado por el profesor.\n• Cuando se ejecuta send_flash_test().\n• Entonces se genera un token UUIDv4 con 48h de vigencia y se despacha el correo vía aiosmtplib.", False, "")
        ],
        border_color="6366F1",
        bg_color="F8FAFC"
    )

    # US-10
    add_callout_box(
        doc,
        "US-10: Ruteo Inteligente y Agendamiento Automático de Citas (Épica 6 — 5 SP | MUST HAVE)",
        [
            ("Plataforma IntegriEval.", True, "Como: "),
            ("Clasificar el resultado del flash test y agendar una cita en el primer bloque libre del profesor.", True, "Quiero: "),
            ("Coordinar la defensa presencial automáticamente si el alumno obtuvo puntaje bajo, alto o aleatorio.", True, "Para: "),
            ("Criterios de Aceptación (Gherkin):", True, ""),
            ("• Dado un estudiante con score flash del 40% (umbral bajo < 50%).\n• Cuando finaliza la sesión del flash test.\n• Entonces se marca review_required = True, se asigna el primer bloque disponible del profesor y se envía la notificación de cita por correo.", False, "")
        ],
        border_color="6366F1",
        bg_color="F8FAFC"
    )

    # ─────────────────────────────────────────────────────────────
    # SECCIÓN 5: CONCLUSIONES
    # ─────────────────────────────────────────────────────────────
    add_heading_1("5. Conclusiones y Valor Estratégico")
    add_body(
        "IntegriEval resuelve la tensión contemporánea entre la adopción de herramientas de IA generativa y la exigencia de certificar competencias académicas fidedignas. Al reemplazar los detectores tradicionales de caja negra por un modelo híbrido de análisis contextualizado, evaluación flash reactiva y defensa oral focalizada, la plataforma optimiza el tiempo docente, garantiza transparencia ética y entrega una experiencia ágil y justa para toda la comunidad universitaria."
    )

    doc.save(filename)
    print("Word document created successfully:", filename)

if __name__ == "__main__":
    build_docx()
