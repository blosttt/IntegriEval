import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app as fastapi_app
from app.core.database import Base, get_db
import app.models.models # Register models in Base.metadata
from sqlalchemy.pool import StaticPool

# Create an isolated, in-memory database for unit tests using StaticPool to preserve tables
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
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
    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()

def test_user_registration_and_login(client):
    """
    Verifies that a student can register and subsequently log in.
    """
    # 1. Register student
    reg_payload = {
        "email": "estudiante.test@uct.cl",
        "name": "Estudiante de Prueba",
        "password": "passwordSeguro123",
        "role": "student"
    }
    reg_response = client.post("/api/auth/register", json=reg_payload)
    assert reg_response.status_code == 200
    data = reg_response.json()
    assert data["email"] == "estudiante.test@uct.cl"
    assert data["role"] == "student"
    assert "id" in data

    # 2. Duplicate email rejection
    dup_response = client.post("/api/auth/register", json=reg_payload)
    assert dup_response.status_code == 400

    # 3. Successful Login
    login_response = client.post("/api/auth/login", data={
        "username": "estudiante.test@uct.cl",
        "password": "passwordSeguro123"
    })
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert "access_token" in login_data
    assert login_data["role"] == "student"
    assert login_data["name"] == "Estudiante de Prueba"
