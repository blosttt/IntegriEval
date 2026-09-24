# Blueprint Maestro de Construcción y Arquitectura: IntegriEval
**Sistema Semi-Automatizado de Evaluación de Integridad Académica, Detección de IA y Verificación Oral Flash**  
*Documento de Ingeniería y Guía de Construcción Paso a Paso de 0 a Producción*  
**Autores:** Sebastian Cisternas, Benjamin Sobarzo | **Fecha:** Septiembre 2026 | **Versión:** 1.0.0  
**Proyecto:** Trabajo de Título (INFO1197) — Ingeniería Civil Informática  

---

## TABLA DE CONTENIDOS
1. [Visión Global y Modelo de Negocio](#1-visión-global-y-modelo-de-negocio)
2. [Arquitectura del Sistema y Decisiones Técnicas](#2-arquitectura-del-sistema-y-decisiones-técnicas)
3. [Estructura de Directorios del Proyecto](#3-estructura-de-directorios-del-proyecto)
4. [Modelo de Datos y Esquema DDL SQL](#4-modelo-de-datos-y-esquema-ddl-sql)
5. [Diseño de API RESTful y Protocolo WebSocket](#5-diseño-de-api-restful-y-protocolo-websocket)
6. [Motor de IA, Extracción Documental y Mock Engine](#6-motor-de-ia-extracción-documental-y-mock-engine)
7. [Arquitectura Frontend y Componentes Clave](#7-arquitectura-frontend-y-componentes-clave)
8. [Reglas de Negocio y Algoritmo de Ruteo](#8-reglas-de-negocio-y-algoritmo-de-ruteo)
9. [Guía de Construcción Paso a Paso (Paso 1 al 8)](#9-guía-de-construcción-paso-a-paso)
10. [Configuración del Entorno y Variables (.env)](#10-configuración-del-entorno-y-variables-env)
11. [Estrategia de Testing y Verificación](#11-estrategia-de-testing-y-verificación)
12. [Checklist de Prelanzamiento (P0 / P1 / P2)](#12-checklist-de-prelanzamiento)
13. [Anexo: Estructura JSON de Evaluación (RF-007)](#13-anexo-estructura-json-de-evaluación-rf-007)

---

## 1. Visión Global y Modelo de Negocio

### 1.1 Qué es IntegriEval y qué problema resuelve
**IntegriEval** es una solución de software orientada a la educación superior que resuelve la crisis de evaluación desatada por la proliferación de Modelos de Lenguaje Grande (LLMs como GPT-4, Claude, Gemini).

Actualmente, los estudiantes entregan sus informes digitales en el LMS institucional (Canvas, Moodle, Blackboard). Los docentes y ayudantes descargan decenas de archivos PDF y enfrentan tres problemas críticos:
1. **Inviabilidad de los Detectores Estadísticos de 'Caja Negra':** Herramientas como Turnitin AI o GPTZero presentan altas tasas de falsos positivos y negativos al basarse únicamente en perplejidad estadística, careciendo de validez ética y jurídica para aplicar sanciones.
2. **Inviabilidad Logística de la Interrogación Universal:** Examinar oralmente al 100% de los estudiantes en cursos masivos (60 a 200 alumnos) es imposible por restricciones de tiempo docente.
3. **Sobrecarga Cognitiva en la Corrección:** Los docentes dedican hasta 25 horas semanales a cotejar mecánicamente informes contra pautas y bibliografía.

### 1.2 La Solución Híbrida (Flujo de 5 Pasos)
IntegriEval no reemplaza al profesor; actúa como un asistente inteligente bajo el paradigma **Human-in-the-Loop**:
1. **Ingesta y Extracción:** El docente carga la nómina de alumnos en CSV (sin que los alumnos creen cuentas) y sube el lote de PDFs de informes más el syllabus/materiales de la asignatura. El sistema convierte los PDFs a Markdown semántico con `pymupdf4llm`.
2. **Evaluación Contextualizada con IA:** El LLM evalúa cada trabajo contrastándolo con la pauta y los materiales del curso, entregando una nota preliminar (1.0 a 7.0), desglose de rúbrica, fortalezas/debilidades y un índice de detección de IA.
3. **Pool de Preguntas y Supervisión Docente:** La IA genera 20 preguntas personalizadas sobre el informe. El docente revisa, edita o agrega reactivos y selecciona 10 para la prueba.
4. **Flash Test en Tiempo Real:** El sistema despacha por Gmail SMTP un enlace con token UUIDv4 único (vigencia 48h). El alumno ingresa sin login y rinde la prueba flash vía WebSocket (60 segundos por pregunta con temporizador server-side).
5. **Ruteo a Defensas y Cierre con Auditoría:** El algoritmo rutea automáticamente a citación presencial solo a casos críticos (score flash $<50\%$, $\ge 95\%$ o $10\%$ aleatorio de control). Tras la entrevista presencial, el docente ratifica o ajusta la nota final en el panel, registrando la acción en un `AuditLog` inmutable.

```mermaid
flowchart LR
    A["1. Docente sube CSV + PDFs"] --> B["2. Extracción Markdown + Análisis IA"]
    B --> C["3. Docente aprueba 10 preguntas"]
    C --> D["4. Alumno rinde Flash Test (60s/preg)"]
    D --> E{"5. Score Flash"}
    E -->|"<50%, >=95% o 10% azar"| F["Cita Defensa Presencial"]
    E -->|"50% a 94%"| G["Aprobación Directa"]
    F --> H["Docente cierra nota + AuditLog"]
    G --> H
```

---

## 2. Arquitectura del Sistema y Decisiones Técnicas

```mermaid
graph TD
    subgraph FRONTEND["Frontend SPA (Next.js 15 / Tailwind CSS / shadcn/ui)"]
        UI_T["Panel Docente 9-en-1 (/teacher/dashboard)"]
        UI_F["Sala Flash Test Estudiante (/flash/[token])"]
    end

    subgraph BACKEND["Backend API (FastAPI / Python 3.14)"]
        API_AUTH["Auth JWT Docente"]
        API_CORE["Gestor Cursos, CSV y PDFs"]
        API_WS["Servidor WebSocket + Temporizador"]
        API_AI["Servicio Inferencia LLM / Mock Engine"]
        API_AUDIT["AuditLog & Cierre Calificaciones"]
    end

    subgraph INTEGRACION["Servicios de Integración"]
        EXT_AI["Anthropic Claude 3.5 Sonnet / Ollama Local"]
        EXT_MAIL["Gmail SMTP TLS (aiosmtplib)"]
    end

    subgraph STORAGE["Capa de Datos"]
        DB[(SQLite Local / PostgreSQL con SQLAlchemy 2.0)]
        FS["Almacenamiento Local de Archivos (PDFs/Markdown)"]
    end

    UI_T -->|HTTP REST| API_AUTH
    UI_T -->|HTTP REST| API_CORE
    UI_T -->|HTTP REST| API_AUDIT
    UI_F -->|WebSocket WSS| API_WS

    API_CORE --> FS
    API_CORE --> DB
    API_AI --> EXT_AI
    API_WS --> EXT_MAIL
    API_WS --> DB
    API_AUDIT --> DB
```

### Justificación de Decisiones Técnicas:
- **Next.js 15 (App Router):** Soporte de Server Components para vistas informativas y Client Components reactivos para el dashboard docente y el examen en tiempo real.
- **FastAPI + Python 3.14:** Rendimiento asíncrono superior, soporte nativo de WebSockets (Starlette) para el examen en vivo y ecosistema líder para procesamiento de texto e IA.
- **SQLAlchemy 2.0:** Abstracción ORM completa compatible tanto con SQLite para desarrollo local portátil como con PostgreSQL para despliegues masivos.
- **`pymupdf4llm`:** Extrae texto de PDFs a Markdown preservando títulos, listas y tablas con un 40% menos de ruido léxico comparado con OCR o extractores de texto plano.
- **Zero-Password para Estudiantes:** Los alumnos no crean cuentas. El token UUIDv4 (128 bits de entropía) enviado a su correo institucional valida la posesión de la cuenta de forma segura y sin fricción.
- **Gmail SMTP asíncrono (`aiosmtplib`):** Permite enviar hasta 500 correos diarios sin costo de APIs transaccionales para el MVP universitario.

---

## 3. Estructura de Directorios del Proyecto

```tree
IntegriEval/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── appointments.py      # Agendamiento y cierre de defensas orales
│   │   │   ├── courses.py           # CRUD de asignaturas y configuración
│   │   │   ├── dashboard.py         # Estadísticas globales y AuditLog
│   │   │   ├── evaluations.py       # Configuración de rúbricas y rigor
│   │   │   ├── flash.py             # Validación token y WebSocket del examen
│   │   │   ├── materials.py         # Subida y conversión de syllabus/guías
│   │   │   ├── reports.py           # Ingesta masiva PDF, análisis IA y pool de preguntas
│   │   │   └── students.py          # Parser CSV y gestión de nómina
│   │   ├── core/
│   │   │   ├── config.py            # Settings con pydantic-settings
│   │   │   ├── database.py          # Engine SQLAlchemy y SessionLocal
│   │   │   └── security.py          # Hashing bcrypt y JWT docentes
│   │   ├── models/
│   │   │   └── models.py            # 10 Entidades SQLAlchemy
│   │   ├── schemas/
│   │   │   └── schemas.py           # Validadores Pydantic v2
│   │   ├── services/
│   │   │   ├── ai_service.py        # Integración Claude 3.5 Sonnet y Mock Engine
│   │   │   ├── email_service.py     # Despacho asíncrono con aiosmtplib
│   │   │   ├── extractor.py         # Conversión PDF a Markdown con pymupdf4llm
│   │   │   └── scheduling.py       # Lógica de ruteo y asignación de citas
│   │   └── main.py                  # Entrypoint FastAPI, CORS y routers
│   ├── tests/
│   │   ├── test_api.py              # Tests de endpoints REST
│   │   ├── test_extractor.py        # Tests de extracción de PDFs
│   │   └── test_websocket.py        # Tests de flujo WebSocket del Flash Test
│   ├── pyproject.toml
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx           # Layout general con estilos globales
│   │   │   ├── page.tsx             # Landing informativa
│   │   │   ├── flash/
│   │   │   │   └── [token]/
│   │   │   │       └── page.tsx     # Sala de examen Flash en tiempo real (WebSocket)
│   │   │   └── teacher/
│   │   │       ├── dashboard/
│   │   │       │   └── page.tsx     # Panel 9-en-1 del docente
│   │   │       └── login/
│   │   │           └── page.tsx     # Login docente
│   │   ├── components/
│   │   │   ├── ui/                  # Componentes reutilizables (Botones, Modales, Badges)
│   │   │   ├── Dropzone.tsx         # Componente de subida masiva Drag & Drop
│   │   │   ├── QuestionEditor.tsx   # Editor interactivo de preguntas
│   │   │   ├── FlashTimer.tsx       # Temporizador circular SVG
│   │   │   └── AuditLogTable.tsx    # Tabla de auditoría inmutable
│   │   ├── lib/
│   │   │   ├── api.ts               # Cliente API tipado para todos los endpoints
│   │   │   └── utils.ts
│   │   └── types/
│   │       └── index.ts             # Interfaces TypeScript compartidas
│   ├── package.json
│   ├── tailwind.config.ts
│   └── tsconfig.json
├── docs/                            # Documentación técnica compilada
├── output/                          # Blueprints generados
└── README.md
```

---

## 4. Modelo de Datos y Esquema DDL SQL

A continuación se define el esquema relacional formal con soporte para PostgreSQL y SQLite:

```sql
-- 1. Usuarios (Docentes y Ayudantes)
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT, -- En Postgres: SERIAL PRIMARY KEY
    nombre VARCHAR(150) NOT NULL,
    correo VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(50) DEFAULT 'docente', -- 'docente' | 'admin' | 'ayudante'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Asignaturas
CREATE TABLE IF NOT EXISTS asignaturas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    docente_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    nombre VARCHAR(200) NOT NULL,
    periodo VARCHAR(50) NOT NULL,
    anio INTEGER NOT NULL,
    parametros TEXT DEFAULT '{"rigor": "medium", "pool_size": 20, "flash_size": 10, "umbral_bajo": 50, "umbral_alto": 95, "porcentaje_aleatorio": 10}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Estudiantes (Nómina sin contraseña)
CREATE TABLE IF NOT EXISTS estudiantes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asignatura_id INTEGER NOT NULL REFERENCES asignaturas(id) ON DELETE CASCADE,
    nombre VARCHAR(150) NOT NULL,
    correo VARCHAR(150) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_estudiante_asignatura UNIQUE (asignatura_id, correo)
);

-- 4. Materiales de Apoyo (Syllabus, Guías)
CREATE TABLE IF NOT EXISTS materiales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asignatura_id INTEGER NOT NULL REFERENCES asignaturas(id) ON DELETE CASCADE,
    nombre VARCHAR(200) NOT NULL,
    tipo VARCHAR(50) NOT NULL, -- 'syllabus' | 'guia' | 'rubrica'
    markdown_content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Trabajos / Informes Entregados
CREATE TABLE IF NOT EXISTS trabajos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    estudiante_id INTEGER NOT NULL REFERENCES estudiantes(id) ON DELETE CASCADE,
    pdf_path VARCHAR(500) NOT NULL,
    markdown_content TEXT NOT NULL,
    estado VARCHAR(50) DEFAULT 'uploaded', -- 'uploaded' | 'processing' | 'done' | 'error'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Evaluaciones de IA
CREATE TABLE IF NOT EXISTS evaluaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trabajo_id INTEGER UNIQUE NOT NULL REFERENCES trabajos(id) ON DELETE CASCADE,
    nota_preliminar REAL, -- Escala 1.0 a 7.0
    porcentaje_ia INTEGER DEFAULT 0, -- 0 a 100%
    feedback TEXT DEFAULT '{}', -- JSON con fortalezas, debilidades, recomendaciones
    desglose_rubrica TEXT DEFAULT '{}', -- JSON con criterios de pauta
    nota_final REAL,
    estado_cierre VARCHAR(50) DEFAULT 'pendiente', -- 'pendiente' | 'confirmada' | 'revisada_oral'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Preguntas del Pool
CREATE TABLE IF NOT EXISTS preguntas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    evaluacion_id INTEGER NOT NULL REFERENCES evaluaciones(id) ON DELETE CASCADE,
    enunciado TEXT NOT NULL,
    tipo VARCHAR(50) DEFAULT 'multiple_choice', -- 'multiple_choice' | 'true_false'
    alternativas TEXT NOT NULL, -- JSON: {"A": "...", "B": "...", "C": "...", "D": "..."}
    respuesta_correcta VARCHAR(10) NOT NULL,
    explicacion TEXT,
    seleccionada BOOLEAN DEFAULT 0, -- 1 si fue aprobada por el docente
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. Sesiones de Flash Test
CREATE TABLE IF NOT EXISTS flash_tests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    estudiante_id INTEGER NOT NULL REFERENCES estudiantes(id) ON DELETE CASCADE,
    evaluacion_id INTEGER NOT NULL REFERENCES evaluaciones(id) ON DELETE CASCADE,
    token VARCHAR(64) UNIQUE NOT NULL,
    vigencia TIMESTAMP NOT NULL,
    respuestas TEXT DEFAULT '[]', -- JSON con respuestas enviadas
    puntaje REAL DEFAULT 0.0,
    tiempo_empleado INTEGER DEFAULT 0,
    estado VARCHAR(50) DEFAULT 'pending', -- 'pending' | 'in_progress' | 'completed' | 'expired'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9. Citas para Defensa Presencial
CREATE TABLE IF NOT EXISTS citas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    estudiante_id INTEGER NOT NULL REFERENCES estudiantes(id) ON DELETE CASCADE,
    docente_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    fecha DATE NOT NULL,
    bloque VARCHAR(50) NOT NULL,
    motivo VARCHAR(100) NOT NULL, -- 'score_bajo' | 'score_alto' | 'control_aleatorio'
    estado VARCHAR(50) DEFAULT 'programada', -- 'programada' | 'realizada' | 'cancelada'
    acuerdos TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 10. AuditLog (Registro inmutable de trazabilidad)
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    accion VARCHAR(100) NOT NULL,
    tabla_afectada VARCHAR(100) NOT NULL,
    registro_id INTEGER NOT NULL,
    datos_previos TEXT,
    datos_nuevos TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 5. Diseño de API RESTful y Protocolo WebSocket

### 5.1 Catálogo de Endpoints REST

#### Módulo de Cursos y Nóminas
- `POST /api/courses` $\rightarrow$ Crea una nueva asignatura. Payload: `{nombre, periodo, anio, parametros}`.
- `GET /api/courses` $\rightarrow$ Lista asignaturas asociadas al docente autenticado.
- `POST /api/students/upload-csv` $\rightarrow$ Ingesta masiva de alumnos. `FormData(file: .csv, course_id: int)`. Retorna `{creados: int, ignorados: int, total: int}`.
- `GET /api/students?course_id={id}` $\rightarrow$ Retorna listado de estudiantes del curso.

#### Módulo de Informes y Materiales
- `POST /api/materials/upload` $\rightarrow$ Sube syllabus/guía PDF. Lo convierte a Markdown y guarda en `materiales`.
- `POST /api/reports/bulk-upload` $\rightarrow$ Sube lote de PDFs de alumnos. Asocia automáticamente por nombre de archivo o crea registros `trabajos` en estado `uploaded`.
- `POST /api/reports/{id}/analyze` $\rightarrow$ Dispara worker asíncrono que extrae el Markdown, consulta a Claude 3.5 Sonnet y crea la `evaluacion` y el pool de 20 `preguntas`.
- `GET /api/reports/{id}/questions` $\rightarrow$ Retorna las 20 preguntas generadas para el informe.
- `PUT /api/reports/{id}/questions` $\rightarrow$ Guarda las ediciones del docente y marca las 10 preguntas seleccionadas (`seleccionada = true`).
- `POST /api/flash/send-token` $\rightarrow$ Genera token UUIDv4 (vigencia 48h), registra `flash_tests` y envía correo con `aiosmtplib`.

#### Módulo de Cierre y Auditoría
- `GET /api/reports/course/{course_id}/summary` $\rightarrow$ Retorna tabla consolidada con nota preliminar, % IA, score flash, estado y citación.
- `POST /api/appointments/close` $\rightarrow$ Registra acuerdos de defensa presencial, actualiza `evaluaciones.nota_final` y genera registro inmutable en `audit_logs`.
- `GET /api/dashboard/audit-logs` $\rightarrow$ Lista historial de auditoría para trazabilidad.

---

### 5.2 Protocolo WebSocket del Flash Test (`/ws/flash/{token}`)

```mermaid
sequenceDiagram
    autonumber
    actor Alumno as Estudiante (/flash/[token])
    participant WS as WebSocket Server (FastAPI)
    participant DB as Base de Datos (SQLite/Postgres)
    participant Mail as Gmail SMTP

    Alumno->>WS: Conexión WebSocket ?token=UUIDv4
    WS->>DB: Validar token y vigencia (48h)
    DB-->>WS: Token válido (estado: pending)
    WS->>DB: Actualizar estado a in_progress
    WS-->>Alumno: Evento question_start (Pregunta 1/10, 60s)
    
    loop Cada una de las 10 preguntas
        Note over Alumno,WS: Reloj 60s en Frontend y Backend
        alt Alumno responde antes de 60s
            Alumno->>WS: Evento submit_answer {index: 1, option: "B"}
        else Expira temporizador (60s)
            WS->>WS: Penalizar timeout (opción: null)
        end
        WS->>DB: Guardar respuesta parcial
        WS-->>Alumno: Evento question_start (Siguiente pregunta)
    end

    WS->>DB: Calcular score final y estado = completed
    WS->>WS: Evaluar regla de ruteo (<50%, >=95% o 10% azar)
    opt Califica para revisión
        WS->>DB: Crear cita en primer bloque disponible
        WS->>Mail: Despachar correo de citación presencial
    end
    WS-->>Alumno: Evento test_completed {score: 80.0, routed: false}
```

---

## 6. Motor de IA, Extracción Documental y Mock Engine

### 6.1 Extracción Semántica (`pymupdf4llm`)
```python
import pymupdf4llm

def extract_pdf_to_markdown(pdf_path: str) -> str:
    """Extrae el texto preservando encabezados Markdown (#, ##), tablas y listas."""
    md_text = pymupdf4llm.to_markdown(pdf_path)
    return md_text
```

### 6.2 Prompt Engineering para Evaluación Contextualizada
El prompt inyecta tres fuentes de datos:
1. **Pauta / Rúbrica definida por el profesor.**
2. **Material de cátedra / Syllabus convertido a Markdown.**
3. **Informe entregado por el estudiante.**

```
Eres un evaluador académico universitario riguroso y pedagógicamente constructivo.
PAUTA DE EVALUACIÓN:
{pauta_docente}

MATERIAL Y GUÍAS DEL CURSO:
{material_markdown}

INFORME DEL ESTUDIANTE:
{informe_markdown}

TAREA:
Evalúa el trabajo del estudiante contrastándolo rigurosamente contra la pauta y el material.
Devuelve EXCLUSIVAMENTE un JSON válido con la siguiente estructura:
{
  "nota_preliminar": 5.8,
  "porcentaje_logro": "75%",
  "deteccion_ia": {
    "porcentaje": "30%",
    "nivel_confianza": "medio",
    "secciones_sospechosas": ["Sección 2.1"],
    "justificacion": "Vocabulario excesivamente genérico sin citas a los autores de la guía."
  },
  "feedback": {
    "fortalezas": ["..."],
    "debilidades": ["..."],
    "recomendaciones": ["..."]
  },
  "desglose_rubrica": {
    "contenido": "80%",
    "estructura": "70%",
    "metodologia": "75%"
  }
}
```

### 6.3 Mock Engine de Contingencia (Fallback offline)
Si la llamada a la API de Anthropic falla (timeout $>30$s o sin conexión a internet), el sistema conmuta automáticamente a `MockEngine`, el cual:
- Analiza heurísticamente la longitud del Markdown, densidad de vocabulario y estructura de secciones.
- Genera una nota preliminar simulada coherente y un pool de 20 preguntas basadas en las palabras clave del informe.
- Permite que el docente continúe su flujo de trabajo sin bloqueos.

---

## 7. Arquitectura Frontend y Componentes Clave

### 7.1 Panel Docente 9-en-1 (`/teacher/dashboard`)
Integra todas las operaciones en pestañas accesibles:
1. **Asignaturas:** Crear y administrar cursos.
2. **Estudiantes (CSV):** Subir nómina con feedback visual de duplicados.
3. **Parámetros & Rúbrica:** Configurar rigor (`strict`, `medium`, `lax`), umbrales de citación y pauta libre.
4. **Materiales:** Cargar syllabus y guías docentes.
5. **Carga Masiva de Informes:** Subir PDFs con indicador de estado (`uploaded`, `processing`, `done`).
6. **Pool de Preguntas:** Editor interactivo para revisar las 20 preguntas generadas y seleccionar 10.
7. **Resultados y Notas:** Tabla filtrable con notas de IA, detección de IA y score flash.
8. **Agenda de Citas:** Gestión de defensas presenciales y registro de acuerdos.
9. **Disponibilidad:** Bloques horarios semanales del docente para citas.

### 7.2 Interfaz Flash Test (`/flash/[token]`)
- Sin header de navegación ni distracciones.
- Bloqueo de atajos de teclado para copiar/pegar.
- Reloj circular animado de 60 segundos por pregunta.
- Barra de progreso interactiva (1 al 10).
- Reconexión transparente: si se pierde conexión, el servidor conserva el tiempo restante de la pregunta.

---

## 8. Reglas de Negocio y Algoritmo de Ruteo

```python
def process_flash_test_result(score: float, course_params: dict) -> dict:
    """
    Determina si un estudiante debe ser convocado a defensa oral presencial.
    """
    umbral_bajo = course_params.get("umbral_bajo", 50.0)
    umbral_alto = course_params.get("umbral_alto", 95.0)
    pct_aleatorio = course_params.get("porcentaje_aleatorio", 10.0) / 100.0

    # Condición 1: Rendimiento deficiente en flash test (< 50%)
    if score < umbral_bajo:
        return {"review_required": True, "motivo": "score_bajo"}
    
    # Condición 2: Rendimiento perfecto sospechoso (>= 95%)
    if score >= umbral_alto:
        return {"review_required": True, "motivo": "score_alto"}
    
    # Condición 3: Control aleatorio estadístico de calidad (10%)
    import random
    if random.random() < pct_aleatorio:
        return {"review_required": True, "motivo": "control_aleatorio"}

    return {"review_required": False, "motivo": "aprobado_directo"}
```

---

## 9. Guía de Construcción Paso a Paso (De 0 a Producción)

### Paso 1: Configuración del Entorno y Repositorio
```bash
# 1. Clonar o iniciar repositorio
git init IntegriEval
cd IntegriEval

# 2. Inicializar Backend
cd backend
python -m venv .venv
# En Windows:
.venv\Scripts\activate
pip install -r requirements.txt

# 3. Inicializar Frontend
cd ../frontend
npm install
```

### Paso 2: Modelado de Base de Datos y Schemas
1. Crear `backend/app/models/models.py` con las 10 entidades SQLAlchemy.
2. Crear `backend/app/schemas/schemas.py` con los validadores Pydantic.
3. Crear `backend/app/core/database.py` inicializando SQLite/Postgres.

### Paso 3: Endpoints Base de Cursos y Nóminas CSV (Sprint 1 — US-01, US-02)
1. Implementar `backend/app/api/courses.py` con CRUD de asignaturas.
2. Implementar `backend/app/api/students.py` con parser CSV que soporte UTF-8 y UTF-8 BOM, eliminando duplicados por `(asignatura_id, correo)`.

### Paso 4: Ingesta Masiva y Extracción a Markdown (Sprint 1 — US-03, US-04)
1. Crear `backend/app/services/extractor.py` usando `pymupdf4llm`.
2. Implementar `backend/app/api/materials.py` y `backend/app/api/reports.py` para subida en lote de archivos PDF.

### Paso 5: Motor de Inferencia IA y Mock Engine (Sprint 2 — US-05, US-06)
1. Crear `backend/app/services/ai_service.py` con cliente Anthropic Claude 3.5 Sonnet.
2. Implementar `MockEngine` con analizador heurístico de texto para fallback offline.
3. Crear endpoint `POST /api/reports/{id}/analyze` con worker asíncrono en FastAPI (`BackgroundTasks`).

### Paso 6: Pool de Preguntas y Despacho SMTP (Sprint 3 — US-07, US-08)
1. Implementar generación de 20 preguntas en `ai_service.py`.
2. Crear `backend/app/services/email_service.py` con `aiosmtplib` y plantilla HTML con botón tokenizado.
3. Implementar endpoints `GET` y `PUT` en `reports.py` para editar reactivos y seleccionar 10.

### Paso 7: Sala WebSocket de Flash Test (Sprint 3 — US-09)
1. Crear endpoint WebSocket en `backend/app/api/flash.py` con temporizador server-side de 60 segundos por pregunta.
2. Construir en Next.js la vista `frontend/src/app/flash/[token]/page.tsx` con conexión WebSocket bidireccional y reloj animado.

### Paso 8: Ruteo Automático, Citas y AuditLog (Sprint 4 — US-10, US-11)
1. Implementar `backend/app/services/scheduling.py` con las reglas de ruteo ($<50\%$, $\ge 95\%$, $10\%$ aleatorio).
2. Construir en `backend/app/api/appointments.py` el cierre de defensas presenciales con actualización de nota final.
3. Implementar registro automático en `audit_logs` para cada modificación manual de calificaciones.

---

## 10. Configuración del Entorno y Variables (.env)

### `backend/.env`
```env
ENVIRONMENT=development
PORT=8000
DATABASE_URL=sqlite:///./integrieval.db
# Para PostgreSQL: postgresql://postgres:password@localhost:5432/integrieval

# LLM API
ANTHROPIC_API_KEY=sk-ant-api03-...
AI_MODEL=claude-3-5-sonnet-20241022
USE_MOCK_AI=false

# Gmail SMTP (App Password)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=notificaciones.integrieval@gmail.com
SMTP_PASSWORD=abcd_efgh_ijkl_mnop
FRONTEND_URL=http://localhost:3000
```

### `frontend/.env.local`
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

---

## 11. Estrategia de Testing y Verificación

1. **Tests Unitarios de Backend (Pytest):**
   - `test_csv_parser`: Valida nóminas con emails inválidos y caracteres especiales.
   - `test_extractor`: Valida extracción Markdown sobre PDFs con tablas y fórmulas.
   - `test_ai_json`: Valida que el output del LLM cumpla estrictamente el schema JSON.
2. **Tests de WebSocket y Concurrencia:**
   - Script de prueba simulando 100 clientes concurrentes respondiendo en intervalos de 5 a 30 segundos con latencia $\le 50\text{ms}$.
3. **Tests de Fallback:**
   - Simular desconexión de internet y verificar activación inmediata del Mock Engine sin error 500.

---

## 12. Checklist de Prelanzamiento

### 🔴 P0: Bloqueantes
- [x] **P0-1:** Hashing seguro `bcrypt` en contraseñas de docentes.
- [x] **P0-2:** Expiración estricta de 48h en tokens UUIDv4 e invalidación tras el primer uso.
- [x] **P0-3:** Temporizador de 60s validado en el servidor para evitar fraudes en el cliente.
- [x] **P0-4:** Registro inmutable en `AuditLog` para todo cambio manual de notas.

### 🟡 P1: Importantes
- [x] **P1-1:** Activación automática del Mock Engine ante cortes de API de IA.
- [x] **P1-2:** Reconexión de WebSocket ($\le 120$s) preservando el tiempo restante de la pregunta.
- [x] **P1-3:** Sanitización de CSV para prevenir inyecciones de fórmulas.
- [x] **P1-4:** Accesibilidad WCAG 2.1 nivel AA y modo oscuro.

### 🟢 P2: Deseables
- [ ] **P2-1:** Integración LTI con LMS Moodle/Canvas.
- [ ] **P2-2:** Exportación de actas finales en formato Excel/PDF para secretaría académica.

---

## 13. Anexo: Estructura JSON de Evaluación (RF-007)

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
