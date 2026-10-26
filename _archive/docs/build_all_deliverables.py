import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=140, right=140):
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

def add_callout_box_word(doc, title, content_paragraphs, border_color="2563EB", bg_color="F8FAFC"):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    
    cell = table.cell(0, 0)
    cell.width = Inches(6.8)
    set_cell_background(cell, bg_color)
    set_cell_margins(cell, top=140, bottom=140, left=180, right=180)
    
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
    run_title.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)
    
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
    
    p_spacer = doc.add_paragraph()
    p_spacer.paragraph_format.space_before = Pt(0)
    p_spacer.paragraph_format.space_after = Pt(4)


# =========================================================================
# GENERADOR WORD (.DOCX)
# =========================================================================
def generate_complete_word(filename="docs/integrieval-blueprint.docx"):
    doc = Document()
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)
        
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("IntegriEval — Blueprint Maestro de Construcción y Arquitectura (INFO1197)")
        hrun.font.name = "Arial"
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)

        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        frun = fp.add_run("IntegriEval System — Sebastian Cisternas, Benjamin Sobarzo | Septiembre 2026")
        frun.font.name = "Arial"
        frun.font.size = Pt(8.5)
        frun.font.color.rgb = RGBColor(0x94, 0xA3, 0xB8)

    COLOR_PRIMARY = RGBColor(0x1E, 0x3A, 0x8A)
    COLOR_SECONDARY = RGBColor(0x25, 0x63, 0xEB)
    COLOR_DARK = RGBColor(0x0F, 0x17, 0x2A)
    COLOR_MUTED = RGBColor(0x47, 0x55, 0x69)

    def add_h1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(16)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        r.bold = True
        r.font.name = "Arial"
        r.font.size = Pt(14)
        r.font.color.rgb = COLOR_PRIMARY

    def add_h2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(11)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        r.bold = True
        r.font.name = "Arial"
        r.font.size = Pt(11.5)
        r.font.color.rgb = COLOR_SECONDARY

    def add_p(text, space_after=4):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.line_spacing = 1.15
        r = p.add_run(text)
        r.font.name = "Arial"
        r.font.size = Pt(9.5)
        r.font.color.rgb = COLOR_DARK

    def add_b(bold_txt, text):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.15
        if bold_txt:
            r1 = p.add_run(bold_txt + " ")
            r1.bold = True
            r1.font.name = "Arial"
            r1.font.size = Pt(9.5)
            r1.font.color.rgb = COLOR_DARK
        r2 = p.add_run(text)
        r2.font.name = "Arial"
        r2.font.size = Pt(9.5)
        r2.font.color.rgb = COLOR_DARK

    # Portada
    p_t = doc.add_paragraph()
    p_t.paragraph_format.space_before = Pt(30)
    p_t.paragraph_format.space_after = Pt(4)
    p_t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_t = p_t.add_run("IntegriEval")
    r_t.bold = True
    r_t.font.name = "Arial"
    r_t.font.size = Pt(26)
    r_t.font.color.rgb = COLOR_PRIMARY

    p_s = doc.add_paragraph()
    p_s.paragraph_format.space_after = Pt(20)
    p_s.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_s = p_s.add_run("Blueprint Maestro de Construcción y Arquitectura de Software\nGuía Integral de Implementación de 0 a Producción")
    r_s.font.name = "Arial"
    r_s.font.size = Pt(12)
    r_s.font.color.rgb = COLOR_SECONDARY

    # Metadata table
    tbl_m = doc.add_table(rows=4, cols=2)
    tbl_m.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_m.autofit = False
    m_rows = [
        [("Trabajo de Título:", True), ("INFO1197 — Ingeniería Civil Informática", False), ("Fecha:", True), ("Septiembre 2026", False)],
        [("Autores:", True), ("Sebastian Cisternas, Benjamin Sobarzo", False), ("Versión:", True), ("1.0.0 (Validado)", False)],
        [("Repositorio:", True), ("github.com/blosttt/IntegriEval", False), ("Entorno:", True), ("Educación Superior / Cátedras", False)],
        [("Alcance:", True), ("Cursos Masivos, Open-Source, Costo Cero", False), ("Stack:", True), ("Next.js 15 + FastAPI + Claude/Mock", False)],
    ]
    for r_i, row in enumerate(m_rows):
        c1 = tbl_m.cell(r_i, 0)
        c2 = tbl_m.cell(r_i, 1)
        c1.width = Inches(3.4)
        c2.width = Inches(3.4)
        set_cell_background(c1, "F8FAFC")
        set_cell_background(c2, "F8FAFC")
        set_cell_margins(c1, 60, 60, 100, 100)
        set_cell_margins(c2, 60, 60, 100, 100)
        
        p1 = c1.paragraphs[0]
        p1.add_run(row[0][0] + " ").bold = True
        p1.add_run(row[1][0])
        
        p2 = c2.paragraphs[0]
        p2.add_run(row[2][0] + " ").bold = True
        p2.add_run(row[3][0])

    set_table_borders(tbl_m, color="93C5FD", sz="4", val="single")
    doc.add_page_break()

    # 1. VISIÓN
    add_h1("1. Definición Clara del Problema y Visión de Negocio (10%)")
    add_h2("1.1 Contexto y Antecedentes")
    add_p("La democratización de los Modelos de Lenguaje Grande (LLMs) como GPT-4, Claude y Gemini ha alterado irreversiblemente la evaluación en la educación superior. En la dinámica actual, los estudiantes entregan sus trabajos en el LMS institucional (Canvas, Moodle, Blackboard). Los docentes deben revisar cientos de páginas en PDF careciendo de mecanismos confiables para verificar si el contenido refleja competencias reales del alumno o fue generado por IA.")
    
    add_h2("1.2 Articulación del Problema (3 Dimensiones Críticas)")
    add_b("1. Inviabilidad de los Detectores Estadísticos de 'Caja Negra':", "Herramientas como Turnitin AI presentan altas tasas de falsos positivos y negativos al basarse únicamente en perplejidad estadística, careciendo de validez jurídica y ética para aplicar sanciones.")
    add_b("2. Inviabilidad Logística de la Interrogación Universal:", "Examinar oralmente al 100% de los estudiantes en cursos masivos (60 a 200 alumnos) es físicamente imposible por restricciones de tiempo de atención docente.")
    add_b("3. Sobrecarga Cognitiva y Temporal:", "Los docentes dedican hasta 25 horas semanales a la corrección mecánica de informes contrastándolos con la pauta y el material del curso.")

    # 2. OBJETIVOS
    add_h1("2. Objetivos del Proyecto y Matriz de Trazabilidad (25%)")
    add_h2("2.1 Objetivo General")
    add_callout_box_word(
        doc,
        "Objetivo General del Proyecto",
        [
            ("Desarrollar un MVP de plataforma web que asista al docente en la verificación del aprendizaje real del estudiante, a través de un flujo que integra análisis automatizado del PDF, generación de preguntas flash personalizadas y soporte para validación oral focalizada, sin reemplazar el criterio docente como autoridad final. (Alcance: Educación superior, cursos masivos, MVP open-source y sin costos recurrentes).", False, "")
        ],
        border_color="2563EB",
        bg_color="EFF6FF"
    )

    add_h2("2.2 Objetivos Específicos SMART (4 Sprints)")
    oe_list = [
        ("OE1 (Sprint 1): Análisis de Requerimientos", [
            ("Analizar los requerimientos funcionales y no funcionales del proceso de verificación de aprendizaje.", True, "Enunciado: "),
            ("Levantamiento de problema, actores y restricciones.", True, "Specific: "),
            ("Documento validado con matriz de trazabilidad completa.", True, "Measurable: "),
            ("Base para el diseño correcto del MVP.", True, "Relevant: "),
            ("Sprint 1.", True, "Temporizado: ")
        ]),
        ("OE2 (Sprint 2): Diseño de Arquitectura y Decisiones Técnicas", [
            ("Diseñar la arquitectura del sistema y las decisiones técnicas del MVP.", True, "Enunciado: "),
            ("Arquitectura sin login, evaluación contextual con LLM, estrategia costo-cero.", True, "Specific: "),
            ("100% de decisiones técnicas justificadas en matriz de alternativas.", True, "Measurable: "),
            ("Evita retrabajo en implementación.", True, "Relevant: "),
            ("Sprint 2.", True, "Temporizado: ")
        ]),
        ("OE3 (Sprint 3): Implementación de Módulos Funcionales", [
            ("Implementar los módulos funcionales del MVP.", True, "Enunciado: "),
            ("Ingesta/nómina, motor IA, pool de preguntas, flash test, panel y cierre.", True, "Specific: "),
            ("61 Story Points entregados en 4 Sprints (11 Historias de Usuario).", True, "Measurable: "),
            ("Entrega funcional completa.", True, "Relevant: "),
            ("Sprint 3.", True, "Temporizado: ")
        ]),
        ("OE4 (Sprint 4): Validación de Funcionamiento y Control Docente", [
            ("Validar el funcionamiento del sistema y el control docente sobre el resultado.", True, "Enunciado: "),
            ("Rendimiento (<=15s, <=100ms), precisión detección IA (>=75%), 100% notas confirmadas por docente.", True, "Specific: "),
            ("Métricas RNF cumplidas + AuditLog inmutable verificado.", True, "Measurable: "),
            ("Confianza y cumplimiento ético/legal.", True, "Relevant: "),
            ("Sprint 4.", True, "Temporizado: ")
        ])
    ]
    for oe_t, oe_c in oe_list:
        add_callout_box_word(doc, oe_t, oe_c)

    doc.add_page_break()

    # 3. REQUERIMIENTOS
    add_h1("3. Análisis de Requerimientos y Fundamentación (45%)")
    add_h2("3.1 Bases Teóricas y Metodológicas")
    add_b("Teoría de la Evaluación Auténtica (Grant Wiggins):", "La asimilación del conocimiento se evidencia cuando el estudiante puede explicar y defender su trabajo. IntegriEval traslada el foco desde '¿el texto fue generado por IA?' a '¿el estudiante domina los conceptos?'.")
    add_b("Limitaciones Documentadas en Detectores de IA (Weber-Wulff et al., 2023):", "Los clasificadores binarios presentan precisiones inferiores al 70%. IntegriEval usa IA como asistente de lectura y generador de preguntas supervisado por humanos.")
    add_b("Principio de Supervisión Humana (Human-in-the-Loop):", "En sistemas de IA educativos, el juicio humano debe ser el decisor final sobre las calificaciones.")

    add_h2("3.2 Requerimientos Funcionales (RF-001 al RF-015)")
    rfs = [
        ("RF-001 [Must]:", "Crear y gestionar asignaturas (nombre, periodo, año)."),
        ("RF-002 [Must]:", "Ingesta de CSV con nombres y correos, validando formato y duplicados."),
        ("RF-003 [Must]:", "Configurar: prompt, rigor, pool (10-30), umbrales visuales."),
        ("RF-004 [Must]:", "Subir materiales (PDF/DOCX) y convertirlos a Markdown para contexto."),
        ("RF-005 [Must]:", "Carga masiva de PDFs y asociación automática por nombre de archivo."),
        ("RF-006 [Must]:", "Extraer PDFs a Markdown preservando títulos, tablas y listas (pymupdf4llm)."),
        ("RF-007 [Must]:", "Evaluar con Modelos LLM: nota, feedback, % detección IA (Anexo A)."),
        ("RF-008 [Must]:", "Generar pool de preguntas con LLM basadas en temática del informe y material."),
        ("RF-009 [Must]:", "Permitir al docente editar/eliminar/agregar preguntas y seleccionar N reactivos."),
        ("RF-010 [Must]:", "Despachar flash test con tokens UUIDv4 (vigencia 48h) vía Gmail SMTP."),
        ("RF-011 [Must]:", "Interfaz flash test con WebSockets y temporizador de 60s por pregunta."),
        ("RF-012 [Must]:", "Panel de resultados para docente con métricas clave para decisión."),
        ("RF-013 [Must]:", "Registrar acuerdos de defensas, ajustar nota final y audit log inmutable."),
        ("RF-014 [Should]:", "Contar con Mock Engine de contingencia para fallback offline."),
        ("RF-015 [Por definir]:", "Autenticación docente (Pendiente).")
    ]
    for r_id, r_d in rfs:
        add_b(r_id, r_d)

    add_h2("3.3 Requerimientos No Funcionales (RNF-001 al RNF-013)")
    rnfs = [
        ("RNF-001 (Rendimiento):", "Soportar 100 conexiones WebSocket concurrentes (Latencia <= 50ms)."),
        ("RNF-002 (Rendimiento):", "Procesar informe en <= 15s (CPU) en 95% de casos."),
        ("RNF-003 (Rendimiento):", "API de cierre de calificaciones <= 200ms."),
        ("RNF-004 (Seguridad):", "Tokens UUIDv4 criptográficos (RFC 4122)."),
        ("RNF-005 (Seguridad):", "Contraseñas docentes protegidas con bcrypt (factor >= 12)."),
        ("RNF-006 (Seguridad):", "Control de accesos basado en roles (RBAC) por asignatura."),
        ("RNF-007 (Resiliencia):", "Fallback automático a Mock Engine tras timeout > 30s."),
        ("RNF-008 (Resiliencia):", "Reconexión de WebSocket <= 120s preservando estado."),
        ("RNF-009 (Usabilidad):", "Accesibilidad WCAG 2.1 AA y tema oscuro."),
        ("RNF-010 (Costo):", "100% open-source, sin costos recurrentes."),
        ("RNF-013 (Privacidad):", "Cumplimiento con Ley N° 21.719 (Protección de Datos Personales Chile).")
    ]
    for rn_id, rn_d in rnfs:
        add_b(rn_id, rn_d)

    doc.add_page_break()

    # 4. PRODUCT BACKLOG
    add_h1("4. Planificación del Proyecto y Product Backlog (20%)")
    add_h2("4.1 Resumen de Épicas y Estimación de Esfuerzo (61 Story Points en 4 Sprints)")
    
    bk_headers = ["Épica", "Historias", "Prioridad", "SP", "Sprint"]
    bk_rows = [
        ["ÉPICA 1: Gestión y Nómina (OE1)", "US-01, US-02", "Must Have", "8 SP", "Sprint 1 (4.2 sem con Ép. 2)"],
        ["ÉPICA 2: Ingesta y Conversión (OE1)", "US-03, US-04", "Must Have", "13 SP", "Sprint 1 (Total: 21 SP)"],
        ["ÉPICA 3: Motor de Evaluación (OE2)", "US-05, US-06", "Must Have", "11 SP", "Sprint 2 (2.2 sem)"],
        ["ÉPICA 4: Pool de Preguntas (OE3)", "US-07", "Must Have", "8 SP", "Sprint 3 (4.2 sem con Ép. 5)"],
        ["ÉPICA 5: Despacho y Flash Test (OE3)", "US-08, US-09", "Must Have", "13 SP", "Sprint 3 (Total: 21 SP)"],
        ["ÉPICA 6: Resultados y Cierre (OE4)", "US-10, US-11", "Must Have", "8 SP", "Sprint 4 (1.6 sem)"],
        ["TOTAL GENERAL DEL BACKLOG", "11 Historias", "Must Have", "61 SP", "4 Sprints (≈ 12.2 sem)"]
    ]
    tbl_b = doc.add_table(rows=len(bk_rows) + 1, cols=5)
    tbl_b.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_b.autofit = False
    col_w_b = [Inches(2.0), Inches(1.2), Inches(1.0), Inches(0.8), Inches(1.8)]
    
    for c_i, h in enumerate(bk_headers):
        cell = tbl_b.cell(0, c_i)
        cell.width = col_w_b[c_i]
        set_cell_background(cell, "1E3A8A")
        set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.bold = True
        r.font.size = Pt(8.5)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        
    for r_i, r_data in enumerate(bk_rows):
        is_tot = (r_i == len(bk_rows) - 1)
        for c_i, val in enumerate(r_data):
            cell = tbl_b.cell(r_i + 1, c_i)
            cell.width = col_w_b[c_i]
            set_cell_background(cell, "EFF6FF" if is_tot else ("F8FAFC" if r_i % 2 == 1 else "FFFFFF"))
            set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
            p = cell.paragraphs[0]
            r = p.add_run(val)
            r.font.size = Pt(8.5 if is_tot else 8)
            if is_tot or c_i == 0:
                r.bold = True
            r.font.color.rgb = COLOR_PRIMARY if is_tot else COLOR_DARK
            
    set_table_borders(tbl_b, color="CBD5E1", sz="4", val="single")

    add_h2("4.2 Historias de Usuario (US-01 a US-11)")
    hu_list = [
        ("US-01: Creación y Gestión de Asignaturas (3 SP)", "Como Docente quiero crear y gestionar asignaturas para organizar mis cursos. CA: Dado un docente autenticado, cuando crea una asignatura, entonces queda registrada."),
        ("US-02: Importación de Estudiantes vía CSV (5 SP)", "Como Docente o ayudante quiero subir CSV con lista de alumnos para registrar la sección en segundos sin crear cuentas. CA: Dado un CSV válido, se procesan las filas y se informa el total creado."),
        ("US-03: Subida Masiva de Trabajos y Conversión a Markdown (8 SP)", "Como Ayudante o Docente quiero subir múltiples PDFs y extraer su contenido semántico con pymupdf4llm."),
        ("US-04: Gestión de Materiales de Apoyo (5 SP)", "Como Docente quiero subir syllabus y rúbricas en PDF/DOCX para dar contexto al LLM."),
        ("US-05: Análisis Automatizado con LLM (8 SP)", "Como Docente quiero que la IA analice cada trabajo contra la pauta y materiales para obtener nota preliminar y % IA."),
        ("US-06: Motor de Contingencia (Mock Engine) (3 SP)", "Como Sistema quiero tener un fallback heurístico sin conexión para garantizar operatividad continua."),
        ("US-07: Generación y Gestión del Pool de Preguntas (8 SP)", "Como Docente quiero revisar, editar y aprobar 10 preguntas de un pool de 20 generadas por IA."),
        ("US-08: Despacho Asíncrono de Flash Test por Correo (5 SP)", "Como Sistema quiero enviar correo con enlace tokenizado UUIDv4 (48h) mediante Gmail SMTP asíncrono."),
        ("US-09: Interfaz del Flash Test en Tiempo Real (WebSocket) (8 SP)", "Como Estudiante quiero responder 10 preguntas con temporizador de 60s por reactivo y recibir mi puntaje."),
        ("US-10: Panel de Resultados del Flash Test (5 SP)", "Como Docente quiero visualizar resultados consolidados y ruteo a citas presenciales (<50%, >=95% o 10% aleatorio)."),
        ("US-11: Cierre de Calificaciones y Auditoría (3 SP)", "Como Docente quiero registrar acuerdos de defensas presenciales, ratificar nota final y registrar AuditLog inmutable.")
    ]
    for hu_t, hu_d in hu_list:
        add_b(hu_t, hu_d)

    # 5. ANEXO A JSON
    add_h1("5. Anexo A: Estructura JSON de Evaluación (RF-007)")
    add_p("A continuación se define la estructura JSON exacta emitida por el motor de análisis y persistida en BD:")
    
    json_text = """{
  "porcentaje_logro": "65%",
  "feedback": {
    "fortalezas": ["Buena estructura", "Argumentos sólidos en sección 2"],
    "debilidades": ["Falta profundidad en metodología", "Citas incompletas"],
    "recomendaciones": ["Ampliar sección de resultados", "Revisar formato APA"]
  },
  "deteccion_ia": {
    "porcentaje": "45%",
    "nivel_confianza": "medio",
    "secciones_sospechosas": ["Introducción", "Conclusiones"],
    "justificacion": "Estilo uniforme, falta de variabilidad léxica"
  },
  "desglose_rubrica": {
    "contenido": "60%",
    "estructura": "70%",
    "ortografia": "65%"
  },
  "evaluacion_respuestas": {
    "nivel_rigor_aplicado": "medium",
    "porcentaje_coherencia": "70%",
    "respuestas_correctas": "7/10",
    "preguntas_falladas": [
      "P3: Explicar metodología utilizada",
      "P8: Justificar elección de muestra"
    ],
    "observacion_ia": "El estudiante demuestra comprensión parcial del contenido. Se recomienda interrogación oral focalizada.",
    "requiere_defensa_oral": true
  }
}"""
    t_j = doc.add_table(rows=1, cols=1)
    t_j.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell_j = t_j.cell(0, 0)
    cell_j.width = Inches(6.8)
    set_cell_background(cell_j, "0F172A")
    set_cell_margins(cell_j, 120, 120, 140, 140)
    p_j = cell_j.paragraphs[0]
    r_j = p_j.add_run(json_text)
    r_j.font.name = "Courier New"
    r_j.font.size = Pt(8)
    r_j.font.color.rgb = RGBColor(0x38, 0xBD, 0xF8) # Cyan highlight
    
    set_table_borders(t_j, color="334155", sz="6", val="single")

    doc.save(filename)
    print("Complete Word Deliverable built successfully:", filename)

if __name__ == "__main__":
    os.makedirs("docs", exist_ok=True)
    generate_complete_word("docs/integrieval-blueprint.docx")
    generate_complete_word("documento_ingenieria_integrieval.docx")
