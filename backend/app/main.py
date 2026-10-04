import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
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
    audit
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables
    Base.metadata.create_all(bind=engine)
    
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

    finally:
        db.close()

    yield

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

# Mount Static Files
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
STATIC_DIR = FRONTEND_DIR / "static"
TEMPLATES_DIR = FRONTEND_DIR / "templates"

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/login", response_class=HTMLResponse)
async def serve_login():
    login_file = TEMPLATES_DIR / "login.html"
    if login_file.exists():
        with open(login_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>Login</h1>")

@app.get("/", response_class=HTMLResponse)
@app.get("/docente", response_class=HTMLResponse)
@app.get("/panel", response_class=HTMLResponse)
async def serve_teacher_dashboard():
    index_file = TEMPLATES_DIR / "index.html"
    if index_file.exists():
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>IntegriEval - Backend Activo</h1><p>Cargue la interfaz web en frontend/templates/index.html</p>")

@app.get("/test/{token}", response_class=HTMLResponse)
async def serve_student_flash_test(token: str):
    test_file = TEMPLATES_DIR / "flashtest.html"
    if test_file.exists():
        with open(test_file, "r", encoding="utf-8") as f:
            content = f.read().replace("{{TOKEN}}", token)
            return HTMLResponse(content=content)
    return HTMLResponse(f"<h1>IntegriEval - Flash Test</h1><p>Token: {token}</p>")
