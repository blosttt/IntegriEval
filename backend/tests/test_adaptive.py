from datetime import datetime, timedelta, timezone

import pytest

from backend.app import models as m
from backend.app.auth import create_access_token


@pytest.mark.parametrize(("answer", "expected"), [("A", "Prevista"), ("B", "Reformular"), (None, "Reformular"), ("timeout", "Reformular")])
def test_adaptive_test_hides_branches_and_records_path(client, db_session, seeded_teacher, answer, expected):
    teacher, course = seeded_teacher["teacher"], seeded_teacher["course"]
    student = m.Estudiante(nombre="Demo", correo="adaptive@example.invalid", asignatura_id=course.id)
    student.trabajo = m.Trabajo(estado="analizado", markdown="Informe sintetico")
    evaluation = m.Evaluacion(nota=5, pct_ia=0, feedback={}, desglose={})
    student.trabajo.evaluacion = evaluation
    for name in ("Base", "Prevista", "Avanzada", "Reformular"):
        evaluation.preguntas.append(m.Pregunta(texto=name, seleccionada=name in ("Base", "Prevista"),
            alternativas=[{"id":"A","texto":"Correcta","es_correcta":True},{"id":"B","texto":"Incorrecta","es_correcta":False}]))
    db_session.add(student)
    db_session.commit()
    base, planned, _, wrong = evaluation.preguntas
    headers = {"Authorization": "Bearer " + create_access_token({"sub": str(teacher.id)})}
    plan = f"/api/evaluaciones/{evaluation.id}/repreguntas"
    data = {"seleccion": [base.id, planned.id], "reglas": [{"base": base.id, "error": wrong.id}]}
    assert client.put(plan, headers=headers, json=data).status_code == 200
    payload = client.post(f"/api/asignaturas/{course.id}/flash-test/despacho", headers=headers, json=[student.id]).json()
    root = f"/api/flash-test/{payload['items'][0]['token']}"
    assert client.get(root+"/info").json()["preguntas"] == []
    state = client.post(root+"/start").json()
    assert state["num_preguntas"] == 2 and [q["texto"] for q in state["preguntas"]] == ["Base"]
    if answer == "timeout":
        test = db_session.query(m.FlashTest).filter_by(estudiante_id=student.id).one()
        stored = db_session.get(m.FlashTestState, test.id)
        stored.inicio_pregunta = datetime.now(timezone.utc) - timedelta(seconds=test.tiempo_limite_segundos + 1)
        db_session.commit()
        state = client.get(root+"/info").json()
    else:
        state = client.post(root+"/answer", json={"question_id": base.id, "answer": answer}).json()
        assert client.post(root+"/answer", json={"question_id": base.id, "answer": answer}).json()["preguntas"][1]["texto"] == expected
    assert state["preguntas"][1]["texto"] == expected
    done = client.post(root+"/answer", json={"question_id": state["preguntas"][1]["id"], "answer": "A"}).json()
    assert done["estado"] == "completado"
    flash = db_session.query(m.FlashTest).filter_by(estudiante_id=student.id).one()
    report = f"/api/flash-tests/{flash.id}/reporte-rubrica"
    followup = client.get(report, headers=headers).json()["registro"][1]
    assert followup["depende_de"] == (None if answer == "A" else 1)
    assert followup["rama"] == {"A": None, "B": "error", None: "sin_respuesta", "timeout": "sin_respuesta"}[answer]
    pdf = client.get(report+"/pdf", headers=headers)
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
