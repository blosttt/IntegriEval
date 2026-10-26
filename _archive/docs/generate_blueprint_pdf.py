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
            return  # Skip cover page
        
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#475569"))
        
        # Header
        self.drawString(54, 750, "IntegriEval — Blueprint Integral de Arquitectura y Servicio")
        self.drawRightString(558, 750, "Versión 1.0 (Septiembre 2026)")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 742, 558, 742)
        
        # Footer
        self.line(54, 45, 558, 45)
        self.setFont("Helvetica", 8)
        self.drawString(54, 32, "Trabajo de Título (INFO1197) — Ingeniería Civil Informática")
        page_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(558, 32, page_text)
        self.restoreState()


def build_pdf(filename="blueprint_integrieval.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=64,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    # Paleta de colores
    c_primary = colors.HexColor("#1E3A8A")     # Azul Marino Profundo
    c_secondary = colors.HexColor("#2563EB")   # Azul Royal
    c_indigo = colors.HexColor("#4338CA")      # Índigo
    c_text = colors.HexColor("#0F172A")        # Slate 900
    c_muted = colors.HexColor("#475569")       # Slate 600
    c_bg_box = colors.HexColor("#F8FAFC")      # Slate 50
    c_accent = colors.HexColor("#0D9488")      # Teal
    
    styles.add(ParagraphStyle('CoverTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=26, leading=32, textColor=c_primary, alignment=1))
    styles.add(ParagraphStyle('CoverSubtitle', parent=styles['Normal'], fontName='Helvetica', fontSize=12, leading=17, textColor=c_indigo, alignment=1))
    styles.add(ParagraphStyle('CoverMeta', parent=styles['Normal'], fontName='Helvetica', fontSize=9.5, leading=14, textColor=c_muted, alignment=1))
    
    styles.add(ParagraphStyle('SecHeading', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=13, leading=17, textColor=c_primary, spaceBefore=12, spaceAfter=5, keepWithNext=True))
    styles.add(ParagraphStyle('SubSecHeading', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10.5, leading=14, textColor=c_secondary, spaceBefore=8, spaceAfter=3, keepWithNext=True))
    
    styles.add(ParagraphStyle('DocBody', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=12, textColor=c_text, spaceAfter=4))
    styles.add(ParagraphStyle('DocBullet', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=12, textColor=c_text, leftIndent=10, spaceAfter=2.5))
    styles.add(ParagraphStyle('TableCell', parent=styles['Normal'], fontName='Helvetica', fontSize=7.5, leading=10, textColor=c_text))
    styles.add(ParagraphStyle('TableHeader', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7.5, leading=10, textColor=colors.white))
    styles.add(ParagraphStyle('BoxTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=12, textColor=c_indigo))
    styles.add(ParagraphStyle('BoxContent', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=11, textColor=c_text))
    styles.add(ParagraphStyle('CodeBlock', parent=styles['Normal'], fontName='Courier', fontSize=7.5, leading=10, textColor=c_text))

    story = []

    # ─────────────────────────────────────────────────────────────
    # PORTADA
    # ─────────────────────────────────────────────────────────────
    story.append(Spacer(1, 40))
    story.append(Paragraph("IntegriEval", styles['CoverTitle']))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Blueprint Integral de Arquitectura, Flujo de Servicio y Especificación Técnica", styles['CoverSubtitle']))
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="80%", thickness=2, color=c_secondary, spaceBefore=10, spaceAfter=20))
    
    box_meta = [
        [Paragraph("<b>Documento:</b> Blueprint Técnico y de Servicio (Service & Architectural Blueprint)", styles['TableCell'])],
        [Paragraph("<b>Asignatura / Proyecto:</b> Trabajo de Título (INFO1197) — Ingeniería Civil Informática", styles['TableCell'])],
        [Paragraph("<b>Autores:</b> Sebastian Cisternas, Benjamin Sobarzo", styles['TableCell'])],
        [Paragraph("<b>Versión:</b> 1.0 (Borrador para Validación)", styles['TableCell'])],
        [Paragraph("<b>Fecha:</b> Septiembre 2026", styles['TableCell'])],
        [Paragraph("<b>Repositorio:</b> https://github.com/blosttt/IntegriEval", styles['TableCell'])]
    ]
    t_box = Table(box_meta, colWidths=[400])
    t_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_bg_box),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
        ('PADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_box)
    story.append(Spacer(1, 140))
    
    story.append(Paragraph("<b>Facultad de Ingeniería y Ciencias de la Computación</b>", styles['CoverMeta']))
    story.append(Paragraph("Proyecto de Desarrollo de Software / Educación Superior", styles['CoverMeta']))
    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────────
    # SECCIÓN 1: SERVICE BLUEPRINT (MAPA DE SERVICIO)
    # ─────────────────────────────────────────────────────────────
    story.append(Paragraph("1. Blueprint de Servicio (Service Blueprint)", styles['SecHeading']))
    story.append(HRFlowable(width="100%", thickness=1, color=c_primary, spaceBefore=2, spaceAfter=6))
    
    story.append(Paragraph(
        "El Service Blueprint mapea de extremo a extremo la experiencia de los usuarios (docentes, ayudantes y estudiantes) interactuando con los módulos del sistema a través de cinco niveles operativos:",
        styles['DocBody']
    ))

    bp_data = [
        [Paragraph("<b>Nivel de Servicio</b>", styles['TableHeader']), Paragraph("<b>Paso 1: Ingesta Masiva</b>", styles['TableHeader']), Paragraph("<b>Paso 2: Evaluación IA</b>", styles['TableHeader']), Paragraph("<b>Paso 3: Aprobación Pool</b>", styles['TableHeader']), Paragraph("<b>Paso 4: Flash Test (Alumno)</b>", styles['TableHeader']), Paragraph("<b>Paso 5: Cierre y Defensa</b>", styles['TableHeader'])],
        [
            Paragraph("<b>Evidencia Física (Touchpoints)</b>", styles['TableCell']),
            Paragraph("Archivo CSV, lote de PDFs descargados del LMS, Syllabus.", styles['TableCell']),
            Paragraph("Pantalla con badges de estado (<i>processing</i> / <i>done</i>).", styles['TableCell']),
            Paragraph("Editor con 20 preguntas, alternativas editables, checkboxes.", styles['TableCell']),
            Paragraph("Email con token, pantalla web con temporizador de 60s.", styles['TableCell']),
            Paragraph("Pauta de cotejo, resumen de informe, panel de notas.", styles['TableCell'])
        ],
        [
            Paragraph("<b>Acciones Usuario (Frontstage)</b>", styles['TableCell']),
            Paragraph("Docente sube nómina CSV y arrastra lote de PDFs.", styles['TableCell']),
            Paragraph("Docente revisa notas preliminares y % de detección IA.", styles['TableCell']),
            Paragraph("Docente edita reactivos, selecciona 10 y despacha.", styles['TableCell']),
            Paragraph("Estudiante abre /flash/[token] y rinde test en tiempo real.", styles['TableCell']),
            Paragraph("Docente interroga a casos citados, registra acuerdos y cierra.", styles['TableCell'])
        ],
        [
            Paragraph("<b>Línea de Interacción (Frontend)</b>", styles['TableCell']),
            Paragraph("Componente Dropzone, tabla reactiva, feedback CSV.", styles['TableCell']),
            Paragraph("Tarjetas de rúbrica, fortalezas, debilidades y % IA.", styles['TableCell']),
            Paragraph("Editor interactivo con validación estricta (N=10).", styles['TableCell']),
            Paragraph("Conexión WebSocket con reloj de 60s y fallback de red.", styles['TableCell']),
            Paragraph("Vista de cierre con ajuste manual y confirmación explícita.", styles['TableCell'])
        ],
        [
            Paragraph("<b>Línea de Visibilidad (Backstage / API)</b>", styles['TableCell']),
            Paragraph("POST /api/students/upload-csv<br/>POST /api/reports/bulk-upload", styles['TableCell']),
            Paragraph("POST /api/reports/{id}/analyze<br/>Workers asíncronos.", styles['TableCell']),
            Paragraph("PUT /api/reports/{id}/questions<br/>POST /api/flash/send-token", styles['TableCell']),
            Paragraph("WebSocket /ws/flash/{token}<br/>Temporizador server-side.", styles['TableCell']),
            Paragraph("POST /api/appointments/close<br/>PUT /api/reports/{id}/grade", styles['TableCell'])
        ],
        [
            Paragraph("<b>Línea de Soporte & Persistencia</b>", styles['TableCell']),
            Paragraph("pymupdf4llm (PDF a MD). Tablas Student y Report.", styles['TableCell']),
            Paragraph("Prompt context con Claude 3.5 Sonnet / Mock Engine.", styles['TableCell']),
            Paragraph("Tokens UUIDv4 (48h). aiosmtplib (Gmail SMTP).", styles['TableCell']),
            Paragraph("Máquina de estados en memoria. Tabla FlashTest.", styles['TableCell']),
            Paragraph("AuditLog inmutable (usuario, fecha, datos previos/nuevos).", styles['TableCell'])
        ],
    ]
    t_bp = Table(bp_data, colWidths=[80, 84, 85, 85, 85, 85])
    t_bp.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg_box]),
        ('PADDING', (0,0), (-1,-1), 3),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t_bp)
    story.append(Spacer(1, 10))

    # ─────────────────────────────────────────────────────────────
    # SECCIÓN 2: BLUEPRINT DE ARQUITECTURA TÉCNICA
    # ─────────────────────────────────────────────────────────────
    story.append(Paragraph("2. Blueprint de Arquitectura Técnica (C4 - Nivel Contenedores)", styles['SecHeading']))
    story.append(HRFlowable(width="100%", thickness=1, color=c_primary, spaceBefore=2, spaceAfter=6))
    
    arch_cards = [
        ("Capa de Presentación (Frontend SPA Next.js 14)",
         "<b>• Panel Docente:</b> Interfaz reactiva en Tailwind CSS para gestión de asignaturas, nóminas CSV, subida de PDFs y revisión de rúbricas.<br/><b>• Interfaz Flash Test:</b> Módulo público (/flash/[token]) sin inicio de sesión, con comunicación en tiempo real mediante WebSockets y reloj estricto."),
        ("Capa de Aplicación y API (FastAPI / Python 3.14)",
         "<b>• Endpoints RESTful y WebSocket:</b> Módulos modulares para Auth, Students, Materials, Reports, Flash y Appointments.<br/><b>• Workers Asíncronos:</b> Encolamiento en segundo plano de tareas pesadas (extracción semántica y llamadas LLM) para garantizar latencia < 200ms."),
        ("Capa de IA y Procesamiento Documental",
         "<b>• pymupdf4llm:</b> Conversión de PDFs a Markdown preservando encabezados, tablas y listas (reducción del 40% de ruido léxico).<br/><b>• Motor de Inferencia:</b> Integración con Claude 3.5 Sonnet / Ollama (Llama 3/Qwen) y motor Mock Engine heurístico de contingencia."),
        ("Capa de Integración y Persistencia",
         "<b>• Gmail SMTP (aiosmtplib):</b> Despacho asíncrono gratuito de invitaciones con tokens UUIDv4.<br/><b>• Base de Datos & AuditLog:</b> SQLite / PostgreSQL administrado vía SQLAlchemy 2.0 con tablas inmutables de auditoría.")
    ]
    for title, content in arch_cards:
        t_c = Table([[Paragraph(f"<b>{title}</b>", styles['BoxTitle'])], [Paragraph(content, styles['BoxContent'])]], colWidths=[504])
        t_c.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), c_bg_box),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#94A3B8")),
            ('PADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,0), 2),
        ]))
        story.append(t_c)
        story.append(Spacer(1, 4))

    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────────
    # SECCIÓN 3: BLUEPRINT DEL MODELO DE DATOS
    # ─────────────────────────────────────────────────────────────
    story.append(Paragraph("3. Blueprint del Modelo de Datos (Esquema Entidad-Relación)", styles['SecHeading']))
    story.append(HRFlowable(width="100%", thickness=1, color=c_primary, spaceBefore=2, spaceAfter=6))
    
    erd_data = [
        [Paragraph("<b>Entidad</b>", styles['TableHeader']), Paragraph("<b>Atributos Clave</b>", styles['TableHeader']), Paragraph("<b>Relaciones y Cardinalidad</b>", styles['TableHeader']), Paragraph("<b>Propósito / Rol en el Sistema</b>", styles['TableHeader'])],
        [
            Paragraph("<b>Usuario</b>", styles['TableCell']),
            Paragraph("id, nombre, correo (UK), password_hash, rol", styles['TableCell']),
            Paragraph("1 a N con Asignatura y Cita", styles['TableCell']),
            Paragraph("Cuentas de docentes y administradores protegidas con bcrypt.", styles['TableCell'])
        ],
        [
            Paragraph("<b>Asignatura</b>", styles['TableCell']),
            Paragraph("id, nombre, periodo, anio, docente_id, parametros (JSON)", styles['TableCell']),
            Paragraph("1 a N con Estudiante y Material", styles['TableCell']),
            Paragraph("Cursos administrados con configuración de rúbrica y rigor.", styles['TableCell'])
        ],
        [
            Paragraph("<b>Estudiante</b>", styles['TableCell']),
            Paragraph("id, nombre, correo, asignatura_id", styles['TableCell']),
            Paragraph("1 a N con Trabajo, FlashTest, Cita", styles['TableCell']),
            Paragraph("Alumnos cargados por CSV sin login ni contraseña.", styles['TableCell'])
        ],
        [
            Paragraph("<b>Trabajo / Report</b>", styles['TableCell']),
            Paragraph("id, estudiante_id, pdf_path, markdown, estado", styles['TableCell']),
            Paragraph("1 a 1 con Evaluacion", styles['TableCell']),
            Paragraph("Documento entregado y convertido a Markdown.", styles['TableCell'])
        ],
        [
            Paragraph("<b>Material</b>", styles['TableCell']),
            Paragraph("id, asignatura_id, nombre, tipo, markdown", styles['TableCell']),
            Paragraph("N a 1 con Asignatura", styles['TableCell']),
            Paragraph("Syllabus y guías inyectadas como contexto al LLM.", styles['TableCell'])
        ],
        [
            Paragraph("<b>Evaluacion</b>", styles['TableCell']),
            Paragraph("id, trabajo_id, nota_preliminar, % IA, feedback (JSON), desglose", styles['TableCell']),
            Paragraph("1 a N con Pregunta", styles['TableCell']),
            Paragraph("Resultado del análisis contextualizado generado por la IA.", styles['TableCell'])
        ],
        [
            Paragraph("<b>Pregunta</b>", styles['TableCell']),
            Paragraph("id, evaluacion_id, texto, alternativas (JSON), correcta, seleccionada", styles['TableCell']),
            Paragraph("N a 1 con Evaluacion", styles['TableCell']),
            Paragraph("Pool de 20 reactivos editables (selección final de 10).", styles['TableCell'])
        ],
        [
            Paragraph("<b>FlashTest</b>", styles['TableCell']),
            Paragraph("id, estudiante_id, token (UK), vigencia (48h), respuestas, puntaje, estado", styles['TableCell']),
            Paragraph("N a 1 con Estudiante", styles['TableCell']),
            Paragraph("Sesión de examen en tiempo real gobernada por WebSocket.", styles['TableCell'])
        ],
        [
            Paragraph("<b>Cita</b>", styles['TableCell']),
            Paragraph("id, estudiante_id, docente_id, fecha, bloque, estado, motivo", styles['TableCell']),
            Paragraph("N a 1 con Estudiante/Docente", styles['TableCell']),
            Paragraph("Defensa presencial agendada para casos críticos.", styles['TableCell'])
        ],
        [
            Paragraph("<b>AuditLog</b>", styles['TableCell']),
            Paragraph("id, usuario_id, accion, tabla, registro_id, timestamp, datos_previos, datos_nuevos", styles['TableCell']),
            Paragraph("N a 1 con Usuario", styles['TableCell']),
            Paragraph("Registro inmutable de trazabilidad de cambios de notas.", styles['TableCell'])
        ],
    ]
    t_erd = Table(erd_data, colWidths=[70, 150, 110, 174])
    t_erd.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg_box]),
        ('PADDING', (0,0), (-1,-1), 3),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t_erd)
    story.append(Spacer(1, 8))

    # ─────────────────────────────────────────────────────────────
    # SECCIÓN 4: BLUEPRINT DE ESTADOS (MÁQUINA DE ESTADOS)
    # ─────────────────────────────────────────────────────────────
    story.append(Paragraph("4. Blueprint de Estados del Flujo de Trabajo (State Machine)", styles['SecHeading']))
    story.append(HRFlowable(width="100%", thickness=1, color=c_primary, spaceBefore=2, spaceAfter=6))
    
    story.append(Paragraph(
        "El ciclo de vida de un informe y de la verificación del estudiante sigue una máquina de estados determinista:",
        styles['DocBody']
    ))
    
    st_steps = [
        ("1. Ingesta Masiva:", "El docente carga el lote de PDFs. El sistema almacena los archivos y asigna estado <code>Subido</code>."),
        ("2. Conversión a Markdown:", "<code>pymupdf4llm</code> extrae la estructura semántica y el informe pasa a <code>ConvertidoMarkdown</code>."),
        ("3. Evaluación IA:", "Worker asíncrono ejecuta la inferencia con Claude 3.5 Sonnet / Mock (<code>EnAnalisisIA</code> &rarr; <code>Analizado</code>)."),
        ("4. Pool de Reactivos:", "Se generan 20 preguntas (<code>PoolGenerado</code>); el docente revisa, edita y aprueba 10 (<code>PoolAprobado</code>)."),
        ("5. Despacho & Examen:", "Se envía token UUIDv4 por correo (<code>Despachado</code>). El alumno rinde el test en vivo (<code>EnExamen</code> &rarr; <code>ExamenFinalizado</code>)."),
        ("6. Ruteo & Cierre:", "Si score &lt; 50%, &ge; 95% o 10% aleatorio &rarr; <code>ConvocadoDefensa</code>. Tras entrevista presencial o validación directa &rarr; <code>NotaConfirmada</code>.")
    ]
    for st_title, st_desc in st_steps:
        story.append(Paragraph(f"<b>{st_title}</b> {st_desc}", styles['DocBullet']))

    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────────
    # SECCIÓN 5: MATRIZ DE COMPONENTES VS SPRINTS
    # ─────────────────────────────────────────────────────────────
    story.append(Paragraph("5. Matriz de Componentes vs. Requerimientos vs. Sprints (61 SP)", styles['SecHeading']))
    story.append(HRFlowable(width="100%", thickness=1, color=c_primary, spaceBefore=2, spaceAfter=6))
    
    sp_data = [
        [Paragraph("<b>Sprint / Fase</b>", styles['TableHeader']), Paragraph("<b>Módulo del Blueprint</b>", styles['TableHeader']), Paragraph("<b>Requerimientos</b>", styles['TableHeader']), Paragraph("<b>Esfuerzo</b>", styles['TableHeader']), Paragraph("<b>Criterios de Aceptación Técnicos</b>", styles['TableHeader'])],
        [
            Paragraph("<b>Sprint 1</b><br/>(Ingesta)", styles['TableCell']),
            Paragraph("Gestión de Cursos, Nómina CSV & Extracción", styles['TableCell']),
            Paragraph("RF-001, RF-002,<br/>RF-004, RF-005,<br/>RF-006", styles['TableCell']),
            Paragraph("<b>21 SP</b><br/>(4.2 sem)", styles['TableCell']),
            Paragraph("Carga CSV &ge; 200 estudiantes, subida masiva de 100 PDFs, extracción Markdown con tasa de éxito &ge; 98%.", styles['TableCell'])
        ],
        [
            Paragraph("<b>Sprint 2</b><br/>(Análisis)", styles['TableCell']),
            Paragraph("Motor de Análisis Contextualizado e IA", styles['TableCell']),
            Paragraph("RF-003, RF-007,<br/>RF-014", styles['TableCell']),
            Paragraph("<b>11 SP</b><br/>(2.2 sem)", styles['TableCell']),
            Paragraph("Procesamiento &le; 15s por informe, inyección de syllabus en prompt, fallback automático a MockEngine ante fallos.", styles['TableCell'])
        ],
        [
            Paragraph("<b>Sprint 3</b><br/>(Reactivos)", styles['TableCell']),
            Paragraph("Pool de Preguntas, Despacho & Flash Test", styles['TableCell']),
            Paragraph("RF-008, RF-009,<br/>RF-010, RF-011", styles['TableCell']),
            Paragraph("<b>21 SP</b><br/>(4.2 sem)", styles['TableCell']),
            Paragraph("Editor de 20 preguntas (selección estricta de 10), despacho SMTP Gmail gratuito, WebSocket con latencia &le; 100ms.", styles['TableCell'])
        ],
        [
            Paragraph("<b>Sprint 4</b><br/>(Cierre)", styles['TableCell']),
            Paragraph("Ruteo Automático, Agenda & Auditoría", styles['TableCell']),
            Paragraph("RF-012, RF-013,<br/>RF-015", styles['TableCell']),
            Paragraph("<b>8 SP</b><br/>(1.6 sem)", styles['TableCell']),
            Paragraph("Ruteo automático de casos críticos (&lt;50%, &ge;95%, 10% aleatorio), panel de cierre con confirmación y AuditLog inmutable.", styles['TableCell'])
        ],
        [
            Paragraph("<b>TOTAL</b>", styles['TableHeader']),
            Paragraph("<b>Arquitectura Completa IntegriEval</b>", styles['TableHeader']),
            Paragraph("<b>15 RFs + 13 RNFs</b>", styles['TableHeader']),
            Paragraph("<b>61 SP</b>", styles['TableHeader']),
            Paragraph("<b>≈ 12.2 semanas de desarrollo e integración</b>", styles['TableHeader'])
        ]
    ]
    t_sp = Table(sp_data, colWidths=[70, 115, 85, 60, 174])
    t_sp.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('BACKGROUND', (0,-1), (-1,-1), c_secondary),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, c_bg_box]),
        ('PADDING', (0,0), (-1,-1), 3.5),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t_sp)
    story.append(Spacer(1, 10))

    # ─────────────────────────────────────────────────────────────
    # SECCIÓN 6: SEGURIDAD, RENDIMIENTO Y LEY 21.719
    # ─────────────────────────────────────────────────────────────
    story.append(Paragraph("6. Aspectos Clave de Seguridad, Rendimiento y Marco Legal", styles['SecHeading']))
    story.append(HRFlowable(width="100%", thickness=1, color=c_primary, spaceBefore=2, spaceAfter=6))
    
    sec_points = [
        ("Estrategia Sin Cuentas para Estudiantes:", "La autenticación se basa en el principio de <i>Posesión de Correo Institucional</i>. El token UUIDv4 posee entropía criptográfica (128 bits), caduca a las 48h y se invalida inmediatamente tras el primer uso."),
        ("Resiliencia y Concurrencia:", "Arquitectura WebSocket sobre Starlette capaz de sostener 100 conexiones simultáneas con latencia &le; 50ms. Soporta reconexión tolerante a fallos conservando el cronómetro activo de la pregunta (timeout &le; 120s)."),
        ("Cumplimiento Ley N° 21.719 (Protección de Datos Personales de Chile):", "Principio de proporcionalidad: solo se almacena nombre, correo institucional y el trabajo entregado. El <code>AuditLog</code> inmutable registra toda modificación docente de notas como respaldo ético y legal.")
    ]
    for title, desc in sec_points:
        story.append(Paragraph(f"<b>• {title}</b> {desc}", styles['DocBody']))

    doc.build(story, canvasmaker=NumberedCanvas)
    print("Blueprint PDF build complete:", filename)

if __name__ == "__main__":
    build_pdf()
