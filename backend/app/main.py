import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import engine, Base, SessionLocal
from backend.app import models
from backend.app.auth import hash_password
from backend.app.routers import (
    auth,
    asignaturas,
    estudiantes,
    materiales,
    trabajos,
    preguntas,
    flash_test,
    panel,
    audit,
    gestion,
    admin
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables
    Base.metadata.create_all(bind=engine)
    from backend.app.migrations import upgrade_activities
    upgrade_activities(engine)
    from backend.app.database import protect_audit_logs
    protect_audit_logs()
    
    # Seed demo users if they don't exist
    db: Session = SessionLocal()
    try:
        # --- Docente demo ---
        teacher = db.query(models.Usuario).filter(models.Usuario.correo == "docente@universidad.cl").first()
        if not teacher:
            teacher = models.Usuario(
                nombre="Prof. Sebastián Cisternas",
                correo="docente@universidad.cl",
                contrasena=hash_password("Docente123!"),
                rol="docente"
            )
            db.add(teacher)
            db.commit()
            db.refresh(teacher)

            # Default course
            default_course = models.Asignatura(
                nombre="INFO1197 - Ingeniería de Software y Título",
                periodo="Semestre 2",
                ano=2026,
                docente_id=teacher.id,
                parametros={
                    "prompt_custom": "Enfocar el rigor en la justificación de decisiones arquitecturales y cumplimiento ético.",
                    "nivel_rigor": "medium",
                    "pool_size": 15,
                    "num_preguntas_test": 5,
                    "umbral_ia": 40.0,
                    "umbral_coherencia": 60.0,
                    "tiempo_test_segundos": 60
                }
            )
            db.add(default_course)
            db.commit()

        # --- Admin demo ---
        admin = db.query(models.Usuario).filter(models.Usuario.correo == "admin@universidad.cl").first()
        if not admin:
            admin = models.Usuario(
                nombre="Administrador Sistema",
                correo="admin@universidad.cl",
                contrasena=hash_password("Admin123!"),
                rol="admin"
            )
            db.add(admin)
            db.commit()

        # --- Ayudante demo ---
        ayudante = db.query(models.Usuario).filter(models.Usuario.correo == "ayudante@universidad.cl").first()
        if not ayudante:
            ayudante = models.Usuario(
                nombre="Ana Ayudante González",
                correo="ayudante@universidad.cl",
                contrasena=hash_password("Ayudante123!"),
                rol="ayudante"
            )
            db.add(ayudante)
            db.commit()

        # Demo assistant is explicitly assigned to the demo teacher's course.
        demo_course = db.query(models.Asignatura).filter_by(docente_id=teacher.id).first()
        if demo_course and not db.get(models.CourseAssistant, (demo_course.id, ayudante.id)):
            db.add(models.CourseAssistant(asignatura_id=demo_course.id, usuario_id=ayudante.id))
            db.commit()
    finally:
        db.close()

    import asyncio
    from contextlib import suppress
    from backend.app.routers.flash_test import sweep_active_tests
    timer_task = asyncio.create_task(sweep_active_tests(SessionLocal))
    from backend.app.services.mail_outbox import reminder_loop
    reminder_task = asyncio.create_task(reminder_loop(SessionLocal))
    from backend.app.services.upload_worker import upload_loop
    upload_task = asyncio.create_task(upload_loop(SessionLocal))
    try:
        yield
    finally:
        upload_task.cancel()
        with suppress(asyncio.CancelledError):
            await upload_task
        reminder_task.cancel()
        with suppress(asyncio.CancelledError):
            await reminder_task
        timer_task.cancel()
        with suppress(asyncio.CancelledError):
            await timer_task

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Sistema Semi-Automatizado de Evaluación de Integridad Académica, Detección de IA y Verificación Oral Flash",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(asignaturas.router)
app.include_router(estudiantes.router)
app.include_router(materiales.router)
app.include_router(trabajos.router)
app.include_router(preguntas.router)
app.include_router(flash_test.router)
app.include_router(panel.router)
app.include_router(audit.router)
app.include_router(gestion.router)
app.include_router(admin.router)
from backend.app.routers import actividades
app.include_router(actividades.router)
from backend.app.routers import recovery, operations
app.include_router(recovery.router)
app.include_router(operations.router)
from backend.app.routers import upload_queue
app.include_router(upload_queue.router)
from backend.app.routers import smtp_admin
app.include_router(smtp_admin.router)

# Mount Static Files
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
STATIC_DIR = FRONTEND_DIR / "static"
TEMPLATES_DIR = FRONTEND_DIR / "templates"

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/login", include_in_schema=False)
@app.get("/", include_in_schema=False)
@app.get("/docente", include_in_schema=False)
@app.get("/panel", include_in_schema=False)
async def redirect_legacy_interface():
    # The modern frontend is the only entry point for interactive dashboards.
    return RedirectResponse(settings.PUBLIC_APP_URL.rstrip("/") + "/", status_code=307)

@app.get("/test/{token}", response_class=HTMLResponse)
async def serve_student_flash_test(token: str):
    test_file = TEMPLATES_DIR / "flashtest.html"
    if test_file.exists():
        with open(test_file, "r", encoding="utf-8") as f:
            content = f.read().replace("{{TOKEN}}", token)
            return HTMLResponse(content=content)
    return HTMLResponse(f"<h1>IntegriEval - Flash Test</h1><p>Token: {token}</p>")
