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
        self.drawString(54, 750, "IntegriEval — Especificación Formal de Ingeniería de Software")
        self.drawRightString(558, 750, "Versión 2.0.0 (Agosto 2026)")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 742, 558, 742)
        
        # Footer
        self.line(54, 45, 558, 45)
        self.setFont("Helvetica", 8)
        self.drawString(54, 32, "Confidencial / Uso Académico — IntegriEval System")
        page_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(558, 32, page_text)
        self.restoreState()


def build_pdf(filename="documento_ingenieria_integrieval.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=64,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    c_primary = colors.HexColor("#1E3A8A")     # Dark Blue
    c_secondary = colors.HexColor("#4338CA")   # Indigo
    c_text = colors.HexColor("#0F172A")        # Slate 900
    c_muted = colors.HexColor("#475569")       # Slate 600
    
    styles.add(ParagraphStyle('CoverTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=26, leading=32, textColor=c_primary, alignment=1))
    styles.add(ParagraphStyle('CoverSubtitle', parent=styles['Normal'], fontName='Helvetica', fontSize=13, leading=18, textColor=c_secondary, alignment=1))
    styles.add(ParagraphStyle('CoverMeta', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=14, textColor=c_muted, alignment=1))
    
    styles.add(ParagraphStyle('SecHeading', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=15, leading=19, textColor=c_primary, spaceBefore=14, spaceAfter=6, keepWithNext=True))
    styles.add(ParagraphStyle('SubSecHeading', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, leading=15, textColor=c_secondary, spaceBefore=10, spaceAfter=4, keepWithNext=True))
    styles.add(ParagraphStyle('SubSubSecHeading', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, leading=13, textColor=c_text, spaceBefore=8, spaceAfter=3, keepWithNext=True))
    
    styles.add(ParagraphStyle('DocBody', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=13, textColor=c_text, spaceAfter=5))
    styles.add(ParagraphStyle('DocBullet', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=13, textColor=c_text, leftIndent=12, spaceAfter=3))
    styles.add(ParagraphStyle('TableCell', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=11, textColor=c_text))
    styles.add(ParagraphStyle('TableHeader', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=11, textColor=colors.white))
    styles.add(ParagraphStyle('BoxTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, leading=13, textColor=c_secondary))
    styles.add(ParagraphStyle('BoxContent', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=12, textColor=c_text))

    story = []

    # ─────────────────────────────────────────────────────────────
    # PORTADA
    # ─────────────────────────────────────────────────────────────
    story.append(Spacer(1, 40))
    story.append(Paragraph("IntegriEval", styles['CoverTitle']))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Sistema Semi-Automatizado de Evaluación de Integridad Académica, Detección de IA y Verificación Oral Flash", styles['CoverSubtitle']))
    story.append(Spacer(1, 24))
    story.append(HRFlowable(width="80%", thickness=2, color=c_secondary, spaceBefore=10, spaceAfter=20))
    
    box_meta = [
        [Paragraph("<b>Proyecto:</b> Sistema de Verificación Académica Híbrida", styles['TableCell'])],
        [Paragraph("<b>Área:</b> Inteligencia Artificial aplicada a la Educación Superior / EdTech", styles['TableCell'])],
        [Paragraph("<b>Versión:</b> 2.0.0 (Release para Producción)", styles['TableCell'])],
        [Paragraph("<b>Fecha:</b> Agosto 2026", styles['TableCell'])],
        [Paragraph("<b>Repositorio:</b> https://github.com/blosttt/IntegriEval", styles['TableCell'])]
    ]
    t_box = Table(box_meta, colWidths=[400])
    t_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
        ('PADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_box)
    story.append(Spacer(1, 140))
    
    story.append(Paragraph("<b>Autoría:</b> Equipo de Desarrollo Estudiantil IntegriEval", styles['CoverMeta']))
    story.append(Paragraph("Facultad de Ingeniería y Ciencias de la Computación", styles['CoverMeta']))
    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────────
    # SECCIÓN 1: DEFINICIÓN DEL PROBLEMA (10%)
    # ─────────────────────────────────────────────────────────────
    story.append(Paragraph("1. Definición Clara del Problema (10%)", styles['SecHeading']))
    story.append(HRFlowable(width="100%", thickness=1, color=c_primary, spaceBefore=2, spaceAfter=8))
    
    story.append(Paragraph("<b>1.1 Contexto y Situación Actual</b>", styles['SubSecHeading']))
    story.append(Paragraph(
        "La masificación de los Modelos de Lenguaje Grande (LLMs) como GPT-4, Claude y Gemini ha impactado profundamente la evaluación académica universitaria. Actualmente, los estudiantes entregan sus informes y trabajos a través del LMS institucional (Moodle, Canvas, Blackboard). Los docentes y ayudantes descargan decenas de archivos PDF y DOCX enfrentando el desafío de certificar si el contenido refleja un aprendizaje auténtico o fue generado de forma no atribuida por herramientas de IA.",
        styles['DocBody']
    ))

    story.append(Paragraph("<b>1.2 Articulación del Problema Central</b>", styles['SubSecHeading']))
    story.append(Paragraph("<b>1. Ineficacia de los Detectores Estadísticos de 'Caja Negra':</b> Herramientas como Turnitin AI Detector o GPTZero basan su análisis en perplejidad y ráfagas léxicas. La evidencia científica demuestra tasas elevadas de falsos positivos (perjudicando a alumnos no nativos o textos formales rigurosos) y falsos negativos (eludibles mediante parafraseo o prompt engineering). Acusar disciplinariamente a un alumno por un porcentaje opaco acarrea graves dilemas éticos y jurídicos.", styles['DocBullet']))
    story.append(Paragraph("<b>2. Inviabilidad Logística de la Interrogación Universal:</b> La defensa oral presencial es el método infalible para verificar autoría; sin embargo, examinar oralmente al 100% de los estudiantes en cursos masivos (60 a 200 alumnos) es físicamente imposible por la restricción de horas de atención docente.", styles['DocBullet']))
    story.append(Paragraph("<b>3. Sobrecarga en la Corrección Manual:</b> Los docentes invierten hasta 25 horas semanales corrigiendo mecánicamente trabajos contra la pauta y la bibliografía del curso.", styles['DocBullet']))

    story.append(Paragraph("<b>1.3 Validación con Partes Interesadas (Stakeholders)</b>", styles['SubSecHeading']))
    
    stk_data = [
        [Paragraph("<b>Stakeholder</b>", styles['TableHeader']), Paragraph("<b>Percepción y Dolores Identificados</b>", styles['TableHeader']), Paragraph("<b>Expectativa y Validación de Relevancia</b>", styles['TableHeader'])],
        [
            Paragraph("<b>Profesores Titulares</b>", styles['TableCell']),
            Paragraph("<i>'No sé si el alumno aprendió o si apretó un botón en ChatGPT. No tengo tiempo de interrogar a 100 alumnos ni puedo acusar sin pruebas tangibles.'</i>", styles['TableCell']),
            Paragraph("Requieren una nota preliminar justificada, un pool de preguntas adaptado al informe y agendamiento de citas solo para casos anómalos o aleatorios.", styles['TableCell'])
        ],
        [
            Paragraph("<b>Ayudantes / TAs</b>", styles['TableCell']),
            Paragraph("<i>'Revisar 80 PDFs idénticos es agotador y dilata semanas la entrega de notas.'</i>", styles['TableCell']),
            Paragraph("Desean subida masiva en lote y extracción de resúmenes ejecutivos estructurados en Markdown.", styles['TableCell'])
        ],
        [
            Paragraph("<b>Estudiantes</b>", styles['TableCell']),
            Paragraph("<i>'Es frustrante que un detector te acuse injustamente. Si hay dudas, prefiero que me pregunten sobre mi informe para demostrar que lo domino.'</i>", styles['TableCell']),
            Paragraph("Exigen un proceso transparente, sin crear cuentas adicionales, y con derecho a defensa oral.", styles['TableCell'])
        ],
        [
            Paragraph("<b>Dirección de Carrera</b>", styles['TableCell']),
            Paragraph("<i>'Debemos resguardar el prestigio de los egresados y evitar litigios por acusaciones infundadas.'</i>", styles['TableCell']),
            Paragraph("Validan la necesidad de pistas de auditoría inmutables y defensas orales fundamentadas en evidencia tangible.", styles['TableCell'])
        ],
    ]
    t_stk = Table(stk_data, colWidths=[90, 200, 214])
    t_stk.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_stk)
    story.append(Spacer(1, 14))

    # ─────────────────────────────────────────────────────────────
    # SECCIÓN 2: OBJETIVOS SMART Y MATRIZ (25%)
    # ─────────────────────────────────────────────────────────────
    story.append(Paragraph("2. Objetivos Específicos y Matriz de Trazabilidad (25%)", styles['SecHeading']))
    story.append(HRFlowable(width="100%", thickness=1, color=c_primary, spaceBefore=2, spaceAfter=8))
    
    story.append(Paragraph("<b>2.1 Objetivo General</b>", styles['SubSecHeading']))
    story.append(Paragraph(
        "Desarrollar e implementar <b>IntegriEval</b>, una plataforma web para la evaluación semi-automatizada de trabajos académicos que integre conversión de documentos a Markdown, análisis de pauta asistido por IA contextualizada con material de curso, generación de bancos de preguntas flash editables y un sistema de verificación oral focalizado con agendamiento automático según la disponibilidad del docente.",
        styles['DocBody']
    ))

    story.append(Paragraph("<b>2.2 Objetivos Específicos SMART</b>", styles['SubSecHeading']))
    
    oe_cards = [
        ("OE1: Módulo de Ingesta, Nómina y Conversión Estructurada",
         "<b>Específico:</b> Carga de estudiantes (CSV) y subida masiva de trabajos (PDF/DOCX) con conversión a Markdown.<br/><b>Medible:</b> Tasa de éxito >= 98% en documentos estándar y soporte para lotes de hasta 100 archivos.<br/><b>Alcanzable:</b> pymupdf4llm y FastAPI.<br/><b>Relevante:</b> Cero cuentas para alumnos y formato óptimo para LLM.<br/><b>Temporizado:</b> Fase 1."),
        ("OE2: Motor de Análisis de Rúbrica y Detección Contextual",
         "<b>Específico:</b> Evaluación asistida que contraste el informe contra pauta y materiales del curso.<br/><b>Medible:</b> Tiempo de respuesta <= 15s por informe en modo asíncrono con desglose porcentual.<br/><b>Alcanzable:</b> Workers en background, Claude 3.5 Sonnet y fallback Mock.<br/><b>Relevante:</b> Justificación cualitativa sin arbitrariedad.<br/><b>Temporizado:</b> Fase 2."),
        ("OE3: Generación, Edición y Despacho del Pool de Preguntas",
         "<b>Específico:</b> Pool dinámico (20-30 reactivos por informe) parametrizado por rigor, editable por el profesor.<br/><b>Medible:</b> 100% asociadas al contenido del alumno; despacho asíncrono con token de un solo uso (48h).<br/><b>Alcanzable:</b> aiosmtplib (Gmail SMTP gratuito) y UUIDv4.<br/><b>Relevante:</b> Control pedagógico docente.<br/><b>Temporizado:</b> Fase 3."),
        ("OE4: Plataforma de Flash Test en Tiempo Real y Ruteo",
         "<b>Específico:</b> Examen en tiempo real vía WebSocket y algoritmo de ruteo a citas presenciales.<br/><b>Medible:</b> Latencia <= 100ms, temporizador estricto y agendamiento automático del 100% de casos atípicos.<br/><b>Alcanzable:</b> WebSockets sobre FastAPI y Next.js App Router.<br/><b>Relevante:</b> Focaliza horas presenciales solo en defensas justificadas.<br/><b>Temporizado:</b> Fase 4.")
    ]

    for title, content in oe_cards:
        t_oe = Table([[Paragraph(f"<b>{title}</b>", styles['BoxTitle'])], [Paragraph(content, styles['BoxContent'])]], colWidths=[504])
        t_oe.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F1F5F9")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#94A3B8")),
            ('PADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,0), 2),
        ]))
        story.append(t_oe)
        story.append(Spacer(1, 6))

    story.append(Paragraph("<b>2.3 Matriz de Trazabilidad (Problema vs. Objetivos)</b>", styles['SubSecHeading']))
    mat_data = [
        [Paragraph("<b>Aspecto del Problema</b>", styles['TableHeader']), Paragraph("<b>Causa Raíz</b>", styles['TableHeader']), Paragraph("<b>Obj.</b>", styles['TableHeader']), Paragraph("<b>Entregable Concreto</b>", styles['TableHeader'])],
        [Paragraph("Falsos positivos de detectores IA", styles['TableCell']), Paragraph("Dependencia de perplejidad sin validar comprensión humana.", styles['TableCell']), Paragraph("<b>OE2, OE3</b>", styles['TableCell']), Paragraph("Evaluación con material de curso y preguntas exclusivas del informe.", styles['TableCell'])],
        [Paragraph("Imposibilidad de interrogar a todos", styles['TableCell']), Paragraph("Restricción horaria del docente en cursos masivos.", styles['TableCell']), Paragraph("<b>OE4</b>", styles['TableCell']), Paragraph("Ruteo automático: solo defienden con score < 50%, >= 95% o 10% aleatorio.", styles['TableCell'])],
        [Paragraph("Fricción de adopción tecnológica", styles['TableCell']), Paragraph("Alumnos se resisten a crear cuentas para un solo test.", styles['TableCell']), Paragraph("<b>OE1, OE3</b>", styles['TableCell']), Paragraph("Acceso sin login: nómina por CSV y enlace con token seguro por correo.", styles['TableCell'])],
        [Paragraph("Evaluación no interdisciplinaria", styles['TableCell']), Paragraph("La IA evalúa aislada sin conocer la materia del curso.", styles['TableCell']), Paragraph("<b>OE2</b>", styles['TableCell']), Paragraph("Módulo de Materiales de Apoyo inyectados en el contexto del LLM.", styles['TableCell'])],
        [Paragraph("Pérdida de control del docente", styles['TableCell']), Paragraph("Sistemas 100% automáticos sin intervención humana.", styles['TableCell']), Paragraph("<b>OE3, OE4</b>", styles['TableCell']), Paragraph("Editor interactivo de preguntas y registro presencial con ajuste de nota.", styles['TableCell'])],
        [Paragraph("Presupuesto cero en MVPs", styles['TableCell']), Paragraph("Costos elevados de APIs transaccionales y servidores.", styles['TableCell']), Paragraph("<b>OE3</b>", styles['TableCell']), Paragraph("Despacho con Gmail SMTP gratuito (aiosmtplib) y SQLite local.", styles['TableCell'])],
    ]
    t_mat = Table(mat_data, colWidths=[120, 140, 44, 200])
    t_mat.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_mat)
    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────────
    # SECCIÓN 3: ANÁLISIS DE REQUERIMIENTOS (45%)
    # ─────────────────────────────────────────────────────────────
    story.append(Paragraph("3. Análisis de Requerimientos y Fundamentación (45%)", styles['SecHeading']))
    story.append(HRFlowable(width="100%", thickness=1, color=c_primary, spaceBefore=2, spaceAfter=8))
    
    story.append(Paragraph("<b>3.1 Fundamentación Teórica y Estado del Arte</b>", styles['SubSecHeading']))
    story.append(Paragraph(
        "<b>• Teoría de la Evaluación Auténtica (Grant Wiggins):</b> Establece que la asimilación del conocimiento se evidencia cuando el estudiante puede explicar, defender y aplicar sus decisiones metodológicas frente a preguntas directas. IntegriEval traslada el foco desde <i>'¿el texto fue generado por una máquina?'</i> hacia <i>'¿el estudiante domina los conceptos plasmados en su entrega?'</i>.",
        styles['DocBody']
    ))
    story.append(Paragraph(
        "<b>• Limitaciones Documentadas en Detectores de IA (Weber-Wulff et al., 2023):</b> Los clasificadores binarios presentan precisiones inferiores al 70% en entornos universitarios. IntegriEval emplea la IA como asistente de lectura y generador de reactivos supervisado por humanos (<i>Human-in-the-Loop</i>).",
        styles['DocBody']
    ))

    story.append(Paragraph("<b>3.2 Requerimientos Funcionales (RF)</b>", styles['SubSecHeading']))
    rfs = [
        ("RF01 - Gestión de Asignaturas:", "Creación y administración de cursos indicando nombre y periodo."),
        ("RF02 - Nómina Masiva (CSV):", "Ingesta de CSV (Nombre, Correo) sin requerir contraseñas."),
        ("RF03 - Configuración de Parámetros:", "Pauta/prompt libre, rigor (strict/medium/lax), tamaño de pool y umbrales."),
        ("RF04 - Materiales de Apoyo:", "Carga de syllabus y guías en PDF/DOCX convertidos a Markdown para contexto."),
        ("RF05 - Subida Masiva de Trabajos:", "Carga en lote de PDFs con auto-asociación heurística o manual por estudiante."),
        ("RF06 - Conversión Estructurada:", "Extracción de alta fidelidad con pymupdf4llm preservando títulos y tablas."),
        ("RF07 - Evaluación Asíncrona IA:", "Nota preliminar, feedback cualitativo y porcentaje de detección de IA."),
        ("RF08 - Pool de Preguntas Flash:", "Edición de alternativas, creación de reactivos propios y selección aleatoria/manual."),
        ("RF09 - Despacho Asíncrono Email:", "Envío de invitación con token UUIDv4 (vigencia 48h) vía Gmail SMTP (aiosmtplib)."),
        ("RF10 - Flash Test WebSocket:", "Examinación cronometrada por reactivo, protección contra caídas y feedback final."),
        ("RF11 - Ruteo y Agendamiento:", "Agendamiento en el primer bloque libre del profesor para alumnos convocados a oficina."),
        ("RF12 - Cierre de Cita Presencial:", "Registro de acuerdos presenciales y actualización de la nota final del alumno.")
    ]
    for code, desc in rfs:
        story.append(Paragraph(f"<b>{code}</b> {desc}", styles['DocBullet']))

    story.append(Paragraph("<b>3.3 Requerimientos No Funcionales (RNF)</b>", styles['SubSecHeading']))
    rnfs = [
        ("RNF01 (Rendimiento):", "Soporte de 100 conexiones WebSocket concurrentes con latencia <= 50ms."),
        ("RNF02 (Seguridad):", "Tokens UUIDv4 de alta entropía y hashing bcrypt (costo >= 12) para accesos docentes."),
        ("RNF03 (Resiliencia):", "Mecanismo de fallback automático a Mock Engine en caso de desconexión con Anthropic."),
        ("RNF04 (Usabilidad):", "Interfaz Next.js + Tailwind CSS adaptada a accesibilidad WCAG 2.1 AA con tema oscuro."),
        ("RNF05 (Costo Cero):", "Operatividad 100% sustentada en tecnologías de código abierto (SQLite, FastAPI, Gmail SMTP).")
    ]
    for code, desc in rnfs:
        story.append(Paragraph(f"<b>{code}</b> {desc}", styles['DocBullet']))

    story.append(Paragraph("<b>3.4 Evaluación Crítica de Alternativas Técnicas</b>", styles['SubSecHeading']))
    alt_data = [
        [Paragraph("<b>Dimensión</b>", styles['TableHeader']), Paragraph("<b>Alternativas Evaluadas</b>", styles['TableHeader']), Paragraph("<b>Selección</b>", styles['TableHeader']), Paragraph("<b>Justificación Técnica</b>", styles['TableHeader'])],
        [
            Paragraph("<b>Acceso Alumno</b>", styles['TableCell']),
            Paragraph("1. Cuenta y password.<br/>2. SSO institucional.<br/>3. Token por correo.", styles['TableCell']),
            Paragraph("<b>Token vía Correo</b>", styles['TableCell']),
            Paragraph("Elimina fricción de registro; el docente no gestiona claves y el token valida posesión del correo oficial.", styles['TableCell'])
        ],
        [
            Paragraph("<b>Integridad</b>", styles['TableCell']),
            Paragraph("1. Detectores de caja negra.<br/>2. Proctored Browser.<br/>3. Flash Test Contextual.", styles['TableCell']),
            Paragraph("<b>Flash Test Contextual</b>", styles['TableCell']),
            Paragraph("Evita falsos positivos evaluando la autoría real en tiempo real mediante preguntas del propio trabajo.", styles['TableCell'])
        ],
        [
            Paragraph("<b>Conversión PDF</b>", styles['TableCell']),
            Paragraph("1. Texto plano.<br/>2. OCR Tesseract.<br/>3. pymupdf4llm.", styles['TableCell']),
            Paragraph("<b>pymupdf4llm</b>", styles['TableCell']),
            Paragraph("Conserva jerarquía de encabezados, tablas y listas con 40% menos de ruido léxico para el LLM.", styles['TableCell'])
        ],
        [
            Paragraph("<b>Servicio Email</b>", styles['TableCell']),
            Paragraph("1. SendGrid de pago.<br/>2. Servidor Postfix VPS.<br/>3. Gmail SMTP asíncrono.", styles['TableCell']),
            Paragraph("<b>Gmail SMTP (aiosmtplib)</b>", styles['TableCell']),
            Paragraph("Cero costo para el MVP con hasta 500 correos diarios mediante contraseña de aplicación.", styles['TableCell'])
        ],
    ]
    t_alt = Table(alt_data, colWidths=[90, 130, 110, 174])
    t_alt.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_alt)
    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────────
    # SECCIÓN 4: PLANIFICACIÓN Y PRODUCT BACKLOG (20%)
    # ─────────────────────────────────────────────────────────────
    story.append(Paragraph("4. Planificación del Proyecto y Product Backlog (20%)", styles['SecHeading']))
    story.append(HRFlowable(width="100%", thickness=1, color=c_primary, spaceBefore=2, spaceAfter=8))
    
    story.append(Paragraph("<b>4.1 Resumen de Épicas y Estimación de Esfuerzo (61 Story Points)</b>", styles['SubSecHeading']))
    bk_data = [
        [Paragraph("<b>Épica</b>", styles['TableHeader']), Paragraph("<b>Historias de Usuario</b>", styles['TableHeader']), Paragraph("<b>Prioridad MoSCoW</b>", styles['TableHeader']), Paragraph("<b>Story Points</b>", styles['TableHeader'])],
        [Paragraph("<b>ÉPICA 1:</b> Gestión Académica y Nómina Sin Cuentas", styles['TableCell']), Paragraph("US-01, US-02", styles['TableCell']), Paragraph("<i>Must Have</i>", styles['TableCell']), Paragraph("8 SP", styles['TableCell'])],
        [Paragraph("<b>ÉPICA 2:</b> Ingesta Masiva, Conversión a Markdown y Materiales", styles['TableCell']), Paragraph("US-03, US-04", styles['TableCell']), Paragraph("<i>Must Have</i>", styles['TableCell']), Paragraph("13 SP", styles['TableCell'])],
        [Paragraph("<b>ÉPICA 3:</b> Motor de Evaluación Contextual y Detección IA", styles['TableCell']), Paragraph("US-05, US-06", styles['TableCell']), Paragraph("<i>Must / Should</i>", styles['TableCell']), Paragraph("11 SP", styles['TableCell'])],
        [Paragraph("<b>ÉPICA 4:</b> Gestión Interactiva del Pool de Preguntas", styles['TableCell']), Paragraph("US-07", styles['TableCell']), Paragraph("<i>Must Have</i>", styles['TableCell']), Paragraph("8 SP", styles['TableCell'])],
        [Paragraph("<b>ÉPICA 5:</b> Motor de Despacho y Flash Test en Tiempo Real", styles['TableCell']), Paragraph("US-08, US-09", styles['TableCell']), Paragraph("<i>Must Have</i>", styles['TableCell']), Paragraph("13 SP", styles['TableCell'])],
        [Paragraph("<b>ÉPICA 6:</b> Agenda de Defensas y Cierre de Calificaciones", styles['TableCell']), Paragraph("US-10, US-11", styles['TableCell']), Paragraph("<i>Must Have</i>", styles['TableCell']), Paragraph("8 SP", styles['TableCell'])],
        [Paragraph("<b>TOTAL GENERAL DEL BACKLOG</b>", styles['TableHeader']), Paragraph("<b>11 Historias Refinadas</b>", styles['TableHeader']), Paragraph("-", styles['TableHeader']), Paragraph("<b>61 SP</b>", styles['TableHeader'])],
    ]
    t_bk = Table(bk_data, colWidths=[200, 120, 100, 84])
    t_bk.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('BACKGROUND', (0,-1), (-1,-1), c_secondary),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, colors.HexColor("#F8FAFC")]),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_bk)
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>4.2 Historias de Usuario Representativas y Criterios de Aceptación</b>", styles['SubSecHeading']))
    
    hu_cards = [
        ("US-02: Importación de Estudiantes vía CSV (Épica 1 — 5 SP | MUST HAVE)",
         "<b>Como:</b> Docente o ayudante de cátedra.<br/><b>Quiero:</b> Subir un archivo CSV con la lista de mis alumnos (nombre y correo).<br/><b>Para:</b> Registrar a toda la sección en segundos sin que ellos deban crear una cuenta.<br/><b>Criterios de Aceptación (Gherkin):</b><br/>• <b>Dado</b> un CSV 'Nombre,Correo' exportado de Excel con UTF-8 BOM.<br/>• <b>Cuando</b> el docente lo sube en '2. Estudiantes'.<br/>• <b>Entonces</b> el backend procesa las filas, descarta duplicados e informa el total creado."),
        ("US-05: Análisis Automatizado de Pauta y Detección de IA (Épica 3 — 8 SP | MUST HAVE)",
         "<b>Como:</b> Profesor evaluador.<br/><b>Quiero:</b> Que la IA analice cada informe contra la pauta y los materiales del curso.<br/><b>Para:</b> Obtener nota preliminar justificada, desglose por rúbrica y porcentaje de probabilidad de IA.<br/><b>Criterios de Aceptación (Gherkin):</b><br/>• <b>Dado</b> un informe PDF en estado 'processing'.<br/>• <b>Cuando</b> la IA completa el análisis con Claude 3.5 Sonnet.<br/>• <b>Entonces</b> el estado cambia a 'done', persistiendo nota, feedback y desglose en BD."),
        ("US-08: Despacho Asíncrono de Flash Test por Correo (Épica 5 — 5 SP | MUST HAVE)",
         "<b>Como:</b> Sistema evaluador.<br/><b>Quiero:</b> Enviar un correo HTML institucional con enlace tokenizado de un solo uso.<br/><b>Para:</b> Que el estudiante acceda a rendir su Flash Test seguro sin iniciar sesión.<br/><b>Criterios de Aceptación (Gherkin):</b><br/>• <b>Dado</b> un set de 10 preguntas aprobado por el profesor.<br/>• <b>Cuando</b> se ejecuta send_flash_test().<br/>• <b>Entonces</b> se genera token UUIDv4 con 48h de vigencia y se envía vía aiosmtplib."),
        ("US-10: Ruteo Inteligente y Agendamiento Automático (Épica 6 — 5 SP | MUST HAVE)",
         "<b>Como:</b> Plataforma IntegriEval.<br/><b>Quiero:</b> Clasificar el flash test y agendar cita en el primer bloque libre del profesor.<br/><b>Para:</b> Coordinar la defensa presencial automáticamente si el alumno obtuvo puntaje bajo, alto o aleatorio.<br/><b>Criterios de Aceptación (Gherkin):</b><br/>• <b>Dado</b> un estudiante con score flash del 40% (umbral < 50%).<br/>• <b>Cuando</b> finaliza el test.<br/>• <b>Entonces</b> se marca review_required = True, se asigna el primer bloque libre del profesor y se envía la citación por correo.")
    ]

    for title, content in hu_cards:
        t_hu = Table([[Paragraph(f"<b>{title}</b>", styles['BoxTitle'])], [Paragraph(content, styles['BoxContent'])]], colWidths=[504])
        t_hu.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
            ('PADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(t_hu)
        story.append(Spacer(1, 5))

    story.append(Spacer(1, 10))
    story.append(Paragraph("5. Conclusiones y Valor Estratégico", styles['SecHeading']))
    story.append(HRFlowable(width="100%", thickness=1, color=c_primary, spaceBefore=2, spaceAfter=8))
    story.append(Paragraph(
        "IntegriEval resuelve la tensión contemporánea entre la adopción de herramientas de IA generativa y la exigencia de certificar competencias académicas fidedignas. Al reemplazar los detectores tradicionales de caja negra por un <b>modelo híbrido de análisis contextualizado, evaluación flash reactiva y defensa oral focalizada</b>, la plataforma optimiza el tiempo docente, garantiza transparencia ética y entrega una experiencia ágil y justa para toda la comunidad universitaria.",
        styles['DocBody']
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
    print("PDF build complete:", filename)

if __name__ == "__main__":
    build_pdf()
