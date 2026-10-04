import pytest
from datetime import datetime, timezone, timedelta
from backend.app.auth import create_access_token
from backend.app import models

def test_full_flash_test_and_cierre_flow(client, db_session, seeded_teacher):
    teacher = seeded_teacher["teacher"]
    course = seeded_teacher["course"]
    token = create_access_token({"sub": str(teacher.id), "rol": teacher.rol, "email": teacher.correo})
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a student
    student = models.Estudiante(
        nombre="Estudiante Prueba",
        correo="estudiante.prueba@alumnos.cl",
        rut="20.123.456-7",
        asignatura_id=course.id
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)

    # 2. Attach work and evaluation
    trabajo = models.Trabajo(
        estudiante_id=student.id,
        pdf_path="test.pdf",
        markdown="# Metodología y Pruebas\n\nDesarrollo del software.",
        estado="analizado"
    )
    db_session.add(trabajo)
    db_session.commit()
    db_session.refresh(trabajo)

    evaluacion = models.Evaluacion(
        trabajo_id=trabajo.id,
        nota=5.5,
        feedback={"fortalezas": ["Bien"], "debilidades": ["Poco detalle"], "recomendaciones": ["Mejorar"]},
        pct_ia=35.0,
        desglose={
            "porcentaje_logro": "75%",
            "feedback": {"fortalezas": ["Bien"], "debilidades": ["Poco detalle"], "recomendaciones": ["Mejorar"]},
            "deteccion_ia": {"porcentaje": "35%", "nivel_confianza": "medio", "secciones_sospechosas": [], "justificacion": "Normal"},
            "desglose_rubrica": {"contenido": "75%", "estructura": "80%", "ortografia": "70%"},
            "evaluacion_respuestas": {
                "nivel_rigor_aplicado": "medium",
                "porcentaje_coherencia": "75%",
                "respuestas_correctas": "3/4",
                "preguntas_falladas": [],
                "observacion_ia": "Coherente",
                "requiere_defensa_oral": False
            }
        }
    )
    db_session.add(evaluacion)
    db_session.commit()
    db_session.refresh(evaluacion)

    # Add questions
    for i in range(1, 6):
        q = models.Pregunta(
            evaluacion_id=evaluacion.id,
            texto=f"Pregunta {i}",
            alternativas=[
                {"id": "A", "texto": "Opción A", "es_correcta": True},
                {"id": "B", "texto": "Opción B", "es_correcta": False},
                {"id": "C", "texto": "Opción C", "es_correcta": False},
                {"id": "D", "texto": "Opción D", "es_correcta": False}
            ],
            seleccionada=True
        )
        db_session.add(q)
    db_session.commit()

    # 3. Despacho Flash Test (RF-010)
    dispatch_resp = client.post(f"/api/asignaturas/{course.id}/flash-test/despacho", headers=headers)
    assert dispatch_resp.status_code == 200
    dispatch_data = dispatch_resp.json()
    assert dispatch_data["total_despachados"] == 1
    item = dispatch_data["items"][0]
    flash_token = item["token"]
    assert len(flash_token) > 20

    # 4. Public Student Info (Zero-login, RN-001)
    info_resp = client.get(f"/api/flash-test/{flash_token}/info")
    assert info_resp.status_code == 200
    info_data = info_resp.json()
    assert info_data["estudiante_nombre"] == "Estudiante Prueba"
    assert len(info_data["preguntas"]) == 5
    # Verify answers are NOT revealed
    for alt in info_data["preguntas"][0]["alternativas"]:
        assert "es_correcta" not in alt

    # 5. Submit Answers (RF-011, RN-002)
    # Student answers all with 'A' (correct answers)
    questions = db_session.query(models.Pregunta).filter(models.Pregunta.evaluacion_id == evaluacion.id).all()
    sub_resp = client.post(f"/api/flash-test/{flash_token}/submit", json={
        "token": flash_token,
        "respuestas": {str(q.id): "A" for q in questions},
        "tiempo_transcurrido": 45
    })
    assert sub_resp.status_code == 200
    assert sub_resp.json()["puntaje"] == 100.0

    # 6. Check Teacher Dashboard (RF-012)
    panel_resp = client.get(f"/api/asignaturas/{course.id}/panel", headers=headers)
    assert panel_resp.status_code == 200
    panel_data = panel_resp.json()
    assert panel_data["total_alumnos"] == 1
    assert panel_data["tests_completados"] == 1
    assert panel_data["estudiantes"][0]["puntaje_flash"] == 100.0

    # 7. Oral Defense Citation (RF-013)
    cita_resp = client.post(f"/api/asignaturas/{course.id}/citas", json={
        "estudiante_id": student.id,
        "fecha": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
        "bloque": "11:00 - 11:15",
        "acuerdos": "Defensa de prueba"
    }, headers=headers)
    assert cita_resp.status_code == 200
    assert cita_resp.json()["bloque"] == "11:00 - 11:15"

    # 8. Close Grade with Mandatory Justification (RN-004)
    close_resp = client.post(f"/api/asignaturas/{course.id}/cerrar-nota", json={
        "estudiante_id": student.id,
        "nota_final": 6.2,
        "justificacion": "Excelente dominio conceptual en verificación flash"
    }, headers=headers)
    assert close_resp.status_code == 200
    assert close_resp.json()["nota_final"] == 6.2

    # 9. Verify Immutable Audit Trail (RN-004, RD-AuditLog)
    audit_resp = client.get("/api/audit", headers=headers)
    assert audit_resp.status_code == 200
    audit_logs = audit_resp.json()
    actions = [log["accion"] for log in audit_logs]
    assert "DESPACHO_FLASH_TESTS" in actions
    assert "CIERRE_MODIFICACION_NOTA" in actions
