# IntegriEval 🎓⚡
### Sistema Semi-Automatizado de Evaluación de Integridad Académica, Detección de IA y Verificación Oral Flash

* **Trabajo de Título:** INFO1197 — Proyecto de Software y Título
* **Carrera:** Ingeniería Civil Informática
* **Fecha:** Septiembre 2026 — Versión 1.0
* **Equipo:** Sebastián Cisternas, Benjamín Sobarzo
* **Entorno:** Educación Superior / Cátedras Universitarias Masivas (60 a 200 alumnos)
* **Alcance:** Cursos masivos, Open-source, Costo cero, Sin fricción de login para estudiantes

---

## 1. Fundamentos Teóricos y Filosofía del Sistema

IntegriEval resuelve la inviabilidad de los detectores estadísticos tradicionales de 'caja negra' y la imposibilidad logística de interrogar a cientos de estudiantes de forma individual:
1. **Teoría de la Evaluación Auténtica (Grant Wiggins):** El foco no es perseguir estadísticamente el texto generado por IA, sino verificar si el estudiante *comprende, domina y es capaz de defender los conceptos* de su entrega.
2. **Principio de Supervisión Humana (Human-in-the-Loop):** La Inteligencia Artificial actúa estrictamente como asistente de lectura semántica y generador de preguntas. La autoridad pedagógica y la calificación final siempre recaen en el docente.
3. **Costo Cero y Cero Fricción:** 100% Open-source, despacho por Gmail SMTP gratuito (`aiosmtplib`), acceso de estudiantes sin cuenta ni contraseñas (únicamente mediante tokens seguros `UUIDv4`), y motor de contingencia heurístico offline (`Mock Engine`, RF-014).

---

## 2. Matriz de Trazabilidad del Blueprint

| Código | Requisito / Dimensión | Implementación en Código |
|---|---|---|
| **RF-001** | Crear y gestionar asignaturas | `backend/app/routers/asignaturas.py`, `models.py` (`Asignatura`) |
| **RF-002** | Ingesta masiva CSV estudiantes (detección duplicados) | `backend/app/routers/estudiantes.py` (delimitadores `,` y `;`) |
| **RF-003** | Configurar parámetros (prompt, rigor, pool 10-30, umbrales) | `backend/app/routers/asignaturas.py`, `schemas.py` (`ParametrosConfig`) |
| **RF-004** | Subir materiales de apoyo (Syllabus, guías, rúbricas) | `backend/app/routers/materiales.py`, `models.py` (`Material`) |
| **RF-005** | Carga masiva de PDFs de alumnos con asociación automática | `backend/app/routers/trabajos.py`, `services/pdf_service.py` |
| **RF-006** | Extracción semántica con títulos y tablas en Markdown | `backend/app/services/pdf_service.py` (`pymupdf4llm` y `fitz`) |
| **RF-007** | Evaluación con LLM / Estructura estandarizada **Anexo A** | `backend/app/services/mock_engine.py`, `services/llm_service.py` |
| **RF-008** | Generación de pool de preguntas IA (10 a 30 reactivos) | `backend/app/services/mock_engine.py` (`generate_mock_questions`) |
| **RF-009** | Edición y selección docente de preguntas ($N \le \text{Pool}$) | `backend/app/routers/preguntas.py`, `models.py` (`Pregunta`) |
| **RF-010** | Despacho Flash Test vía Gmail SMTP (Tokens UUIDv4 48h) | `backend/app/services/email_service.py`, `routers/flash_test.py` |
| **RF-011** | Interfaz Flash Test en tiempo real con WebSockets y timer | `frontend/templates/flashtest.html`, `backend/app/services/websocket_mgr.py` |
| **RF-012** | Panel de resultados docente con métricas y alertas | `frontend/templates/index.html`, `backend/app/routers/panel.py` |
| **RF-013** | Registro de defensas orales y ajuste de nota justificado | `backend/app/routers/panel.py` (`Cita`, `AuditLog`) |
| **RF-014** | Mock Engine de contingencia (análisis heurístico offline) | `backend/app/services/mock_engine.py` (TTR, burstiness, markers) |
| **RF-015** | Autenticación docente con bcrypt factor $\ge 12$ y JWT | `backend/app/auth.py`, `backend/app/routers/auth.py` |
| **RNF-001** | Concurrencia WebSocket latencia $\le 50$ms | `backend/app/services/websocket_mgr.py` |
| **RNF-002** | Tiempo análisis informe $\le 15$s CPU | Optimizado con `pymupdf4llm` y heurísticas lineales |
| **RNF-003** | Cierre de calificaciones en API $\le 200$ms | Endpoint `POST /api/asignaturas/{id}/cerrar-nota` directo |
| **RNF-004** | Tokens de acceso UUIDv4 (RFC 4122) | Generación nativa `uuid.uuid4()` con vigencia 48h |
| **RNF-005** | Contraseñas bcrypt factor $\ge 12$ | `bcrypt.gensalt(rounds=12)` en `backend/app/auth.py` |
| **RNF-006** | Control de acceso RBAC por asignatura | `check_course_access()` en `backend/app/auth.py` |
| **RNF-007** | Fallback a Mock Engine si timeout $> 30$s | Timeout configurado en `backend/app/services/llm_service.py` |
| **RNF-008** | Resiliencia de reconexión WebSocket $\le 120$s | Estado y respuestas preservados en `FlashTestSession` |
| **RNF-009** | Usabilidad WCAG 2.1 AA y modo oscuro/claro | Estilos en `frontend/static/css/style.css` |
| **RNF-013** | Cumplimiento Ley N° 21.719 (Privacidad y Auditoría Chile) | Tabla `audit_logs` inmutable, minimización de datos personales |
| **RN-001** | Token de acceso único válido por 48 horas | Validación en `routers/flash_test.py` |
| **RN-002** | Expiración de 60s/test con registro de respuestas parciales | Implementado en cliente y servidor |
| **RN-003** | Umbrales parametrizables en `Asignatura.parametros` | Almacenamiento JSON en `models.py` |
| **RN-004** | Nota editable con justificación obligatoria y auditoría | Campo obligatorio en cierre de nota (`flash_tests`) |

---

## 3. Estructura Exacta del Anexo A (RF-007)

El sistema genera y persiste evaluaciones que cumplen estrictamente con la estructura JSON del blueprint:
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

---

## 4. Estructura del Proyecto

```
integry/
├── backend/
│   ├── app/
│   │   ├── config.py              # Configuración y variables de entorno
│   │   ├── database.py            # Conexión SQLAlchemy y motor
│   │   ├── models.py              # Entidades completas del Blueprint (Usuario, Asignatura, etc.)
│   │   ├── schemas.py             # Esquemas Pydantic v2 (Anexo A estandarizado)
│   │   ├── auth.py                # Bcrypt factor 12, JWT y RBAC
│   │   ├── audit.py               # Auditoría inmutable de trazabilidad
│   │   ├── main.py                # Aplicación FastAPI, WebSockets y rutas
│   │   ├── services/
│   │   │   ├── pdf_service.py     # Extracción semántica con PyMuPDF / pymupdf4llm
│   │   │   ├── mock_engine.py     # Motor heurístico contingencia (RF-014)
│   │   │   ├── llm_service.py     # Integración Ollama / OpenAI / Claude / Mock
│   │   │   ├── email_service.py   # Despacho Gmail SMTP con aiosmtplib (RF-010)
│   │   │   └── websocket_mgr.py   # Gestor de conexiones y temporizador en tiempo real
│   │   └── routers/
│   │       ├── auth.py            # Login, registro y me
│   │       ├── asignaturas.py     # CRUD asignaturas y parámetros
│   │       ├── estudiantes.py     # Ingesta CSV con detección de duplicados
│   │       ├── materiales.py      # Carga de syllabus y rúbricas
│   │       ├── trabajos.py        # Subida individual/lote de PDFs y evaluación
│   │       ├── preguntas.py       # Edición y selección del pool de preguntas
│   │       ├── flash_test.py      # Despacho de tokens y WebSocket del test
│   │       ├── panel.py           # Dashboard docente, citas y cierre de nota
│   │       └── audit.py           # Consulta de auditoría inmutable
│   └── tests/
│       ├── conftest.py            # Fixtures de BD en memoria y cliente
│       ├── test_auth.py           # Tests de bcrypt, JWT y login
│       ├── test_csv_parser.py     # Tests de delimitadores y duplicados en CSV
│       ├── test_evaluation_engine.py # Tests de Anexo A y pool de preguntas
│       └── test_flash_test.py     # Test de flujo completo (despacho -> test -> cierre)
├── frontend/
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css          # Estilos accesibles WCAG 2.1 AA (Modo Oscuro/Claro)
│   │   └── js/
│   │       └── app.js             # Lógica reactiva SPA y WebSocket del docente
│   └── templates/
│       ├── index.html             # Portal del docente (Dashboard, Nómina, Materiales, etc.)
│       └── flashtest.html         # Interfaz en tiempo real para estudiantes (Sin login)
├── sample_data/
│   ├── nomina_estudiantes.csv     # Nómina de prueba con 10 estudiantes
│   ├── syllabus_info1197.md       # Syllabus de ejemplo para contexto
│   ├── carlos_alumno_informe_final.pdf # PDF de informe académico para pruebas
│   └── create_sample_pdf.py       # Generador de PDFs de prueba
├── .env.example                   # Plantilla de variables de entorno
├── .env                           # Variables de entorno locales
├── pytest.ini                     # Configuración de pytest
├── requirements.txt               # Dependencias del proyecto
└── run.py                         # Script de inicio rápido
```

---

## 5. Puesta en Marcha Rápida (Quickstart)

### Requisitos Previos
* Python 3.10+ (probado y verificado en Python 3.13)
* Navegador web moderno

### Instalación y Ejecución

1. **Activar el entorno virtual e instalar dependencias:**
   ```powershell
   # En Windows PowerShell
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Ejecutar la suite de pruebas automatizadas:**
   ```powershell
   .venv\Scripts\pytest -v
   ```
   *Todos los 9 tests unitarios e integrados pasan exitosamente.*

3. **Iniciar el servidor:**
   ```powershell
   .venv\Scripts\python run.py
   ```

4. **Acceder a la aplicación:**
   * **Portal del Docente:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
     * **Credenciales por defecto:** `docente@universidad.cl` / `Docente123!`
   * **Documentación Interactiva Swagger / OpenAPI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 6. Flujo de Trabajo Demostrativo

1. **Gestión de Nómina (RF-002):**
   * Vaya a la pestaña **👥 Nómina (CSV)**.
   * Arrastre el archivo `sample_data/nomina_estudiantes.csv` para cargar los alumnos del curso.
2. **Contexto Pedagógico (RF-004):**
   * Vaya a **📚 Materiales de Apoyo**.
   * Suba `sample_data/syllabus_info1197.md` con el rol *Syllabus / Programa*.
3. **Carga y Evaluación de Informe (RF-005, RF-006, RF-007):**
   * Vaya a **📄 Ingesta de Informes (PDF)**.
   * Seleccione a *Carlos Alumno Pérez* y suba el archivo `sample_data/carlos_alumno_informe_final.pdf`.
   * El sistema extraerá el contenido estructurado en Markdown y ejecutará el análisis heurístico con formato Anexo A y generación de 15 preguntas contextuales.
4. **Pool y Despacho (RF-008, RF-009, RF-010):**
   * Vaya a **❓ Pool de Preguntas & Despacho**. Seleccione las preguntas preferidas.
   * Presione **🚀 Despachar Flash Tests**. Se generarán los tokens `UUIDv4` únicos (48h).
5. **Verificación Flash del Estudiante (RF-011, RN-001, RN-002):**
   * Abra en una pestaña incógnito el enlace generado (ej: `http://127.0.0.1:8000/test/<token>`).
   * Observe el temporizador regresivo de 60 segundos por WebSocket, responda las preguntas y envíe.
6. **Decisión Docente y Cierre (RF-012, RF-013, RN-004):**
   * En **📊 Panel de Resultados**, vea las métricas actualizadas en tiempo real.
   * Si requiere defensa oral, presione **📅 Citar**.
   * Presione **✍ Calificar** para fijar la nota definitiva (1.0 - 7.0) con justificación obligatoria.
   * En **🛡️ Auditoría Inmutable**, verifique la trazabilidad del cambio.
