import io
import pytest
from backend.app.auth import create_access_token

def test_csv_ingestion_valid_and_duplicates(client, seeded_teacher):
    teacher = seeded_teacher["teacher"]
    course = seeded_teacher["course"]
    token = create_access_token({"sub": str(teacher.id), "rol": teacher.rol, "email": teacher.correo})
    headers = {"Authorization": f"Bearer {token}"}

    csv_data = (
        "nombre,correo,rut\n"
        "Carlos Alumno,carlos@alumnos.cl,20.111.222-3\n"
        "Maria Estudiante,maria@alumnos.cl,21.333.444-5\n"
        "Carlos Alumno,carlos@alumnos.cl,20.111.222-3\n"  # Duplicate
        "Pedro Perez,pedro@alumnos.cl,19.555.666-7\n"
    )

    files = {"file": ("alumnos.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    resp = client.post(f"/api/asignaturas/{course.id}/estudiantes/csv", files=files, headers=headers)
    
    assert resp.status_code == 200
    res = resp.json()
    assert res["total_procesados"] == 4
    assert res["cargados_exitosamente"] == 3
    assert res["duplicados_omitidos"] == 1
    assert len(res["estudiantes"]) == 3

def test_csv_ingestion_semicolon_format(client, seeded_teacher):
    teacher = seeded_teacher["teacher"]
    course = seeded_teacher["course"]
    token = create_access_token({"sub": str(teacher.id), "rol": teacher.rol, "email": teacher.correo})
    headers = {"Authorization": f"Bearer {token}"}

    csv_semicolon = (
        "nombre;correo;rut\n"
        "Ana Silva;ana.silva@universidad.cl;18.999.888-1\n"
        "Lucas Soto;lucas.soto@universidad.cl;22.444.555-6\n"
    )
    files = {"file": ("nomina_semi.csv", io.BytesIO(csv_semicolon.encode("utf-8")), "text/csv")}
    resp = client.post(f"/api/asignaturas/{course.id}/estudiantes/csv", files=files, headers=headers)
    assert resp.status_code == 200
    res = resp.json()
    assert res["cargados_exitosamente"] == 2
