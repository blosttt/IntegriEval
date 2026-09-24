# Blueprint de Arquitectura de Software: IntegriEval
**Plataforma Semi-Automatizada de Evaluación de Integridad Académica, Detección de IA y Verificación Oral Flash**  
*Generado bajo el estándar metodológico de El Arquitecto Innovares*  
**Versión:** 1.0.0 (Septiembre 2026)  
**Autores:** Sebastian Cisternas, Benjamin Sobarzo  
**Proyecto Base:** Trabajo de Título (INFO1197) — Ingeniería Civil Informática  

---

## 1. Visión del Proyecto

### 1.1 Qué es y Para Quién
**IntegriEval** es una plataforma web orientada a la educación superior diseñada para asistir a docentes y ayudantes universitarios en la evaluación de trabajos académicos (PDF/DOCX), la detección contextualizada de contenido sintetizado por Inteligencia Artificial y la verificación del aprendizaje real del estudiante mediante evaluaciones orales y pruebas *Flash* cronometradas en tiempo real.

### 1.2 Problema Central que Resuelve
1. **Ineficacia de los Detectores Estadísticos de 'Caja Negra':** Herramientas como Turnitin AI y GPTZero presentan elevadas tasas de falsos positivos y negativos al basarse únicamente en perplejidad y *burstiness*. Acusar disciplinariamente a un alumno sin pruebas tangibles genera incertidumbre ética y jurídica.
2. **Inviabilidad Logística de la Interrogación Universal:** En cursos masivos (60 a 200 estudiantes), es físicamente imposible examinar oralmente al 100% de la nómina por limitaciones horarias de atención docente.
3. **Sobrecarga en la Corrección Mecánica:** Los docentes dedican hasta 25 horas semanales a cotejar informes contra pautas y materiales de cátedra.

### 1.3 Métricas de Éxito
- **Tasa de conversión documental $\ge 98\%$** en PDFs de informes y syllabus a Markdown estructurado.
- **Tiempo de respuesta $\le 15\text{s}$** por informe para análisis de rúbrica y detección contextual mediante workers asíncronos.
- **Reducción de $\ge 60\%$** en el tiempo invertido por el docente en revisión mecánica y citación a oficina.
- **$100\%$ de confirmación explícita docente** sobre las notas finales antes de su publicación (*Human-in-the-Loop*).
- **Cero fricción de autenticación** para estudiantes mediante enlaces tokenizados de un solo uso despachados por correo electrónico.

---

## 2. Tech Stack y Justificación Técnica

| Capa | Tecnología Seleccionada | Justificación Técnica y Operativa |
|---|---|---|
| **Frontend Framework** | **Next.js 15 (App Router)** + TypeScript | Renderizado híbrido (SSR para vistas públicas, CSR reactivo para paneles), tipado estricto y alto rendimiento. |
| **Estilos & UI** | **Tailwind CSS v4** + **shadcn/ui** | Consistencia visual, accesibilidad WCAG 2.1 AA, tema oscuro de alto contraste y componentes reutilizables sin sobrecarga. |
| **Backend API** | **FastAPI (Python 3.14)** + Pydantic v2 | Alto rendimiento asíncrono, compatibilidad nativa con Starlette WebSockets para exámenes en vivo y validación estricta de schemas. |
| **Base de Datos & ORM** | **PostgreSQL** (Supabase / Self-hosted NAS) / **SQLite** local + **SQLAlchemy 2.0** | Soporte transaccional ACID, esquemas relacionales robustos y capacidad de migración fluida entre local y cloud. |
| **Extracción Semántica** | **`pymupdf4llm`** (MuPDF) | Extracción de PDFs/DOCX a Markdown estructurado preservando jerarquía de títulos, tablas y listas, reduciendo un 40% el ruido léxico para el LLM. |
| **Motor de Inferencia IA** | **Claude 3.5 Sonnet** (Anthropic API) + **Mock Engine** (Fallback) | Razonamiento contextual superior para análisis de rúbricas; motor heurístico local para garantizar continuidad operacional sin red. |
| **Tiempo Real (Flash Test)** | **WebSockets bidireccionales** (Starlette/FastAPI) | Comunicación bidireccional con latencia $\le 50\text{ms}$ y temporización server-side estricta de 60 segundos por reactivo. |
| **Servicio de Correo** | **Gmail SMTP Asíncrono** (`aiosmtplib`) / **Resend** | Despacho seguro de tokens UUIDv4 a costo cero para el MVP institucional con soporte para hasta 500 envíos diarios. |
| **Hosting & Infraestructura** | **Vercel** (Frontend) + **GMKtec M5 / Mac mini M4** + **Cloudflare Tunnel** | Arquitectura híbrida: UI global en edge de Vercel y API/Workers persistentes auto-hospedados con URL segura HTTPS fija. |

---

## 3. Estructura de Directorios del Proyecto

```tree
IntegriEval/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── appointments.py      # Agendamiento y cierre de defensas orales
│   │   │   ├── courses.py           # CRUD de asignaturas y parámetros de rúbrica
│   │   │   ├── dashboard.py         # Métricas globales y AuditLog
│   │   │   ├── evaluations.py       # Configuración de evaluaciones y rigor
│   │   │   ├── flash.py             # Validación de tokens y WebSocket de examen en vivo
│   │   │   ├── materials.py         # Carga de syllabus y guías de cátedra
│   │   │   ├── reports.py           # Ingesta en lote de PDFs y pool de preguntas
│   │   │   └── students.py          # Parser CSV de nóminas y gestión de alumnos
│   │   ├── core/
│   │   │   ├── config.py            # Variables de entorno y settings Pydantic
│   │   │   ├── database.py          # Engine SQLAlchemy y session maker
│   │   │   └── security.py          # Hashing bcrypt y validación de tokens
│   │   ├── models/
│   │   │   └── models.py            # Entidades SQLAlchemy (Usuario, Estudiante, etc.)
│   │   ├── schemas/
│   │   │   └── schemas.py           # Modelos Pydantic de validación request/response
│   │   ├── services/
│   │   │   ├── ai_service.py        # Integración Anthropic Claude 3.5 y Mock Engine
│   │   │   ├── email_service.py     # Despacho SMTP asíncrono con plantillas HTML
│   │   │   ├── extractor.py         # pymupdf4llm para conversión PDF -> Markdown
│   │   │   └── scheduling.py       # Algoritmo de ruteo y asignación de citas
│   │   └── main.py                  # Entrypoint FastAPI, CORS y registro de routers
│   ├── tests/
│   │   ├── test_ai.py
│   │   ├── test_api.py
│   │   └── test_websocket.py
│   ├── pyproject.toml
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx           # Root layout con providers
│   │   │   ├── page.tsx             # Landing institucional informativa
│   │   │   ├── flash/
│   │   │   │   └── [token]/
│   │   │   │       └── page.tsx     # Sala de examen Flash en tiempo real (WebSocket)
│   │   │   └── teacher/
│   │   │       ├── dashboard/
│   │   │       │   └── page.tsx     # Panel 9-en-1 del profesor
│   │   │       └── login/
│   │   │           └── page.tsx     # Autenticación docente
│   │   ├── components/
│   │   │   ├── ui/                  # Componentes shadcn (Button, Dialog, Badge, etc.)
│   │   │   ├── Dropzone.tsx         # Subida masiva drag & drop
│   │   │   ├── QuestionEditor.tsx   # Editor de reactivos y selector de 10 preguntas
│   │   │   ├── FlashTimer.tsx       # Temporizador circular SVG de 60s
│   │   │   └── AuditLogTable.tsx    # Tabla inmutable de eventos
│   │   ├── lib/
│   │   │   ├── api.ts               # Cliente API tipado con Axios / Fetch
│   │   │   └── utils.ts
│   │   └── types/
│   │       └── index.ts             # Tipos TypeScript compartidos
│   ├── package.json
│   ├── tailwind.config.ts
│   └── tsconfig.json
├── docs/
│   ├── blueprint_integrieval.pdf
│   ├── documento_ingenieria_integrieval.docx
│   └── documento_ingenieria_integrieval.tex
├── output/
│   └── integrieval-blueprint.md
└── CLAUDE.md                        # Guía de construcción y reglas para Claude Code
```

---

## 4. Modelo de Datos y Esquema SQL

### 4.1 Entidades y Relaciones
```sql
-- Esquema PostgreSQL / Supabase para IntegriEval

CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    correo VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(50) DEFAULT 'docente', -- 'docente' | 'admin' | 'ayudante'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS asignaturas (
    id SERIAL PRIMARY KEY,
    docente_id INT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    nombre VARCHAR(200) NOT NULL,
    periodo VARCHAR(50) NOT NULL,
    anio INT NOT NULL,
    parametros JSONB DEFAULT '{"rigor": "medium", "pool_size": 20, "flash_size": 10, "umbral_bajo": 50, "umbral_alto": 95, "porcentaje_aleatorio": 10}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS estudiantes (
    id SERIAL PRIMARY KEY,
    asignatura_id INT NOT NULL REFERENCES asignaturas(id) ON DELETE CASCADE,
    nombre VARCHAR(150) NOT NULL,
    correo VARCHAR(150) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_estudiante_asignatura UNIQUE (asignatura_id, correo)
);

CREATE TABLE IF NOT EXISTS materiales (
    id SERIAL PRIMARY KEY,
    asignatura_id INT NOT NULL REFERENCES asignaturas(id) ON DELETE CASCADE,
    nombre VARCHAR(200) NOT NULL,
    tipo VARCHAR(50) NOT NULL, -- 'syllabus' | 'guia' | 'rubrica'
    markdown_content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trabajos (
    id SERIAL PRIMARY KEY,
    estudiante_id INT NOT NULL REFERENCES estudiantes(id) ON DELETE CASCADE,
    pdf_path VARCHAR(500) NOT NULL,
    markdown_content TEXT NOT NULL,
    estado VARCHAR(50) DEFAULT 'uploaded', -- 'uploaded' | 'processing' | 'done' | 'error'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS evaluaciones (
    id SERIAL PRIMARY KEY,
    trabajo_id INT UNIQUE NOT NULL REFERENCES trabajos(id) ON DELETE CASCADE,
    nota_preliminar NUMERIC(3, 1), -- Escala 1.0 a 7.0
    porcentaje_ia INT DEFAULT 0,   -- 0 a 100%
    feedback JSONB DEFAULT '{}'::jsonb,
    desglose_rubrica JSONB DEFAULT '{}'::jsonb,
    nota_final NUMERIC(3, 1),
    estado_cierre VARCHAR(50) DEFAULT 'pendiente', -- 'pendiente' | 'confirmada' | 'revisada_oral'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS preguntas (
    id SERIAL PRIMARY KEY,
    evaluacion_id INT NOT NULL REFERENCES evaluaciones(id) ON DELETE CASCADE,
    enunciado TEXT NOT NULL,
    tipo VARCHAR(50) DEFAULT 'multiple_choice', -- 'multiple_choice' | 'true_false'
    alternativas JSONB NOT NULL,
    respuesta_correcta VARCHAR(10) NOT NULL,
    explicacion TEXT,
    seleccionada BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS flash_tests (
    id SERIAL PRIMARY KEY,
    estudiante_id INT NOT NULL REFERENCES estudiantes(id) ON DELETE CASCADE,
    evaluacion_id INT NOT NULL REFERENCES evaluaciones(id) ON DELETE CASCADE,
    token VARCHAR(64) UNIQUE NOT NULL,
    vigencia TIMESTAMP WITH TIME ZONE NOT NULL,
    respuestas JSONB DEFAULT '[]'::jsonb,
    puntaje NUMERIC(5, 2) DEFAULT 0.0,
    tiempo_empleado INT DEFAULT 0,
    estado VARCHAR(50) DEFAULT 'pending', -- 'pending' | 'in_progress' | 'completed' | 'expired'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS citas (
    id SERIAL PRIMARY KEY,
    estudiante_id INT NOT NULL REFERENCES estudiantes(id) ON DELETE CASCADE,
    docente_id INT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    fecha DATE NOT NULL,
    bloque VARCHAR(50) NOT NULL,
    motivo VARCHAR(100) NOT NULL, -- 'score_bajo' | 'score_alto' | 'control_aleatorio'
    estado VARCHAR(50) DEFAULT 'programada', -- 'programada' | 'realizada' | 'cancelada'
    acuerdos TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    usuario_id INT REFERENCES usuarios(id) ON DELETE SET NULL,
    accion VARCHAR(100) NOT NULL,
    tabla_afectada VARCHAR(100) NOT NULL,
    registro_id INT NOT NULL,
    datos_previos JSONB,
    datos_nuevos JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

---

## 5. Diseño de API RESTful y WebSockets

### 5.1 Endpoints Principales

| Método | Ruta | Descripción | Payload / Parámetros | Respuesta |
|---|---|---|---|---|
| `POST` | `/api/auth/login` | Login docente y emisión JWT | `{correo, password}` | `{token, user}` |
| `POST` | `/api/students/upload-csv` | Importación masiva de alumnos | `FormData(file: .csv, course_id)` | `{creados, ignorados, total}` |
| `POST` | `/api/reports/bulk-upload` | Subida en lote de informes PDF | `FormData(files: [.pdf], course_id)` | `{procesados: [{id, name, status}]}` |
| `POST` | `/api/reports/{id}/analyze` | Dispara worker de análisis IA | Ninguno | `{message: "Encolado", status: "processing"}` |
| `GET` | `/api/reports/{id}/questions` | Obtiene pool de 20 preguntas | Ninguno | `{questions: [QuestionSchema]}` |
| `PUT` | `/api/reports/{id}/questions` | Edita o aprueba set de 10 | `{selected_ids: [int], custom: [...]}` | `{status: "approved", count: 10}` |
| `POST` | `/api/flash/send-token` | Despacha email con enlace | `{report_id: int}` | `{sent: true, token, expires_at}` |
| `GET` | `/api/flash/validate/{token}` | Valida vigencia y estado | Token en ruta | `{valid: true, student, test_status}` |
| `WS` | `/ws/flash/{token}` | Sala interactiva del Flash Test | Query `?token=...` | Flujo de preguntas, temporizador y envío de respuestas |
| `POST` | `/api/appointments/close` | Cierra cita y ajusta nota final | `{appointment_id, nota_final, acuerdos}` | `{status: "closed", audit_id}` |

### 5.2 Protocolo WebSocket del Flash Test (`/ws/flash/{token}`)

```json
// Evento 1: Servidor -> Cliente (Inicio de pregunta)
{
  "type": "question_start",
  "data": {
    "index": 1,
    "total": 10,
    "enunciado": "¿Qué patrón arquitectónico se implementó en el módulo de autenticación?",
    "alternativas": {
      "A": "Session-based con cookies seguras",
      "B": "Tokens UUIDv4 efímeros con expiración temporal",
      "C": "OAuth 2.0 PKCE descentralizado",
      "D": "Basic Auth sobre HTTPS"
    },
    "duration_seconds": 60
  }
}

// Evento 2: Cliente -> Servidor (Respuesta del alumno)
{
  "type": "submit_answer",
  "data": {
    "question_index": 1,
    "selected_option": "B",
    "client_timestamp": "2026-09-24T14:30:15Z"
  }
}

// Evento 3: Servidor -> Cliente (Resultado y cierre de sesión)
{
  "type": "test_completed",
  "data": {
    "score": 80.0,
    "correct_count": 8,
    "total_questions": 10,
    "routed_to_interview": false,
    "message": "Evaluación completada con éxito. Resultados registrados."
  }
}
```

---

## 6. Arquitectura Frontend

- **Server Components (SSR):** Landing institucional, vistas estáticas informativas y validación preliminar de rutas protegidas.
- **Client Components (`'use client'`):**
  - `TeacherDashboard`: Panel integrado con 9 submódulos (Cursos, Estudiantes, Rúbrica, Materiales, Subida Masiva, Pool de Preguntas, Calificaciones, Agenda y Disponibilidad).
  - `FlashSessionRunner`: Componente de alta reactividad con WebSocket, animador de temporizador y bloqueo de copiar/pegar para asegurar integridad.
- **Gestión de Estado:** `Zustand` para el estado global del panel docente y `React Query / SWR` para revalidación asíncrona de reportes y estado de análisis en tiempo real.

---

## 7. Sistema de Diseño (Design System)

- **Paleta de Colores Corporativa:**
  - `Primary:` Azul Royal (`#2563EB`) — Identidad y acciones primarias.
  - `Secondary:` Índigo Profundo (`#4338CA`) — Encabezados y bloques estructurales.
  - `Dark BG:` Pizarra Oscura (`#0F172A`) — Fondo de alto contraste en modo oscuro.
  - `Success:` Verde Esmeralda (`#10B981`) — Calificaciones aprobatorias y validaciones exitosas.
  - `Warning / Alert:` Ámbar (`#F59E0B`) y Carmesí (`#EF4444`) — Detección crítica de IA y alertas de citas.
- **Tipografía:** `Inter` / `Geist Sans` para interfaces limpias y legibilidad en documentos densos; `JetBrains Mono` para visualización de fragmentos Markdown y JSON.

---

## 8. Autenticación y Control de Accesos (RBAC)

1. **Docentes y Ayudantes:**
   - Autenticación con correo y contraseña protegida con `bcrypt` (factor de costo $\ge 12$).
   - Tokens de sesión JWT firmados con algoritmo HS256 y expiración a 8 horas.
   - Restricción de permisos: Los ayudantes pueden cargar informes y ver notas preliminares; solo el docente titular puede modificar pautas y ratificar actas de cierre.
2. **Estudiantes (Paradigma Zero-Password):**
   - No requieren cuenta ni contraseña en la plataforma.
   - El acceso es conferido mediante tokens criptográficos UUIDv4 enviados exclusivamente a su correo oficial.
   - El token es de **un solo uso** e intransferible; expira a las 48 horas de su emisión o inmediatamente al completar la prueba.

---

## 9. Decisión de Hosting (Mapeo al Home Lab Innovares)

| Servicio / Componente | Destino de Hosting | Justificación Técnica y Operativa |
|---|---|---|
| **Frontend Next.js** | **Vercel** | Edge network global, renderizado serverless, certificados SSL automáticos y cero costo operativo para el front público. |
| **API REST & WebSockets (FastAPI)** | **GMKtec M5 Ultra** (Ryzen 7 7730U, 16GB) | Nodo headless 24/7 de alta eficiencia energética; maneja la concurrencia de WebSockets y workers de extracción asíncrona. |
| **Base de Datos & AuditLog** | **Supabase** (Postgres Cloud) / **NAS UGREEN DXP4800** (Docker Postgres) | Persistencia ACID transaccional; para pruebas de desarrollo local opera sobre SQLite embebido y escala a Postgres en el NAS/Supabase. |
| **Exposición Pública Segura** | **Cloudflare Tunnel** (Nombrado) | Expone el backend auto-hospedado en el GMKtec M5 con URL pública fija HTTPS sin abrir puertos en el router (`api.integrieval.innovares.cl`). |
| **Inferencia IA Pesada / Local** | **Estación i9-14900KF + RTX 5070** / **API Anthropic** | Permite ejecutar modelos locales (Llama 3 / Qwen 2.5 vía Ollama) con aceleración GPU para pruebas locales con costo cero de API. |

---

## 10. Orden de Construcción (Guía para Claude Code)

```
Paso 1: Setup del Repositorio y Entorno Base
  ├── 1.1 Configurar backend con FastAPI, Pydantic v2 y SQLAlchemy 2.0.
  └── 1.2 Configurar frontend Next.js 15 con Tailwind CSS v4 y shadcn/ui.

Paso 2: Modelado de Datos y Gestión Académica (Sprint 1)
  ├── 2.1 Crear modelos: Usuario, Asignatura, Estudiante, Material, Trabajo, Evaluacion.
  ├── 2.2 Implementar parser de nóminas CSV UTF-8 BOM con deduplicación.
  └── 2.3 Implementar carga masiva de PDFs y extracción a Markdown con pymupdf4llm.

Paso 3: Motor de Análisis Contextual e Inferencia IA (Sprint 2)
  ├── 3.1 Diseñar prompts que inyecten pauta + syllabus en contexto de Claude 3.5 Sonnet.
  ├── 3.2 Implementar worker asíncrono en FastAPI con almacenamiento de nota, feedback y % IA.
  └── 3.3 Desarrollar Mock Engine con generador heurístico para fallback offline.

Paso 4: Pool de Reactivos y Despacho Tokenizado (Sprint 3)
  ├── 4.1 Generar pool de 20 preguntas basadas exclusivamente en el texto del informe.
  ├── 4.2 Construir editor interactivo en Next.js con validación obligatoria de 10 reactivos.
  └── 4.3 Implementar servicio Gmail SMTP asíncrono con generación de tokens UUIDv4 (48h).

Paso 5: Sala de Examen en Tiempo Real y Ruteo Automático (Sprint 4)
  ├── 5.1 Construir servidor WebSocket con cronómetro estricto de 60s por pregunta.
  ├── 5.2 Implementar frontend de examen /flash/[token] con manejo de reconexión.
  └── 5.3 Programar lógica de ruteo automático: citación a cita si score < 50%, >= 95% o 10% aleatorio.

Paso 6: Panel de Cierre, Auditoría y Validaciones Finales (Sprint 4)
  ├── 6.1 Construir panel de actas finales con confirmación explícita docente de notas.
  ├── 6.2 Implementar AuditLog inmutable en base de datos.
  └── 6.3 Ejecutar suite de pruebas unitarias, de carga (100 WS) y generar documentación técnica.
```

---

## 11. Setup del Entorno y Variables de Configuración

### Backend (`backend/.env`)
```bash
# Servidor & Entorno
ENVIRONMENT=development
PORT=8000
SECRET_KEY=clave_secreta_jwt_para_firmar_tokens_docentes_super_segura
DATABASE_URL=sqlite:///./integrieval.db
# Para Postgres: postgresql://postgres:password@localhost:5432/integrieval

# Proveedor de IA
ANTHROPIC_API_KEY=sk-ant-api03-...
AI_MODEL=claude-3-5-sonnet-20241022
USE_MOCK_AI=false

# Servicio de Correo SMTP (Gmail App Password)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=notificaciones.integrieval@gmail.com
SMTP_PASSWORD=xxxx_xxxx_xxxx_xxxx
FRONTEND_URL=http://localhost:3000
```

### Frontend (`frontend/.env.local`)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

---

## 12. Dependencias Principales

### Backend (`requirements.txt`)
- `fastapi>=0.115.0`: Core de API web asíncrona.
- `uvicorn[standard]>=0.30.0`: Servidor ASGI de alto rendimiento.
- `sqlalchemy>=2.0.0`: ORM relacional y capa de abstracción de base de datos.
- `pydantic>=2.8.0`: Validación y tipado de datos.
- `pymupdf4llm>=0.0.17`: Extracción semántica de documentos a Markdown estructurado.
- `anthropic>=0.34.0`: SDK oficial para inferencia con modelos Claude.
- `aiosmtplib>=3.0.0`: Cliente SMTP asíncrono para envío de correos sin bloqueo de red.
- `python-jose[cryptography]`: Generación y validación de tokens JWT.
- `passlib[bcrypt]`: Hashing de contraseñas de docentes.
- `python-docx` y `reportlab`: Generación programática de informes en Word y PDF.

### Frontend (`package.json`)
- `next@15.0.0`: Framework React con App Router y Server Actions.
- `react@19.0.0` y `react-dom@19.0.0`: Biblioteca de interfaz de usuario.
- `tailwindcss@4.0.0`: Utilidades CSS atómicas para estilizado.
- `lucide-react`: Iconografía SVG modular.
- `framer-motion`: Animaciones fluidas para transiciones y temporizadores.
- `canvas-confetti`: Retroalimentación visual al finalizar el examen.

---

## 13. Estrategia de Testing y Verificación

1. **Pruebas Unitarias & de Integración (Pytest):**
   - Validación del parser CSV ante archivos con codificación UTF-8, UTF-8 BOM y delimitadores `;` o `,`.
   - Test del extractor `pymupdf4llm` frente a PDFs con encabezados jerárquicos y tablas complejas.
   - Test de generación de reactivos asegurando que contengan alternativas A, B, C y D válidas.
2. **Pruebas de Carga y Concurrencia (WebSockets):**
   - Script de prueba concurrente simulando 100 estudiantes rindiendo la prueba flash en simultáneo con latencia $< 50\text{ms}$.
3. **Pruebas de Resiliencia y Fallback:**
   - Corte forzado de API de Anthropic para validar activación instantánea del `MockEngine` sin degradar el flujo docente.

---

## 14. Checklist de Prelanzamiento (Estándar Innovares P0 / P1 / P2)

### 🔴 P0: Bloqueantes para Puesta en Marcha
- [x] **P0-1:** Hashing seguro `bcrypt` implementado para todos los accesos docentes y administrativos.
- [x] **P0-2:** Expiración estricta de 48 horas y consumo de un solo uso para todos los tokens de Flash Test.
- [x] **P0-3:** Validación server-side del temporizador de 60 segundos por pregunta para prevenir manipulaciones en el cliente.
- [x] **P0-4:** Persistencia inmutable en `AuditLog` para cualquier modificación manual de notas.

### 🟡 P1: Requerimientos Importantes de Operación
- [x] **P1-1:** Activación automática del Mock Engine ante caídas de la API de Anthropic.
- [x] **P1-2:** Reconexión automática de WebSocket preservando el cronómetro activo ante pérdidas de señal de internet.
- [x] **P1-3:** Sanitización estricta de archivos CSV subidos para prevenir inyecciones de fórmulas (*CSV Formula Injection*).
- [x] **P1-4:** Diseño responsivo accesible según pautas WCAG 2.1 nivel AA.

### 🟢 P2: Mejoras Deseables de Continuidad
- [ ] **P2-1:** Integración directa mediante LTI con LMS Moodle / Canvas para sincronización directa de actas.
- [ ] **P2-2:** Exportación de reportes de auditoría en formato Excel / PDF para decanaturas.

---

## 15. Reglas No Negociables y CLAUDE.md del Proyecto

```markdown
# Reglas de Construcción para IntegriEval

1. **Paradigma Human-in-the-Loop:** La IA nunca publica una nota final de forma autónoma. El docente siempre mantiene el control y debe confirmar explícitamente el cierre de calificaciones.
2. **Cero Cuentas para Alumnos:** Los estudiantes NUNCA crean cuentas con contraseñas en la plataforma. Todo su ciclo de acceso es mediante enlace tokenizado de un solo uso despachado al correo institucional.
3. **Persistencia Inmutable:** Toda modificación de nota preliminar debe registrarse en la tabla `audit_logs` con el ID del usuario, fecha, valor anterior y justificación.
4. **Resiliencia ante Fallos de IA:** Ningún endpoint HTTP debe fallar si la API externa de IA está inaccesible; se debe activar de forma transparente el Mock Engine.
5. **Idioma:** Toda la interfaz de usuario, mensajes de error, plantillas de correo y documentación técnica deben estar en español neutro chileno.
```
