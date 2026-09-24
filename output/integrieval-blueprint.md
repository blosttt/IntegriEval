# Blueprint de Arquitectura y Especificación del Sistema: IntegriEval
**Sistema Semi-Automatizado de Evaluación de Integridad Académica, Detección de IA y Verificación Oral Flash**  
*Documento de Especificación Formal de Ingeniería de Software — Trabajo de Título (INFO1197)*  
**Autores:** Sebastian Cisternas, Benjamin Sobarzo  
**Fecha:** Septiembre 2026 | **Versión:** 1.0 (Borrador para validación)  
**Facultad:** Ingeniería Civil Informática | **Repositorio:** github.com/blosttt/IntegriEval  

---

## 1. Definición del Problema y Alcance

### 1.1 Contexto y Antecedentes
La democratización de los Modelos de Lenguaje Grande (LLMs) ha transformado la evaluación en la educación superior. Los estudiantes entregan trabajos digitales en los LMS institucionales (Canvas, Moodle, Blackboard), pero los docentes carecen de herramientas confiables y pedagógicamente justas para verificar si el contenido refleja las competencias reales del estudiante o fue generado por IA.

### 1.2 Articulación del Problema (3 Dimensiones Críticas)
1. **Inviabilidad de los Detectores Estadísticos de 'Caja Negra':** Herramientas como Turnitin AI tienen altas tasas de falsos positivos y negativos, careciendo de validez jurídica y ética para sanciones.
2. **Inviabilidad Logística de la Interrogación Universal:** La defensa oral presencial es efectiva, pero es humanamente imposible de implementar en cursos masivos (60 a 200 alumnos).
3. **Sobrecarga Cognitiva y Temporal:** Los docentes dedican hasta 25 horas semanales a la corrección mecánica de informes contra pauta.

### 1.3 Validación con Partes Interesadas (Stakeholders)
- **Docentes:** *"No sé si el alumno aprendió o si un LLM hizo el trabajo. No puedo interrogar a 100 alumnos ni acusar a nadie sin pruebas."* $\rightarrow$ **Expectativa:** Herramienta que entregue notas preliminares justificadas y evidencia para la toma de decisiones respecto del alumnado (ej: a quiénes citar para defensa oral).
- **Ayudantes:** *"Revisar 80 PDFs idénticos es agotador y dilata la retroalimentación."* $\rightarrow$ **Expectativa:** Subida masiva en lote y extracción de resúmenes estructurados en Markdown.
- **Estudiantes:** *"Frustrante que un detector te acuse injustamente. Si hay dudas, prefiero que me hagan preguntas sobre mi trabajo."* $\rightarrow$ **Expectativa:** Proceso transparente y derecho a defensa oral.
- **Dirección de Carrera:** *"Debemos resguardar el prestigio y evitar sanciones arbitrarias que deriven en litigios."* $\rightarrow$ **Expectativa:** Trazabilidad auditable y defensas orales fundamentadas en evidencia.

---

## 2. Objetivos del Proyecto y Trazabilidad

### 2.1 Objetivo General
Desarrollar un MVP de plataforma web que asista al docente en la verificación del aprendizaje real del estudiante, a través de un flujo que integra análisis automatizado del PDF, generación de preguntas flash personalizadas y soporte para validación oral focalizada, sin reemplazar el criterio docente como autoridad final.

> **Alcance del Proyecto:** Educación superior, con enfoque en cursos masivos de estudiantes, MVP open-source y sin costos recurrentes. No incluye integración LMS en su versión inicial.

---

### 2.2 Objetivos Específicos (Criterios SMART por Sprint)

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ OE1 (Sprint 1): Análisis de Requerimientos                                                                      │
│ • Enunciado: Analizar los requerimientos funcionales y no funcionales del proceso de verificación de            │
│   aprendizaje.                                                                                                  │
│ • Specific: Levantamiento de problema, actores y restricciones.                                                 │
│ • Measurable: Documento validado con matriz de trazabilidad completa.                                           │
│ • Relevant: Base para el diseño correcto del MVP.                                                               │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ OE2 (Sprint 2): Diseño de Arquitectura y Decisiones Técnicas                                                    │
│ • Enunciado: Diseñar la arquitectura del sistema y las decisiones técnicas del MVP.                             │
│ • Specific: Arquitectura sin login, evaluación contextual con LLM, estrategia costo-cero (sección 3.7).        │
│ • Measurable: 100% de decisiones técnicas justificadas en matriz de alternativas.                              │
│ • Relevant: Evita retrabajo en implementación.                                                                  │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ OE3 (Sprint 3): Implementación de Módulos Funcionales del MVP                                                   │
│ • Enunciado: Implementar los módulos funcionales del MVP.                                                       │
│ • Specific: Ingesta/nómina, motor IA, pool de preguntas, flash test, panel y cierre.                            │
│ • Measurable: 61 Story Points entregados en 4 Sprints (11 Historias de Usuario).                                │
│ • Relevant: Entrega funcional completa.                                                                         │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ OE4 (Sprint 4): Validación de Funcionamiento y Control Docente                                                  │
│ • Enunciado: Validar el funcionamiento del sistema y el control docente sobre el resultado.                    │
│ • Specific: Rendimiento (<=15s, <=100ms), precisión detección IA (>=75%), 100% notas confirmadas por docente.  │
│ • Measurable: Métricas RNF cumplidas + AuditLog inmutable verificado.                                           │
│ • Relevant: Confianza y cumplimiento ético/legal.                                                               │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 2.3 Matriz de Trazabilidad (Problema vs. Objetivos vs. Entregables)

| Dimensión del Problema | Objetivo(s) | Entregable Concreto |
|---|---|---|
| **Falsos positivos de detectores IA** | OE2, OE3 | Evaluación contextualizada con pauta y generación de preguntas personalizadas. |
| **Imposibilidad logística de interrogar a todos** | OE3 | Panel de resultados que filtra estudiantes por puntaje para decidir a quién citar. |
| **Fricción de adopción tecnológica** | OE2, OE3 | Acceso sin login con nómina CSV y enlaces tokenizados (UUIDv4). |
| **Evaluación sin contexto de la asignatura** | OE2 | Inyección de syllabus, guías y rúbricas en el prompt del LLM. |
| **Pérdida de control del docente** | OE3, OE4 | Editor de preguntas y panel de cierre con confirmación explícita de nota. |
| **Presupuesto cero para el MVP** | OE2, OE3 | Despacho con Gmail SMTP gratuito y arquitectura de costo cero. |
| **Docente no puede probar el uso indebido de IA** | OE3, OE4 | Desglose JSON y AuditLog inmutable. |
| **Tiempo excesivo en corrección mecánica** | OE3, OE4 | Automatización del análisis preliminar, focalizando tiempo docente en defensas. |

---

## 3. Especificación Formal de Requerimientos

### 3.1 Requerimientos Funcionales (RF-001 al RF-015)

| ID | Requisito Funcional | Prioridad | Estado |
|---|---|---|---|
| **RF-001** | Crear y gestionar asignaturas (nombre, periodo, año). | Must | Bueno |
| **RF-002** | Ingesta de CSV con nombres y correos, validando formato y duplicados. | Must | Bueno |
| **RF-003** | Configurar: prompt, rigor, pool (10-30), umbrales visuales. | Must | Bueno |
| **RF-004** | Subir materiales (PDF/DOCX) y convertirlos a Markdown para contexto. | Must | Bueno |
| **RF-005** | Carga masiva de PDFs y asociación automática por nombre de archivo. | Must | Bueno |
| **RF-006** | Extraer PDFs a Markdown preservando títulos, tablas y listas. | Must | Bueno |
| **RF-007** | Evaluar con Modelos LLM: nota, feedback, % detección IA (según estructura JSON Anexo A). | Must | Bueno |
| **RF-008** | Mediante el LLM, generar un pool de X preguntas basadas en la temática y contenidos del informe (apoyado con material subido). | Must | Bueno |
| **RF-009** | Permitir al docente editar/eliminar/agregar preguntas y seleccionar cuántas incluirá en la prueba flash ($N \le \text{Pool}$). | Must | Bueno |
| **RF-010** | Despachar flash test con tokens UUIDv4 (48h) vía Gmail SMTP. | Must | Bueno |
| **RF-011** | Interfaz flash test con WebSockets, temporizador 60+s/flash-test. | Must | Bueno |
| **RF-012** | Panel de resultados para docente con métricas clave para decisión. | Must | Bueno |
| **RF-013** | Registrar acuerdos de defensas, ajustar nota final y audit log inmutable. | Must | Bueno |
| **RF-014** | Contar con Mock Engine de contingencia. | Should | Bueno |
| **RF-015** | Autenticación docente (Pendiente de formalización). | Por definir | Incompleto |

---

### 3.2 Requerimientos No Funcionales (RNF-001 al RNF-013)

| ID | Categoría | Requisito | Métrica | Prioridad | Estado |
|---|---|---|---|---|---|
| **RNF-001** | Rendimiento | Soportar 100 conexiones WebSocket concurrentes. | Latencia $\le 50\text{ms}$ | Must | Bueno |
| **RNF-002** | Rendimiento | Procesar informe en $\le 15\text{s}$ (CPU). | $95\%$ de casos | Must | Bueno |
| **RNF-003** | Rendimiento | API de cierre de calificaciones. | $\le 200\text{ms}$ | Should | Bueno |
| **RNF-004** | Seguridad | Tokens UUIDv4 (RFC 4122). | UUIDv4 | Must | Bueno |
| **RNF-005** | Seguridad | Contraseñas con bcrypt. | Factor $\ge 12$ | Must | Bueno |
| **RNF-006** | Seguridad | RBAC por asignatura. | RBAC | Must | Bueno |
| **RNF-007** | Resiliencia | Fallback automático a Mock Engine. | Timeout $> 30\text{s}$ | Should | Bueno |
| **RNF-008** | Resiliencia | Reconexión WebSocket. | $\le 120\text{s}$ | Should | Bueno |
| **RNF-009** | Usabilidad | WCAG 2.1 AA y tema oscuro. | WCAG 2.1 AA | Could | Bueno |
| **RNF-010** | Costo | $100\%$ open-source, sin costos recurrentes. | Sin costos | Must | Bueno |
| **RNF-011** | Disponibilidad | Pendiente: $[X]\%$ en horario de evaluación. | Por definir | Por definir | Incompleto |
| **RNF-012** | Escalabilidad | Pendiente: $[X]$ estudiantes simultáneos. | Por definir | Por definir | Incompleto |
| **RNF-013** | Privacidad | Cumplimiento Ley N° 21.719 (Protección de Datos Personales Chile). | Verificable antes de 01/12/2026 | Must | Requiere ajuste |

---

### 3.3 Reglas de Negocio (RN-001 al RN-007)

- **RN-001 (Acceso Tokenizado):** Token UUIDv4 válido con vigencia de 48h. Permite acceso al test y se invalida tras el primer uso.
- **RN-002 (Temporizador Expirado):** Al expirar el temporizador de 60s/pregunta, el sistema registra respuesta parcial y calcula puntaje sobre las preguntas respondidas.
- **RN-003 (Panel de Indicadores):** Umbrales parametrizables por asignatura en `Asignatura.parametros` (RF-003). El sistema resalta visualmente a los alumnos críticos.
- **RN-004 (Nota Final Editable):** La nota final es editable por el docente dentro del rango, con campo de justificación obligatorio (por defecto *"Criterio del docente"*). Persiste con auditoría (usuario, fecha, hora).
- **RN-005 (Pendiente):** Ausencia a defensa sin justificación.
- **RN-006 (Pendiente):** Solicitud de reprogramación.
- **RN-007 (Pendiente):** Pérdida de enlace $\rightarrow$ reenvío.

---

### 3.4 Requerimientos de Integración (RI-001 al RI-003)

- **RI-001 (LLM Auto-hospedado / API):** LLM open-source (Llama 3.x o Qwen2.5 vía Ollama / Claude 3.5 Sonnet) local sin costo API. Bidireccional REST HTTPS para evaluación y generación de preguntas.
- **RI-002 (Gmail SMTP):** Protocolo SMTP TLS para envío unidireccional de correos con enlaces tokenizados.
- **RI-003 (Pendiente LMS Blackboard):** API para sincronización de nóminas y notas (Incompleto / Futuro).

---

### 3.5 Requerimientos de Datos (Entidades y Atributos Clave)

- **Usuario:** `id`, `nombre`, `correo` (único), `contraseña` (bcrypt), `rol`, `asignaturas`.
- **Asignatura:** `id`, `nombre`, `periodo`, `año`, `docente_id`, `parámetros` (JSON).
- **Estudiante:** `id`, `nombre`, `correo` (único por asignatura), `asignatura_id`.
- **Trabajo:** `id`, `estudiante_id`, `pdf_path`, `markdown`, `estado`.
- **Material:** `id`, `asignatura_id`, `nombre`, `tipo`, `markdown`.
- **Evaluacion:** `id`, `trabajo_id`, `nota` (1-7), `feedback` (JSON), `% IA` (0-100), `desglose`.
- **Pregunta:** `id`, `evaluacion_id`, `texto`, `alternativas` (JSON), `seleccionada`.
- **FlashTest:** `id`, `estudiante_id`, `token` (único), `vigencia` (48h), `respuestas` (JSON), `puntaje`, `estado`.
- **Cita:** `id`, `estudiante_id`, `docente_id`, `fecha`, `bloque`, `estado`, `creada_por`.
- **AuditLog:** `id`, `usuario_id`, `accion`, `tabla`, `registro_id`, `timestamp`, `datos_previos` (JSON), `datos_nuevos` (JSON).  
*(Observaciones: Retención de datos pendiente; AuditLog inmutable).*

---

### 3.6 Evaluación Crítica de Alternativas (Sección 3.7)

#### Validación del Aprendizaje:
- **A: Solo detector de IA:** Ventajas: Fácil de implementar | Desventajas: No verifica aprendizaje | **Conclusión:** *Descartada* (No resuelve el problema de fondo).
- **B: Solo entrevista oral humana:** Ventajas: Verifica aprendizaje con alta certeza | Desventajas: No es escalable | **Conclusión:** *Descartada* (Impracticable en la mayoría de contextos masivos).
- **C: Nuestra solución (Detección + Flash Test + Panel):** Ventajas: Combina automatización con juicio humano; escala bien | Desventajas: Mayor complejidad técnica | **Conclusión:** *Seleccionada* (Equilibra lo mejor de ambos).

#### Alternativas Tecnológicas:
- **Acceso alumno:** *Selección:* Token vía Email (elimina fricción de registro; valida posesión del correo oficial).
- **Estrategia de Integridad:** *Selección:* Flash Test Contextual (evita falsos positivos evaluando autoría real).
- **Conversión PDF:** *Selección:* `pymupdf4llm` (conserva jerarquía de encabezados, tablas y listas con 40% menos de ruido léxico).
- **Servicio de Email:** *Selección:* Gmail SMTP `aiosmtplib` (cero costo para el MVP con hasta 500 correos diarios).

---

## 4. Planificación del Proyecto y Product Backlog (61 Story Points)

### 4.1 Resumen de Épicas y Distribución por Sprints

```
╔═══════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                 PLANIFICACIÓN DE SPRINTS Y ÉPICAS                                     ║
╠═════════════════════════════════════════════════════════════════╦═══════════════╦══════════════╦══════╣
║ Épica                                                           ║ Historias     ║ Total SP     ║Sprint║
╠═════════════════════════════════════════════════════════════════╬═══════════════╬══════════════╬══════╣
║ ÉPICA 1: Gestión y Nómina (OE1)                                 ║ US-01, US-02  ║ 8 SP         ║ Sp. 1║
║ ÉPICA 2: Ingesta y Conversión (OE1)                             ║ US-03, US-04  ║ 13 SP        ║ Sp. 1║
║ ÉPICA 3: Motor de Evaluación (OE2)                              ║ US-05, US-06  ║ 11 SP        ║ Sp. 2║
║ ÉPICA 4: Pool de Preguntas (OE3)                                ║ US-07         ║ 8 SP         ║ Sp. 3║
║ ÉPICA 5: Despacho y Flash Test (OE3)                            ║ US-08, US-09  ║ 13 SP        ║ Sp. 3║
║ ÉPICA 6: Resultados y Cierre (OE4)                              ║ US-10, US-11  ║ 8 SP         ║ Sp. 4║
╠═════════════════════════════════════════════════════════════════╬═══════════════╬══════════════╬══════╣
║ TOTAL GENERAL DEL BACKLOG                                       ║ 11 Historias  ║ 61 SP        ║4 Sp. ║
╚═════════════════════════════════════════════════════════════════╩═══════════════╩══════════════╩══════╝
```

* **Sprint 1 (Ingesta):** Épicas 1 y 2 (US-01 a US-04) = **21 SP** ($\approx 4.2$ semanas)
* **Sprint 2 (Análisis):** Épica 3 (US-05, US-06) = **11 SP** ($\approx 2.2$ semanas)
* **Sprint 3 (Reactivos y Despacho):** Épicas 4 y 5 (US-07 a US-09) = **21 SP** ($\approx 4.2$ semanas)
* **Sprint 4 (Resultados y Cierre):** Épica 6 (US-10, US-11) = **8 SP** ($\approx 1.6$ semanas)
* **Total del Proyecto:** 11 Historias Refinadas, 61 Story Points, $\approx 12.2$ semanas.

---

### 4.2 Desglose de Historias de Usuario y Criterios de Aceptación

- **US-01: Creación y Gestión de Asignaturas (3 SP):** Como Docente quiero crear y gestionar asignaturas para organizar mis cursos. *CA:* Dado un docente autenticado, cuando crea una asignatura, entonces queda registrada.
- **US-02: Importación de Estudiantes vía CSV (5 SP):** Como Docente o ayudante quiero subir CSV con lista de alumnos para registrar la sección en segundos. *CA:* Dado un CSV válido, cuando el docente lo sube, entonces se procesa y se informa el total de alumnos creados.
- **US-03: Subida Masiva de Trabajos y Conversión a Markdown (8 SP):** Como Ayudante o Docente quiero subir múltiples PDFs y extraer su contenido para automatizar la ingesta. *CA:* Dado un conjunto de PDFs, cuando se suben en lote, entonces cada PDF se convierte a Markdown.
- **US-04: Gestión de Materiales de Apoyo (5 SP):** Como Docente quiero subir syllabus y rúbricas para dar contexto al LLM. *CA:* Dado un docente, cuando sube un syllabus, entonces se guarda como contexto.
- **US-05: Análisis Automatizado con LLM (8 SP):** Como Docente quiero que la IA analice cada trabajo contra la pauta para obtener una nota preliminar justificada. *CA:* Dado un PDF en estado "processing", cuando el análisis termina, entonces el estado cambia a "done".
- **US-06: Motor de Contingencia (Mock Engine) (3 SP):** Como Sistema quiero tener un fallback sin conexión para garantizar operatividad. *CA:* Dado un fallo en la API de Anthropic, cuando se intenta analizar, entonces se usa el Mock Engine.
- **US-07: Generación y Gestión del Pool de Preguntas (8 SP):** Como Docente quiero revisar, editar y aprobar un subconjunto de preguntas generadas por IA antes de enviarlas al estudiante para garantizar que sean respondibles por quien realizó el trabajo y alineadas con la rúbrica.
  - *CA-a:* Dado un informe analizado, cuando el docente accede al generador, se muestran 20 preguntas editables individualmente.
  - *CA-b:* Dado una pregunta genérica, cuando la edita o descarta, el sistema permite reemplazarla o dejar el pool con menos de 20.
  - *CA-c:* Dado un pool revisado, cuando marca 10 como aprobadas, el sistema bloquea el envío hasta que exactamente 10 estén seleccionadas.
  - *CA-d:* Dado menos de 10 aprobadas, cuando intenta despachar (US-08), el sistema impide la acción y muestra advertencia.
- **US-08: Despacho Asíncrono de Flash Test por Correo (5 SP):** Como Sistema quiero enviar correo con enlace tokenizado para acceso seguro del estudiante. *CA:* Dado un set de 10 preguntas aprobado, cuando se ejecuta el despacho, se genera un token UUIDv4 y se envía el correo.
- **US-09: Interfaz del Flash Test en Tiempo Real (WebSocket) (8 SP):** Como Estudiante quiero responder con temporizador y feedback para demostrar mi comprensión. *CA:* Dado un estudiante con token válido, cuando accede al test, responde (60s/pregunta) y recibe su puntaje.
- **US-10: Panel de Resultados del Flash Test (5 SP):** Como Docente quiero visualizar resultados con indicadores clave para tomar decisiones (citar a defensa oral). *CA:* Dado un curso con estudiantes que han rendido el test, cuando el docente accede al panel, visualiza todos los resultados con indicadores.
- **US-11: Cierre de Calificaciones y Auditoría (3 SP):** Como Docente quiero registrar defensas, ajustar nota y dejar constancia para mantener control final. *CA:* Dado un estudiante con datos de evaluación, cuando el docente accede al cierre, confirma la nota y la acción queda registrada en el AuditLog.

---

### 4.3 Matriz de Alineación Backlog-Objetivos (Sección 4.4)

| Objetivo | Historias Asociadas | Tareas Técnicas Clave | Criterios de Aceptación |
|---|---|---|---|
| **OE1** | US-01, US-02, US-03, US-04 | Modelos SQLAlchemy, endpoints CRUD, parser CSV, procesamiento asíncrono, `pymupdf4llm`. | CA-001, CA-002, CA-003, CA-004 |
| **OE2** | US-05, US-06 | API Anthropic, prompt design, procesamiento asíncrono, Mock Engine Heurístico. | CA-005, CA-006 |
| **OE3** | US-07, US-08 | Generación de preguntas, interfaz de edición, Gmail SMTP, tokens UUIDv4. | CA-007, CA-008 |
| **OE4** | US-09, US-10, US-11 | WebSockets, interfaz reactiva, temporizador 60s, panel de resultados con filtros, panel de cierre, confirmación/modificación de nota, AuditLog inmutable. | CA-009, CA-010, CA-011 |

---

## 5. Anexo A: Estructura JSON de Evaluación (RF-007)

```json
{
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
}
```
