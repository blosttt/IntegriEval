import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.auth import hash_password
from backend.app import models

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def seeded_teacher(db_session):
    teacher = models.Usuario(
        nombre="Prof. Sebastián Cisternas",
        correo="docente.test@universidad.cl",
        contrasena=hash_password("Docente123!"),
        rol="docente"
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)

    course = models.Asignatura(
        nombre="INFO1197 - Proyecto",
        periodo="Semestre 2",
        ano=2026,
        docente_id=teacher.id,
        parametros={
            "prompt_custom": "Rigor metodológico",
            "nivel_rigor": "medium",
            "pool_size": 15,
            "num_preguntas_test": 5,
            "umbral_ia": 40.0,
            "umbral_coherencia": 60.0,
            "tiempo_test_segundos": 60
        }
    )
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)

    return {"teacher": teacher, "course": course}
