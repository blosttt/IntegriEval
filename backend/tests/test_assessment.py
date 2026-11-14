from backend.app import models as m
from backend.app.auth import create_access_token
from backend.app.config import settings


def test_rubric_pool_report_and_independent_review(client, db_session, seeded_teacher, monkeypatch):
    teacher, course = seeded_teacher["teacher"], seeded_teacher["course"]
    course.parametros = {**course.parametros, "pool_size": 10, "num_preguntas_test": 4}
    student = m.Estudiante(nombre="Caso sintetico", correo="rubrica@example.invalid", asignatura_id=course.id)
    work = m.Trabajo(estado="cargado", markdown="# Algoritmo\nLa busqueda binaria requiere un arreglo ordenado.")
    student.trabajo = work
    db_session.add(student)
    db_session.commit()
    headers = {"Authorization": "Bearer " + create_access_token({"sub": str(teacher.id)})}
    root = f"/api/asignaturas/{course.id}"
    setup = {
        "temas": "Busqueda binaria",
        "criterios": [
            {"nombre": "Precondicion", "descripcion": "Explica el orden", "peso": 60},
            {"nombre": "Aplicacion", "descripcion": "Resuelve otro caso", "peso": 40},
        ],
    }
    templates = root + "/plantillas-rubrica"
    template = {"nombre": "Algoritmos", "criterios": setup["criterios"]}
    assert client.post(templates, headers=headers, json=template).status_code == 201
    assert client.get(templates, headers=headers).json() == [template]
    config = root + "/preparacion-evaluacion"
    assert client.put(config, headers=headers, json={**setup, "criterios": setup["criterios"][:1]}).status_code == 422
    assert client.put(config, headers=headers, json=setup).json()["version"] == 1
    assert client.post(f"/api/trabajos/{work.id}/reanalizar", headers=headers).status_code == 200
    db_session.expire_all()
    evaluation = work.evaluacion
    assert len(evaluation.preguntas) == 12
    assert {q.seccion_origen for q in evaluation.preguntas if q.seleccionada} == {"Precondicion", "Aplicacion"}

    dispatch = client.post(root + "/flash-test/despacho", headers=headers, json=[student.id]).json()
    flash = db_session.query(m.FlashTest).filter_by(token=dispatch["items"][0]["token"]).one()
    state = db_session.get(m.FlashTestState, flash.id)
    flash.estado = "completado"
    flash.respuestas = {str(q["id"]): q["alternativas"][0]["id"] for q in state.preguntas}
    db_session.commit()
    url = f"/api/flash-tests/{flash.id}/reporte-rubrica"
    findings = [
        {"criterio": "Precondicion", "puntaje": 90, "observacion": "Explica el requisito", "evidencia": "arreglo ordenado",
         "fuente": "informe", "pregunta": None, "entrevista": "Pedir contraejemplo"},
        {"criterio": "Aplicacion", "puntaje": None, "observacion": "Falta evidencia", "evidencia": "",
         "fuente": "sin_evidencia", "pregunta": None, "entrevista": "Cambiar la entrada"},
    ]

    async def model(*args, **kwargs):
        return {"criterios": findings}

    monkeypatch.setattr(settings, "LLM_PROVIDER", "ollama")
    monkeypatch.setattr("backend.app.services.assessment.request_json", model)
    assert client.post(url + "/ia", headers=headers).status_code == 200
    blind = client.get(url, headers=headers).json()
    assert blind["ia"] is None and blind["ia_generada"]
    assert len(blind["registro"]) == 4
    assert client.put(url + "/docente", headers=headers, json={"criterios": findings}).status_code == 200
    revealed = client.get(url, headers=headers).json()
    assert revealed["ia"]["cobertura"] == revealed["docente"]["cobertura"] == 60
    assert revealed["ia"]["puntaje"] is None
    assert client.put(url + "/contraste", headers=headers, json={"acuerdo": True, "comentario": "Coincide la evidencia"}).status_code == 200
    recalibrated = client.post(url + "/calibrar", headers=headers)
    assert recalibrated.status_code == 200
    assert recalibrated.json()["despues"] == {"criterios_comparables": 1, "error_medio": 0.0}
