import asyncio
import pytest
from backend.app import models
from backend.app.auth import create_access_token
from backend.app.config import settings
from backend.app.services import llm_service as llm


def test_every_section_including_tail_is_read(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "ollama")
    report = "Inicio. " + "Resultados detallados. " * 850 + "CONCLUSION_FINAL_UNICA"
    evidence_requests, final_requests = [], []
    valid = llm.mock_evaluation(markdown_content="Informe") [0]

    async def respond(system, prompt, schema=None):
        if "resumen" in schema.get("properties", {}):
            evidence_requests.append(prompt.split("\n", 1)[1])
            return {"resumen": "CONCLUSION_FINAL_UNICA" if "CONCLUSION_FINAL_UNICA" in prompt else "Hallazgos de esta sección", "evidencias": []}
        final_requests.append(prompt)
        return valid

    monkeypatch.setattr(llm, "request_json", respond)
    data, _, _ = asyncio.run(llm.evaluate_submission_llm(report))
    assert "".join(evidence_requests) == report
    assert "CONCLUSION_FINAL_UNICA" in final_requests[0]
    assert data["cobertura_documento"]["caracteres_originales"] == len(report)
    assert data["motor_analisis"] == "ollama" and not data["fallback_ia"]


def test_hierarchical_synthesis_is_bounded_without_truncation(monkeypatch):
    levels = []
    async def respond(system, prompt, schema=None):
        levels.append(prompt.split("\n", 1)[0])
        return {"resumen": "E" * 1500, "evidencias": ["D" * 390] * 5}
    monkeypatch.setattr(llm, "request_json", respond)
    result = asyncio.run(llm.prepare_document("X" * 60000, "Informe"))
    assert len(result) <= 8000
    assert any("nivel 2" in label for label in levels)


def test_question_generation_also_reads_end_of_long_report(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "ollama")
    report = "Informe y método. " * 1800 + "HALLAZGO_FINAL"
    seen = []
    pool = llm.mock_questions("Informe", "", pool_size=10)
    async def respond(system, prompt, schema=None):
        seen.append(prompt)
        if "resumen" in schema.get("properties", {}):
            return {"resumen": "HALLAZGO_FINAL" if "HALLAZGO_FINAL" in prompt else "Método", "evidencias": []}
        return {"preguntas": pool}
    monkeypatch.setattr(llm, "request_json", respond)
    questions = asyncio.run(llm.generate_question_pool_llm(report, pool_size=10))
    assert len(questions) == 10
    assert "HALLAZGO_FINAL" in seen[-1]
    assert all(q["_motor"] == "ollama" for q in questions)


def test_synthesis_failure_is_not_converted_to_grade(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "ollama")
    async def invalid(*args, **kwargs):
        return {"resumen": "", "evidencias": []}
    monkeypatch.setattr(llm, "request_json", invalid)
    with pytest.raises(llm.LLMUnavailable):
        asyncio.run(llm.evaluate_submission_llm("Informe " * 2000))


def test_question_failure_preserves_previous_evaluation_and_retry(client, db_session, seeded_teacher, monkeypatch):
    from backend.app.routers import trabajos
    teacher, course = seeded_teacher["teacher"], seeded_teacher["course"]
    student = models.Estudiante(nombre="Prueba", correo="test@example.invalid", asignatura_id=course.id)
    work = models.Trabajo(markdown="Informe completo", estado="analizado")
    student.trabajo = work
    work.evaluacion = models.Evaluacion(nota=5, pct_ia=10, feedback={}, desglose={"porcentaje_logro": "70%"})
    work.evaluacion.preguntas.append(models.Pregunta(texto="Pregunta revisada", alternativas=[], seleccionada=True))
    db_session.add(student)
    db_session.commit()
    previous_id = work.evaluacion.id
    previous_question = work.evaluacion.preguntas[0].id
    auth = {"Authorization": "Bearer " + create_access_token({"sub": str(teacher.id)})}
    async def fail(*args, **kwargs):
        raise llm.LLMUnavailable("Ollama no disponible. Reintenta.")
    monkeypatch.setattr(trabajos, "generate_question_pool_llm", fail)
    response = client.post(f"/api/trabajos/{work.id}/reanalizar", headers=auth)
    assert response.status_code == 503
    db_session.expire_all()
    assert db_session.get(models.Trabajo, work.id).estado == "error"
    assert db_session.get(models.Evaluacion, previous_id).nota == 5
    assert db_session.get(models.Pregunta, previous_question).texto == "Pregunta revisada"
    assert client.post(f"/api/asignaturas/{course.id}/flash-test/despacho", headers=auth).json()["total_despachados"] == 0
    assert client.post(f"/api/asignaturas/{course.id}/flash-test/despacho", headers=auth, json=[student.id]).status_code == 409

    async def succeed(*args, **kwargs):
        return llm.mock_questions("Informe", "", pool_size=15)
    monkeypatch.setattr(trabajos, "generate_question_pool_llm", succeed)
    assert client.post(f"/api/trabajos/{work.id}/reanalizar", headers=auth).status_code == 200
    db_session.expire_all()
    assert db_session.get(models.Trabajo, work.id).estado == "analizado"
    assert len(db_session.get(models.Trabajo, work.id).evaluacion.preguntas) == 15


def test_simulated_historical_evaluations_cannot_be_dispatched_as_real(client, db_session, seeded_teacher, monkeypatch):
    teacher, course = seeded_teacher["teacher"], seeded_teacher["course"]
    student = models.Estudiante(nombre="Demo", correo="demo@example.invalid", asignatura_id=course.id)
    student.trabajo = models.Trabajo(markdown="Demo", estado="analizado")
    student.trabajo.evaluacion = models.Evaluacion(nota=6, pct_ia=0, feedback={}, desglose={"motor_analisis": "mock", "fallback_ia": True})
    student.trabajo.evaluacion.preguntas.append(models.Pregunta(texto="Demo", alternativas=[], seleccionada=True))
    db_session.add(student)
    db_session.commit()
    monkeypatch.setattr(settings, "LLM_PROVIDER", "ollama")
    headers = {"Authorization": "Bearer " + create_access_token({"sub": str(teacher.id)})}
    response = client.post(f"/api/asignaturas/{course.id}/flash-test/despacho", headers=headers)
    assert response.status_code == 200 and response.json()["total_despachados"] == 0
    assert client.post(f"/api/asignaturas/{course.id}/flash-test/despacho", headers=headers, json=[student.id]).status_code == 409
    assert db_session.query(models.FlashTest).count() == 0


def test_old_test_links_redirect_to_modern_interface(client):
    response = client.get("/test/example-token", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == settings.PUBLIC_APP_URL.rstrip("/") + "/flash/example-token"
