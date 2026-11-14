import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
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
    from backend.app.migrations import upgrade_activities, upgrade_questions
    upgrade_activities(engine)
    upgrade_questions(engine)
    from backend.app.database import protect_audit_logs
    protect_audit_logs()
    from backend.app.services.smtp_configuration import disable_unverified_mail
    with SessionLocal() as mail_db:
        disable_unverified_mail(mail_db)
    
    if settings.SEED_DEMO_DATA:
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
    from backend.app.services.backups import backup_loop
    backup_task = asyncio.create_task(backup_loop(settings)) if settings.BACKUP_ENABLED else None
    try:
        yield
    finally:
        if backup_task:
            backup_task.cancel()
            with suppress(asyncio.CancelledError):
                await backup_task
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
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
if settings.ENVIRONMENT == "production":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    if settings.ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response


@app.get("/api/health", include_in_schema=False)
def health():
    from sqlalchemy import text
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ok"}

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
from backend.app.routers import readiness
app.include_router(readiness.router)
from backend.app.routers import development
app.include_router(development.router)

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

@app.get("/test/{token}", include_in_schema=False)
async def serve_student_flash_test(token: str):
    from urllib.parse import quote
    return RedirectResponse(settings.PUBLIC_APP_URL.rstrip("/") + "/flash/" + quote(token, safe=""), status_code=307)
from backend.app.routers import general_pool
app.include_router(general_pool.router)

from backend.app.routers import assessment
app.include_router(assessment.router)
