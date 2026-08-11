from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import Base, engine, settings
from app.api import auth, courses, evaluations, reports, questions, session, appointments, dashboard

# Automatically create database tables on startup for SQLite development.
# In production, this can be managed by Alembic, but this ensures out-of-the-box readiness.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="IntegriEval API",
    description="API del MVP IntegriEval para validación de autoría de informes académicos",
    version="1.0.0"
)

# Parse origins from settings
origins = [org.strip() for org in settings.ALLOW_ORIGINS.split(",") if org.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount endpoints under /api prefix
app.include_router(auth.router, prefix="/api")
app.include_router(courses.router, prefix="/api")
app.include_router(evaluations.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(questions.router, prefix="/api")
app.include_router(session.router, prefix="/api")
app.include_router(appointments.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")

@app.get("/")
def read_root():
    return {
        "name": "IntegriEval API Services",
        "status": "healthy",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }
