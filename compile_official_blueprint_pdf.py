import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            return  # No header/footer on cover
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#475569"))
        self.drawString(54, 750, "IntegriEval — Blueprint de Especificación Formal (INFO1197)")
        self.drawRightString(558, 750, "Versión 1.0 (Septiembre 2026)")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 742, 558, 742)
        self.line(54, 45, 558, 45)
        self.setFont("Helvetica", 8)
        self.drawString(54, 32, "Ingeniería Civil Informática — Sebastian Cisternas, Benjamin Sobarzo")
        self.drawRightString(558, 32, f"Página {self._pageNumber} de {page_count}")
        self.restoreState()


def build_pdf(filename="docs/blueprint_integrieval.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=64,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    c_primary = colors.HexColor("#1E3A8A")     # Azul Marino
    c_secondary = colors.HexColor("#2563EB")   # Azul Royal
    c_indigo = colors.HexColor("#4338CA")      # Índigo
    c_text = colors.HexColor("#0F172A")        # Slate 900
    c_muted = colors.HexColor("#475569")       # Slate 600
    c_bg = colors.HexColor("#F8FAFC")          # Gris Fondo
    
    styles.add(ParagraphStyle('CovTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=24, leading=28, textColor=c_primary, alignment=1))
    styles.add(ParagraphStyle('CovSubtitle', parent=styles['Normal'], fontName='Helvetica', fontSize=11, leading=15, textColor=c_indigo, alignment=1))
    styles.add(ParagraphStyle('SecTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, leading=15, textColor=c_primary, spaceBefore=10, spaceAfter=4, keepWithNext=True))
    styles.add(ParagraphStyle('SubSecTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9.5, leading=13, textColor=c_secondary, spaceBefore=6, spaceAfter=2, keepWithNext=True))
    styles.add(ParagraphStyle('Body', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=11, textColor=c_text, spaceAfter=3))
    styles.add(ParagraphStyle('DocBullet', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=11, textColor=c_text, leftIndent=8, spaceAfter=2))
    styles.add(ParagraphStyle('TCell', parent=styles['Normal'], fontName='Helvetica', fontSize=7.5, leading=10, textColor=c_text))
    styles.add(ParagraphStyle('THead', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7.5, leading=10, textColor=colors.white))
    styles.add(ParagraphStyle('JsonCode', parent=styles['Normal'], fontName='Courier', fontSize=7, leading=9, textColor=c_text))

    story = []

    # PORTADA
    story.append(Spacer(1, 20))
    story.append(Paragraph("IntegriEval", styles['CovTitle']))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Sistema Semi-Automatizado de Evaluación de Integridad Académica, Detección de IA y Verificación Oral Flash", styles['CovSubtitle']))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="90%", thickness=1.5, color=c_secondary, spaceBefore=6, spaceAfter=12))

    meta_table_data = [
        [Paragraph("<b>Trabajo de Título:</b> INFO1197", styles['TCell']), Paragraph("<b>Proyecto:</b> Ingeniería Civil Informática", styles['TCell'])],
        [Paragraph("<b>Fecha:</b> Septiembre 2026", styles['TCell']), Paragraph("<b>Versión:</b> 1.0 (Borrador para validación)", styles['TCell'])],
        [Paragraph("<b>Equipo:</b> Sebastian Cisternas, Benjamin Sobarzo", styles['TCell']), Paragraph("<b>Entorno:</b> Educación Superior / Cátedras Universitarias", styles['TCell'])],
        [Paragraph("<b>Repositorio:</b> github.com/blosttt/IntegriEval", styles['TCell']), Paragraph("<b>Alcance:</b> Cursos masivos, Open-source, Costo cero", styles['TCell'])]
    ]
    t_meta = Table(meta_table_data, colWidths=[250, 254])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_bg),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 10))

    # SECCIÓN 1
    story.append(Paragraph("1. Definición Clara del Problema (10%)", styles['SecTitle']))
    story.append(Paragraph("<b>1.1 Contexto y Antecedentes:</b> La democratización de los LLMs ha transformado la evaluación en la educación superior. Los estudiantes entregan trabajos digitales, pero los docentes carecen de herramientas confiables y justas para verificar si el contenido refleja competencias reales o fue generado por IA.", styles['Body']))
    story.append(Paragraph("<b>1.2 Articulación del Problema:</b><br/>"
                           "1. <i>Inviabilidad de los Detectores Estadísticos de 'Caja Negra':</i> Altas tasas de falsos positivos/negativos, sin validez jurídica/ética.<br/>"
                           "2. <i>Inviabilidad Logística de la Interrogación Universal:</i> Imposible de implementar en cursos masivos (60 a 200 alumnos).<br/>"
                           "3. <i>Sobrecarga Cognitiva y Temporal:</i> Docentes dedican gran cantidad de tiempo a la corrección mecánica de informes.", styles['Body']))
    
    stk_rows = [
        [Paragraph("<b>Stakeholder</b>", styles['THead']), Paragraph("<b>Percepción y Dolores Identificados</b>", styles['THead']), Paragraph("<b>Expectativa y Validación de Relevancia</b>", styles['THead'])],
        [Paragraph("<b>Docentes</b>", styles['TCell']), Paragraph("\"No sé si el alumno aprendió o si un LLM hizo el trabajo. No puedo interrogar a 100 alumnos ni acusar sin pruebas.\"", styles['TCell']), Paragraph("Herramienta que entregue notas preliminares justificadas y evidencia para decidir a quiénes citar para defensa oral.", styles['TCell'])],
        [Paragraph("<b>Ayudantes</b>", styles['TCell']), Paragraph("\"Revisar 80 PDFs idénticos es agotador y dilata la retroalimentación.\"", styles['TCell']), Paragraph("Subida masiva en lote y extracción de resúmenes estructurados en Markdown.", styles['TCell'])],
        [Paragraph("<b>Estudiantes</b>", styles['TCell']), Paragraph("\"Frustrante que un detector te acuse injustamente. Si hay dudas, prefiero que me pregunten sobre mi trabajo.\"", styles['TCell']), Paragraph("Proceso transparente y derecho a defensa oral.", styles['TCell'])],
        [Paragraph("<b>Dirección Carrera</b>", styles['TCell']), Paragraph("\"Debemos resguardar el prestigio y evitar sanciones arbitrarias que deriven en litigios.\"", styles['TCell']), Paragraph("Trazabilidad auditable y defensas orales fundamentadas en evidencia.", styles['TCell'])],
    ]
    t_stk = Table(stk_rows, colWidths=[90, 200, 214])
    t_stk.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg]),
        ('PADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_stk)
    story.append(Spacer(1, 6))

    # SECCIÓN 2
    story.append(Paragraph("2. Objetivos Específicos y Matriz de Trazabilidad (25%)", styles['SecTitle']))
    story.append(Paragraph("<b>2.1 Objetivo General:</b> Desarrollar un MVP de plataforma web que asista al docente en la verificación del aprendizaje real del estudiante, a través de un flujo que integra análisis automatizado del PDF, generación de preguntas flash personalizadas y soporte para validación oral focalizada, sin reemplazar el criterio docente como autoridad final. <i>(Alcance: Cursos masivos, Open-source, Costo cero, Sin integración LMS inicial)</i>.", styles['Body']))
    
    oe_rows = [
        [Paragraph("<b>ID</b>", styles['THead']), Paragraph("<b>Objetivo Específico</b>", styles['THead']), Paragraph("<b>Criterio SMART (Resumen)</b>", styles['THead']), Paragraph("<b>Sprint</b>", styles['THead'])],
        [Paragraph("<b>OE1</b>", styles['TCell']), Paragraph("Analizar los requerimientos funcionales y no funcionales del proceso de verificación de aprendizaje.", styles['TCell']), Paragraph("<b>S:</b> Levantamiento de problema, actores, restricciones.<br/><b>M:</b> Documento validado con matriz completa.<br/><b>R:</b> Base para el diseño correcto del MVP.", styles['TCell']), Paragraph("Sprint 1", styles['TCell'])],
        [Paragraph("<b>OE2</b>", styles['TCell']), Paragraph("Diseñar la arquitectura del sistema y las decisiones técnicas del MVP.", styles['TCell']), Paragraph("<b>S:</b> Arquitectura sin login, evaluación contextual con LLM, costo-cero.<br/><b>M:</b> 100% de decisiones justificadas en matriz.<br/><b>R:</b> Evita retrabajo en implementación.", styles['TCell']), Paragraph("Sprint 2", styles['TCell'])],
        [Paragraph("<b>OE3</b>", styles['TCell']), Paragraph("Implementar los módulos funcionales del MVP.", styles['TCell']), Paragraph("<b>S:</b> Ingesta/nómina, motor IA, pool preguntas, flash test, panel, cierre.<br/><b>M:</b> 61 SP entregados en 4 Sprints.<br/><b>R:</b> Entrega funcional completa.", styles['TCell']), Paragraph("Sprint 3", styles['TCell'])],
        [Paragraph("<b>OE4</b>", styles['TCell']), Paragraph("Validar el funcionamiento del sistema y el control docente sobre el resultado.", styles['TCell']), Paragraph("<b>S:</b> Rendimiento (<=15s, <=100ms), precisión IA (>=75%), 100% notas confirmadas.<br/><b>M:</b> Métricas RNF cumplidas + AuditLog.<br/><b>R:</b> Confianza y cumplimiento ético/legal.", styles['TCell']), Paragraph("Sprint 4", styles['TCell'])],
    ]
    t_oe = Table(oe_rows, colWidths=[35, 175, 234, 60])
    t_oe.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg]),
        ('PADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_oe)
    story.append(Spacer(1, 6))

    # Matriz Trazabilidad
    story.append(Paragraph("<b>2.3 Matriz de Trazabilidad Problema vs. Objetivos:</b>", styles['SubSecTitle']))
    mat_rows = [
        [Paragraph("<b>Dimensión del Problema</b>", styles['THead']), Paragraph("<b>Objetivo(s)</b>", styles['THead']), Paragraph("<b>Entregable Concreto</b>", styles['THead'])],
        [Paragraph("Falsos positivos de detectores IA", styles['TCell']), Paragraph("OE2, OE3", styles['TCell']), Paragraph("Evaluación contextualizada con pauta y generación de preguntas personalizadas.", styles['TCell'])],
        [Paragraph("Imposibilidad logística de interrogar a todos", styles['TCell']), Paragraph("OE3", styles['TCell']), Paragraph("Panel de resultados que filtra estudiantes por puntaje para decidir a quién citar.", styles['TCell'])],
        [Paragraph("Fricción de adopción tecnológica", styles['TCell']), Paragraph("OE2, OE3", styles['TCell']), Paragraph("Acceso sin login con nómina CSV y enlaces tokenizados.", styles['TCell'])],
        [Paragraph("Evaluación sin contexto de la asignatura", styles['TCell']), Paragraph("OE2", styles['TCell']), Paragraph("Inyección de syllabus, guías y rúbricas en el prompt del LLM.", styles['TCell'])],
        [Paragraph("Pérdida de control del docente", styles['TCell']), Paragraph("OE3, OE4", styles['TCell']), Paragraph("Editor de preguntas y panel de cierre con confirmación explícita de nota.", styles['TCell'])],
        [Paragraph("Presupuesto cero para el MVP", styles['TCell']), Paragraph("OE2, OE3", styles['TCell']), Paragraph("Despacho con Gmail SMTP gratuito y arquitectura de costo cero.", styles['TCell'])],
        [Paragraph("Docente no puede probar uso indebido de IA", styles['TCell']), Paragraph("OE3, OE4", styles['TCell']), Paragraph("Desglose JSON y AuditLog inmutable.", styles['TCell'])],
        [Paragraph("Tiempo excesivo en corrección mecánica", styles['TCell']), Paragraph("OE3, OE4", styles['TCell']), Paragraph("Automatización del análisis preliminar, focalizando tiempo docente en defensas.", styles['TCell'])],
    ]
    t_mat = Table(mat_rows, colWidths=[150, 64, 290])
    t_mat.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg]),
        ('PADDING', (0,0), (-1,-1), 2.5),
    ]))
    story.append(t_mat)
    story.append(PageBreak())

    # SECCIÓN 3: REQUERIMIENTOS
    story.append(Paragraph("3. Análisis de Requerimientos y Fundamentación (45%)", styles['SecTitle']))
    story.append(Paragraph("<b>3.1 Bases Teóricas y Metodológicas:</b><br/>"
                           "• <i>Teoría de la Evaluación Auténtica (Grant Wiggins):</i> La asimilación del conocimiento se evidencia cuando el estudiante puede explicar y defender su trabajo. IntegriEval traslada el foco desde '¿el texto fue generado por IA?' a '¿el estudiante domina los conceptos?'.<br/>"
                           "• <i>Limitaciones Documentadas en Detectores de IA (Weber-Wulff et al., 2023):</i> Los clasificadores binarios presentan precisiones inferiores al 70%. IntegriEval usa IA como asistente de lectura y generador de preguntas supervisado por humanos.<br/>"
                           "• <i>Principio de supervisión humana:</i> En sistemas de IA educativos, el juicio humano debe ser el decisor final.", styles['Body']))
    
    story.append(Paragraph("<b>3.2 Requerimientos Funcionales (RF) & 3.3 No Funcionales (RNF):</b>", styles['SubSecTitle']))
    rf_rows = [
        [Paragraph("<b>ID</b>", styles['THead']), Paragraph("<b>Requisito / Categoría</b>", styles['THead']), Paragraph("<b>Métrica / Especificación</b>", styles['THead']), Paragraph("<b>Prio.</b>", styles['THead']), Paragraph("<b>Estado</b>", styles['THead'])],
        [Paragraph("RF-001", styles['TCell']), Paragraph("Crear y gestionar asignaturas", styles['TCell']), Paragraph("Nombre, periodo, año", styles['TCell']), Paragraph("Must", styles['TCell']), Paragraph("Bueno", styles['TCell'])],
        [Paragraph("RF-002", styles['TCell']), Paragraph("Ingesta de CSV de estudiantes", styles['TCell']), Paragraph("Validación de formato y duplicados", styles['TCell']), Paragraph("Must", styles['TCell']), Paragraph("Bueno", styles['TCell'])],
        [Paragraph("RF-003", styles['TCell']), Paragraph("Configurar parámetros de evaluación", styles['TCell']), Paragraph("Prompt, rigor, pool (10-30), umbrales", styles['TCell']), Paragraph("Must", styles['TCell']), Paragraph("Bueno", styles['TCell'])],
        [Paragraph("RF-004", styles['TCell']), Paragraph("Subir materiales de apoyo", styles['TCell']), Paragraph("PDF/DOCX a Markdown para contexto", styles['TCell']), Paragraph("Must", styles['TCell']), Paragraph("Bueno", styles['TCell'])],
        [Paragraph("RF-005", styles['TCell']), Paragraph("Carga masiva de PDFs de alumnos", styles['TCell']), Paragraph("Asociación automática por nombre archivo", styles['TCell']), Paragraph("Must", styles['TCell']), Paragraph("Bueno", styles['TCell'])],
        [Paragraph("RF-006", styles['TCell']), Paragraph("Extracción semántica de PDFs", styles['TCell']), Paragraph("pymupdf4llm preservando títulos y tablas", styles['TCell']), Paragraph("Must", styles['TCell']), Paragraph("Bueno", styles['TCell'])],
        [Paragraph("RF-007", styles['TCell']), Paragraph("Evaluación con Modelos LLM", styles['TCell']), Paragraph("Nota, feedback, % detección IA (Anexo A)", styles['TCell']), Paragraph("Must", styles['TCell']), Paragraph("Bueno", styles['TCell'])],
        [Paragraph("RF-008", styles['TCell']), Paragraph("Generación de pool de preguntas IA", styles['TCell']), Paragraph("X preguntas del informe + material", styles['TCell']), Paragraph("Must", styles['TCell']), Paragraph("Bueno", styles['TCell'])],
        [Paragraph("RF-009", styles['TCell']), Paragraph("Edición y selección docente de preguntas", styles['TCell']), Paragraph("Docente selecciona N preguntas (N <= Pool)", styles['TCell']), Paragraph("Must", styles['TCell']), Paragraph("Bueno", styles['TCell'])],
        [Paragraph("RF-010", styles['TCell']), Paragraph("Despacho de Flash Test por correo", styles['TCell']), Paragraph("Tokens UUIDv4 (vigencia 48h) vía Gmail SMTP", styles['TCell']), Paragraph("Must", styles['TCell']), Paragraph("Bueno", styles['TCell'])],
        [Paragraph("RF-011", styles['TCell']), Paragraph("Interfaz Flash Test en tiempo real", styles['TCell']), Paragraph("WebSockets con temporizador 60+s/test", styles['TCell']), Paragraph("Must", styles['TCell']), Paragraph("Bueno", styles['TCell'])],
        [Paragraph("RF-012", styles['TCell']), Paragraph("Panel de resultados para docente", styles['TCell']), Paragraph("Métricas clave para decisión de citación", styles['TCell']), Paragraph("Must", styles['TCell']), Paragraph("Bueno", styles['TCell'])],
        [Paragraph("RF-013", styles['TCell']), Paragraph("Registro de defensas y ajuste de nota", styles['TCell']), Paragraph("Acuerdos, nota final y AuditLog inmutable", styles['TCell']), Paragraph("Must", styles['TCell']), Paragraph("Bueno", styles['TCell'])],
        [Paragraph("RF-014", styles['TCell']), Paragraph("Mock Engine de contingencia", styles['TCell']), Paragraph("Fallback heurístico sin conexión a API", styles['TCell']), Paragraph("Should", styles['TCell']), Paragraph("Bueno", styles['TCell'])],
        [Paragraph("RF-015", styles['TCell']), Paragraph("Autenticación docente", styles['TCell']), Paragraph("Pendiente de formalización", styles['TCell']), Paragraph("Por def.", styles['TCell']), Paragraph("Incompleto", styles['TCell'])],
        [Paragraph("RNF-001", styles['TCell']), Paragraph("Rendimiento: Concurrencia WebSocket", styles['TCell']), Paragraph("100 conexiones con latencia <= 50ms", styles['TCell']), Paragraph("Must", styles['TCell']), Paragraph("Bueno", styles['TCell'])],
        [Paragraph("RNF-002", styles['TCell']), Paragraph("Rendimiento: Tiempo análisis informe", styles['TCell']), Paragraph("<= 15s (CPU) en 95% de casos", styles['TCell']), Paragraph("Must", styles['TCell']), Paragraph("Bueno", styles['TCell'])],
        [Paragraph("RNF-003", styles['TCell']), Paragraph("Rendimiento: API cierre calificaciones", styles['TCell']), Paragraph("<= 200ms", styles['TCell']), Paragraph("Should", styles['TCell']), Paragraph("Bueno", styles['TCell'])],
        [Paragraph("RNF-004", styles['TCell']), Paragraph("Seguridad: Tokens de acceso", styles['TCell']), Paragraph("UUIDv4 (RFC 4122)", styles['TCell']), Paragraph("Must", styles['TCell']), Paragraph("Bueno", styles['TCell'])],
        [Paragraph("RNF-005", styles['TCell']), Paragraph("Seguridad: Contraseñas docentes", styles['TCell']), Paragraph("bcrypt con factor >= 12", styles['TCell']), Paragraph("Must", styles['TCell']), Paragraph("Bueno", styles['TCell'])],
        [Paragraph("RNF-006", styles['TCell']), Paragraph("Seguridad: Control de accesos", styles['TCell']), Paragraph("RBAC por asignatura", styles['TCell']), Paragraph("Must", styles['TCell']), Paragraph("Bueno", styles['TCell'])],
        [Paragraph("RNF-007", styles['TCell']), Paragraph("Resiliencia: Fallback a Mock Engine", styles['TCell']), Paragraph("Timeout > 30s", styles['TCell']), Paragraph("Should", styles['TCell']), Paragraph("Bueno", styles['TCell'])],
        [Paragraph("RNF-008", styles['TCell']), Paragraph("Resiliencia: Reconexión WebSocket", styles['TCell']), Paragraph("<= 120s preservando estado", styles['TCell']), Paragraph("Should", styles['TCell']), Paragraph("Bueno", styles['TCell'])],
        [Paragraph("RNF-009", styles['TCell']), Paragraph("Usabilidad: Accesibilidad y Tema", styles['TCell']), Paragraph("WCAG 2.1 AA y tema oscuro", styles['TCell']), Paragraph("Could", styles['TCell']), Paragraph("Bueno", styles['TCell'])],
        [Paragraph("RNF-010", styles['TCell']), Paragraph("Costo: Licenciamiento", styles['TCell']), Paragraph("100% open-source, sin costos recurrentes", styles['TCell']), Paragraph("Must", styles['TCell']), Paragraph("Bueno", styles['TCell'])],
        [Paragraph("RNF-013", styles['TCell']), Paragraph("Privacidad: Ley N° 21.719 (Chile)", styles['TCell']), Paragraph("Cumplimiento antes de 01/12/2026", styles['TCell']), Paragraph("Must", styles['TCell']), Paragraph("Req. ajuste", styles['TCell'])],
    ]
    t_rf = Table(rf_rows, colWidths=[48, 140, 196, 50, 70])
    t_rf.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg]),
        ('PADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_rf)
    story.append(PageBreak())

    # SECCIÓN 3.4 a 3.7
    story.append(Paragraph("3.4 Reglas de Negocio, Integración y Datos", styles['SecTitle']))
    story.append(Paragraph("<b>Reglas de Negocio (RN):</b><br/>"
                           "• <b>RN-001 (Token):</b> UUIDv4 válido (48h). Permite acceso y se invalida tras primer uso.<br/>"
                           "• <b>RN-002 (Temporizador):</b> Si expira el tiempo de 60s/test, registra respuesta parcial y calcula sobre respondidas.<br/>"
                           "• <b>RN-003 (Indicadores):</b> Umbrales parametrizables en Asignatura.parametros; el sistema resalta alumnos en panel.<br/>"
                           "• <b>RN-004 (Nota Editable):</b> Nota editable por docente con campo de justificación obligatorio (defecto: 'Criterio del docente') y persistencia con auditoría.<br/>"
                           "• <i>Pendientes (RN-005 a RN-007):</i> Ausencia sin justificación, solicitud de reprogramación y reenvío por pérdida de enlace.", styles['Body']))
    
    story.append(Paragraph("<b>Requerimientos de Integración (RI):</b><br/>"
                           "• <b>RI-001 (LLM):</b> Open-source auto-hospedado (Llama 3.x / Qwen 2.5 vía Ollama / Claude) local sin costo API (REST HTTPS).<br/>"
                           "• <b>RI-002 (Gmail SMTP):</b> Protocolo SMTP TLS para despacho de correos.<br/>"
                           "• <b>RI-003 (LMS Blackboard):</b> API para sincronización de nóminas y notas (Pendiente / Incompleto).", styles['Body']))

    story.append(Paragraph("<b>Requerimientos de Datos (RD) — Entidades y Atributos:</b><br/>"
                           "• <b>Usuario:</b> id, nombre, correo (único), contraseña (bcrypt), rol, asignaturas.<br/>"
                           "• <b>Asignatura:</b> id, nombre, periodo, año, docente_id, parámetros (JSON).<br/>"
                           "• <b>Estudiante:</b> id, nombre, correo (único por asignatura), asignatura_id.<br/>"
                           "• <b>Trabajo:</b> id, estudiante_id, pdf_path, markdown, estado.<br/>"
                           "• <b>Material:</b> id, asignatura_id, nombre, tipo, markdown.<br/>"
                           "• <b>Evaluacion:</b> id, trabajo_id, nota (1-7), feedback (JSON), % IA (0-100), desglose.<br/>"
                           "• <b>Pregunta:</b> id, evaluacion_id, texto, alternativas (JSON), seleccionada.<br/>"
                           "• <b>FlashTest:</b> id, estudiante_id, token (único), vigencia (48h), respuestas (JSON), puntaje, estado.<br/>"
                           "• <b>Cita:</b> id, estudiante_id, docente_id, fecha, bloque, estado, creada_por.<br/>"
                           "• <b>AuditLog:</b> id, usuario_id, accion, tabla, registro_id, timestamp, datos_previos (JSON), datos_nuevos (JSON).", styles['Body']))

    story.append(Paragraph("<b>3.7 Evaluación Crítica de Alternativas Técnicas:</b><br/>"
                           "• <b>Validación Aprendizaje:</b> Detección + Preguntas Flash + Panel (Seleccionada) frente a solo detectores (descartada) o solo entrevista oral (inviable).<br/>"
                           "• <b>Acceso Alumno:</b> Token vía Email (Cero fricción, factor de posesión).<br/>"
                           "• <b>Integridad:</b> Flash Test Contextual (Reactivos basados en el propio texto).<br/>"
                           "• <b>Conversión PDF:</b> pymupdf4llm (Preserva estructura semántica en Markdown).<br/>"
                           "• <b>Servicio Email:</b> Gmail SMTP aiosmtplib (Costo cero para MVP).", styles['Body']))
    story.append(Spacer(1, 6))

    # SECCIÓN 4: PRODUCT BACKLOG
    story.append(Paragraph("4. Planificación del Proyecto y Product Backlog (20%)", styles['SecTitle']))
    
    bk_rows = [
        [Paragraph("<b>Épica</b>", styles['THead']), Paragraph("<b>Historias de Usuario</b>", styles['THead']), Paragraph("<b>Prioridad</b>", styles['THead']), Paragraph("<b>SP</b>", styles['THead']), Paragraph("<b>Sprint / Duración</b>", styles['THead'])],
        [Paragraph("<b>ÉPICA 1:</b> Gestión y Nómina (OE1)", styles['TCell']), Paragraph("US-01 (3 SP), US-02 (5 SP)", styles['TCell']), Paragraph("Must Have", styles['TCell']), Paragraph("8 SP", styles['TCell']), Paragraph("Sprint 1 (4.2 semanas con Épica 2)", styles['TCell'])],
        [Paragraph("<b>ÉPICA 2:</b> Ingesta y Conversión (OE1)", styles['TCell']), Paragraph("US-03 (8 SP), US-04 (5 SP)", styles['TCell']), Paragraph("Must Have", styles['TCell']), Paragraph("13 SP", styles['TCell']), Paragraph("Sprint 1 (Total: 21 SP)", styles['TCell'])],
        [Paragraph("<b>ÉPICA 3:</b> Motor de Evaluación (OE2)", styles['TCell']), Paragraph("US-05 (8 SP), US-06 (3 SP)", styles['TCell']), Paragraph("Must Have", styles['TCell']), Paragraph("11 SP", styles['TCell']), Paragraph("Sprint 2 (2.2 semanas)", styles['TCell'])],
        [Paragraph("<b>ÉPICA 4:</b> Pool de Preguntas (OE3)", styles['TCell']), Paragraph("US-07 (8 SP)", styles['TCell']), Paragraph("Must Have", styles['TCell']), Paragraph("8 SP", styles['TCell']), Paragraph("Sprint 3 (4.2 semanas con Épica 5)", styles['TCell'])],
        [Paragraph("<b>ÉPICA 5:</b> Despacho y Flash Test (OE3)", styles['TCell']), Paragraph("US-08 (5 SP), US-09 (8 SP)", styles['TCell']), Paragraph("Must Have", styles['TCell']), Paragraph("13 SP", styles['TCell']), Paragraph("Sprint 3 (Total: 21 SP)", styles['TCell'])],
        [Paragraph("<b>ÉPICA 6:</b> Resultados y Cierre (OE4)", styles['TCell']), Paragraph("US-10 (5 SP), US-11 (3 SP)", styles['TCell']), Paragraph("Must Have", styles['TCell']), Paragraph("8 SP", styles['TCell']), Paragraph("Sprint 4 (1.6 semanas)", styles['TCell'])],
        [Paragraph("<b>TOTAL GENERAL</b>", styles['THead']), Paragraph("<b>11 Historias Refinadas</b>", styles['THead']), Paragraph("<b>Must Have</b>", styles['THead']), Paragraph("<b>61 SP</b>", styles['THead']), Paragraph("<b>4 Sprints (≈ 12.2 semanas)</b>", styles['THead'])],
    ]
    t_bk = Table(bk_rows, colWidths=[115, 125, 64, 40, 160])
    t_bk.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('BACKGROUND', (0,-1), (-1,-1), c_secondary),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, c_bg]),
        ('PADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_bk)
    story.append(Spacer(1, 6))

    # SECCIÓN 4.4 Matriz Alineación
    story.append(Paragraph("<b>4.4 Matriz de Alineación Backlog-Objetivos:</b>", styles['SubSecTitle']))
    ali_rows = [
        [Paragraph("<b>Objetivo</b>", styles['THead']), Paragraph("<b>Historias Asociadas</b>", styles['THead']), Paragraph("<b>Tareas Técnicas Clave</b>", styles['THead']), Paragraph("<b>Criterios Aceptación</b>", styles['THead'])],
        [Paragraph("<b>OE1</b>", styles['TCell']), Paragraph("US-01, US-02, US-03, US-04", styles['TCell']), Paragraph("Modelos SQLAlchemy, endpoints CRUD, parser CSV, procesamiento asíncrono, pymupdf4llm.", styles['TCell']), Paragraph("CA-001, CA-002, CA-003, CA-004", styles['TCell'])],
        [Paragraph("<b>OE2</b>", styles['TCell']), Paragraph("US-05, US-06", styles['TCell']), Paragraph("API Anthropic, prompt design, procesamiento asíncrono, Mock Engine Heurístico.", styles['TCell']), Paragraph("CA-005, CA-006", styles['TCell'])],
        [Paragraph("<b>OE3</b>", styles['TCell']), Paragraph("US-07, US-08", styles['TCell']), Paragraph("Generación de preguntas, interfaz de edición, Gmail SMTP, tokens UUIDv4.", styles['TCell']), Paragraph("CA-007, CA-008", styles['TCell'])],
        [Paragraph("<b>OE4</b>", styles['TCell']), Paragraph("US-09, US-10, US-11", styles['TCell']), Paragraph("WebSockets, interfaz reactiva, temporizador 60s, panel resultados con filtros, panel cierre, confirmación/modificación de nota, AuditLog inmutable.", styles['TCell']), Paragraph("CA-009, CA-010, CA-011", styles['TCell'])],
    ]
    t_ali = Table(ali_rows, colWidths=[48, 120, 216, 120])
    t_ali.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg]),
        ('PADDING', (0,0), (-1,-1), 2.5),
    ]))
    story.append(t_ali)
    story.append(PageBreak())

    # SECCIÓN 5: ANEXO A JSON
    story.append(Paragraph("5. Anexo A: Estructura JSON de Evaluación (RF-007)", styles['SecTitle']))
    story.append(Paragraph("A continuación se presenta la estructura JSON estandarizada generada por el motor de análisis LLM para persistencia y visualización en el panel docente:", styles['Body']))
    
    json_sample = """{
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
    t_json = Table([[Paragraph(f"<pre>{json_sample.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')}</pre>", styles['JsonCode'])]], colWidths=[504])
    t_json.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#0F172A")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#334155")),
        ('PADDING', (0,0), (-1,-1), 8),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor("#E2E8F0")),
    ]))
    story.append(t_json)

    doc.build(story, canvasmaker=NumberedCanvas)
    print("Official Blueprint PDF build complete:", filename)

if __name__ == "__main__":
    os.makedirs("docs", exist_ok=True)
    build_pdf("docs/blueprint_integrieval.pdf")
    build_pdf("blueprint_integrieval.pdf")
