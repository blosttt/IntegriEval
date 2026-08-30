from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import Base, engine, settings
from app.api import (
    auth, courses, evaluations, reports, flash,
    appointments, dashboard, students, materials
)

# Create all database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="IntegriEval API",
    description=(
        "API de IntegriEval — Herramienta de verificación de integridad académica. "
        "Permite al profesor subir trabajos en lote, analizarlos con IA, gestionar el pool "
        "de preguntas flash y coordinar las citas de revisión con estudiantes."
    ),
    version="2.0.0"
)

origins = [org.strip() for org in settings.ALLOW_ORIGINS.split(",") if org.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix="/api")
app.include_router(courses.router, prefix="/api")
app.include_router(students.router, prefix="/api")       # Student management (no-account)
app.include_router(evaluations.router, prefix="/api")
app.include_router(materials.router, prefix="/api")      # Course material upload
app.include_router(reports.router, prefix="/api")        # Bulk upload + analysis + questions
app.include_router(flash.router, prefix="/api")          # Flash test (token-based, no auth)
app.include_router(appointments.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")


@app.get("/")
def read_root():
    return {
        "name": "IntegriEval API",
        "version": "2.0.0",
        "status": "healthy",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
    }
