from backend.app import models as m
from backend.app.auth import create_access_token


def test_shared_questions_are_scoped_and_preserved_at_dispatch(client, db_session, seeded_teacher):
    teacher, course = seeded_teacher["teacher"], seeded_teacher["course"]
    course.parametros = {**course.parametros, "num_preguntas_test": 2}
    activity = m.Actividad(asignatura_id=course.id, titulo="Otra evaluacion", parametros={})
    for number in range(2):
        student = m.Estudiante(nombre=f"Demo {number}", correo=f"mixto{number}@example.invalid", asignatura_id=course.id)
        work = m.Trabajo(estado="analizado")
        student.trabajo = work
        work.evaluacion = m.Evaluacion(nota=5, pct_ia=0, feedback={}, desglose={})
        work.evaluacion.preguntas.append(m.Pregunta(
            texto=f"Pregunta individual {number}",
            alternativas=[{"id":"A","texto":"Correcta","es_correcta":True},{"id":"B","texto":"Otra","es_correcta":False}],
        ))
        db_session.add(student)
    db_session.add(activity)
    db_session.commit()

    auth = {"Authorization": "Bearer " + create_access_token({"sub": str(teacher.id)})}
    root = f"/api/asignaturas/{course.id}"
    pool = root + "/pool-general"
    data = {"texto": "Pregunta general", "tipo": "desarrollo", "criterios_evaluacion": "Pauta privada"}
    response = client.post(pool, headers=auth, json=data)
    assert response.status_code == 201
    question_id = response.json()["id"]
    assert client.get(pool + f"?actividad_id={activity.id}", headers=auth).json() == []
    assert client.get(pool + "/asignaciones").status_code == 401

    response = client.post(pool + "/sortear", headers=auth)
    assert response.json()["asignados"] == 2
    rows = client.get(pool + "/asignaciones", headers=auth).json()
    for number, row in enumerate(rows):
        assert {(q["texto"], q["pool_general"]) for q in row["seleccion"]} == {
            (f"Pregunta individual {number}", False), ("Pregunta general", True),
        }

    sent = client.post(root + "/flash-test/despacho", headers=auth, json=[rows[0]["estudiante_id"]]).json()
    assert sent["total_despachados"] == 1
    assert client.put(f"{pool}/{question_id}", headers=auth, json={**data, "texto": "Nueva version"}).status_code == 200
    assert client.post(pool + "/sortear", headers=auth).json()["asignados"] == 1
    assert client.delete(f"{pool}/{question_id}", headers=auth).status_code == 204

    history, draft = client.get(pool + "/asignaciones", headers=auth).json()
    assert "Pregunta general" in {q["texto"] for q in history["intentos"][0]["preguntas"]}
    assert "Nueva version" in {q["texto"] for q in draft["seleccion"]}
    public = client.get(f"/api/flash-test/{sent['items'][0]['token']}/info")
    assert "Pregunta general" in {q["texto"] for q in public.json()["preguntas"]}
    assert "Pauta privada" not in public.text
