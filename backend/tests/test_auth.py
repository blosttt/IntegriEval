import pytest
from backend.app.auth import hash_password, verify_password, create_access_token

def test_bcrypt_hashing_and_verification():
    raw_pass = "SecurePass123!"
    hashed = hash_password(raw_pass)
    assert hashed != raw_pass
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_user_registration_and_login(client):
    # 1. Register new teacher
    reg_resp = client.post("/api/auth/register", json={
        "nombre": "Benjamin Sobarzo",
        "correo": "benjamin@universidad.cl",
        "contrasena": "Admin2026!",
        "rol": "docente"
    })
    assert reg_resp.status_code == 200
    data = reg_resp.json()
    assert "access_token" in data
    assert data["user"]["correo"] == "benjamin@universidad.cl"

    # 2. Login with registered credentials
    login_resp = client.post("/api/auth/login", json={
        "correo": "benjamin@universidad.cl",
        "contrasena": "Admin2026!"
    })
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    # 3. Authenticated me endpoint
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["nombre"] == "Benjamin Sobarzo"

def test_login_invalid_password(client, seeded_teacher):
    resp = client.post("/api/auth/login", json={
        "correo": "docente.test@universidad.cl",
        "contrasena": "WrongPass"
    })
    assert resp.status_code == 401
