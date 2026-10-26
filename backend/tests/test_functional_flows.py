import asyncio
from datetime import datetime, timedelta, timezone
import pytest
import httpx
from backend.app import models
from backend.app.auth import create_access_token, hash_password
from backend.app.config import settings
from backend.app.services import llm_service


def headers(user):
    return {"Authorization": "Bearer " + create_access_token({"sub": str(user.id)})}


@pytest.fixture
def prepared(client, db_session, seeded_teacher):
    teacher, course = seeded_teacher["teacher"], seeded_teacher["course"]
    student = models.Estudiante(nombre="María Pérez", correo="maria@example.cl", asignatura_id=course.id)
    student.trabajo = models.Trabajo(markdown="# Informe\nArquitectura distribuida", estado="analizado")
    student.trabajo.evaluacion = models.Evaluacion(nota=5, pct_ia=10, feedback={}, desglose={"porcentaje_logro": "75%"})
    for i in range(2):
        student.trabajo.evaluacion.preguntas.append(models.Pregunta(texto=f"Pregunta {i}", seleccionada=True, alternativas=[{"id": "A", "texto": "Correcta", "es_correcta": True}, {"id": "B", "texto": "Incorrecta", "es_correcta": False}]))
    db_session.add(student)
    db_session.commit()
    result = client.post(f"/api/asignaturas/{course.id}/flash-test/despacho", headers=headers(teacher))
    assert result.status_code == 200
    token = result.json()["items"][0]["token"]
    return teacher, course, student, token


def test_answer_persistence_and_recovery(client, db_session, prepared):
    _, _, _, token = prepared
    state = client.post(f"/api/flash-test/{token}/start").json()
    q1, q2 = state["preguntas"]
    assert "es_correcta" not in q1["alternativas"][0]
    assert client.post(f"/api/flash-test/{token}/answer", json={"question_id": q2["id"], "answer": "A"}).status_code == 409
    assert client.post(f"/api/flash-test/{token}/answer", json={"question_id": q1["id"], "answer": "Z"}).status_code == 422
    result = client.post(f"/api/flash-test/{token}/answer", json={"question_id": q1["id"], "answer": "A"})
    assert result.status_code == 200
    recovered = client.get(f"/api/flash-test/{token}/info").json()
    assert recovered["pregunta_actual"] == 1
    assert recovered["respuestas"] == {str(q1["id"]): "A"}
    assert client.post(f"/api/flash-test/{token}/start").json()["pregunta_actual"] == 1
    final = client.post(f"/api/flash-test/{token}/answer", json={"question_id": q2["id"], "answer": "B"}).json()
    assert final["estado"] == "completado"
    assert final["puntaje"] == 50
    # A repeated or forged submission cannot replace persisted answers.
    res = client.post(f"/api/flash-test/{token}/submit", json={"token": token, "respuestas": {str(q2["id"]): "A"}})
    assert res.json()["puntaje"] == 50


def test_expired_token_cannot_start_or_submit(client, db_session, prepared):
    _, _, _, token = prepared
    test = db_session.query(models.FlashTest).filter_by(token=token).one()
    test.vigencia = datetime.now(timezone.utc) - timedelta(seconds=1)
    db_session.commit()
    assert client.get(f"/api/flash-test/{token}/info").status_code == 410
    assert client.post(f"/api/flash-test/{token}/start").status_code == 410
    assert client.post(f"/api/flash-test/{token}/submit", json={"token": token, "respuestas": {}}).status_code == 410


def test_timeout_closes_with_partial_score(client, db_session, prepared):
    _, _, _, token = prepared
    state = client.post(f"/api/flash-test/{token}/start").json()
    q = state["preguntas"][0]
    client.post(f"/api/flash-test/{token}/answer", json={"question_id": q["id"], "answer": "A"})
    test = db_session.query(models.FlashTest).filter_by(token=token).one()
    saved = db_session.get(models.FlashTestState, test.id)
    saved.inicio_pregunta = datetime.now(timezone.utc) - timedelta(seconds=61)
    db_session.commit()
    final = client.get(f"/api/flash-test/{token}/info").json()
    assert final["estado"] == "completado"
    assert final["puntaje"] == 50


def test_course_isolation_and_dispatched_question_lock(client, db_session, prepared):
    teacher, course, student, token = prepared
    other = models.Usuario(nombre="Otro", correo="other@example.cl", contrasena=hash_password("password123"), rol="docente")
    db_session.add(other)
    db_session.commit()
    foreign_course = models.Asignatura(nombre="Otra", periodo="S1", ano=2026, docente_id=other.id)
    db_session.add(foreign_course)
    db_session.commit()
    evaluation = student.trabajo.evaluacion
    q = evaluation.preguntas[0]
    assert client.get(f"/api/evaluaciones/{evaluation.id}/preguntas", headers=headers(other)).status_code == 403
    assert client.put(f"/api/preguntas/{q.id}", headers=headers(other), json={"texto": "Intrusión"}).status_code == 403
    assert client.get(f"/api/asignaturas/{foreign_course.id}/estudiantes/{student.id}/evaluacion", headers=headers(other)).status_code == 404
    assert client.put(f"/api/preguntas/{q.id}", headers=headers(teacher), json={"texto": "Cambio"}).status_code == 409


def test_assistant_assignment_and_read_only(client, db_session, seeded_teacher, seeded_admin):
    teacher, course = seeded_teacher["teacher"], seeded_teacher["course"]
    assistant = models.Usuario(nombre="Ayudante", correo="helper@example.cl", contrasena=hash_password("password123"), rol="ayudante")
    db_session.add(assistant)
    db_session.commit()
    assert client.get(f"/api/asignaturas/{course.id}", headers=headers(assistant)).status_code == 403
    assert client.post(f"/api/asignaturas/{course.id}/ayudantes", headers=headers(seeded_admin), json={"correo": assistant.correo}).status_code == 200
    assert client.get(f"/api/asignaturas/{course.id}/panel", headers=headers(assistant)).status_code == 200
    assert any(c["id"] == course.id for c in client.get('/api/asignaturas', headers=headers(assistant)).json())
    assert client.put(f"/api/asignaturas/{course.id}", headers=headers(assistant), json={"nombre": "Cambio"}).status_code == 403
    assert client.post('/api/asignaturas', headers=headers(assistant), json={"nombre": "Curso", "periodo": "S1", "ano": 2026}).status_code == 403


def test_public_registration_cannot_create_admin(client):
    response = client.post('/api/auth/register', json={"nombre": "Admin", "correo": "elevate@example.cl", "contrasena": "password123", "rol": "admin"})
    assert response.status_code in {401, 422}


@pytest.mark.parametrize('value', [0, 3, 6.2, 100])
def test_grade_remains_percentage(client, prepared, value):
    teacher, course, student, _ = prepared
    path = f'/api/asignaturas/{course.id}'
    assert client.post(path + '/cerrar-nota', headers=headers(teacher), json={"estudiante_id": student.id, "nota_final": value, "justificacion": "Evaluación docente documentada"}).status_code == 200
    assert client.get(path + '/panel', headers=headers(teacher)).json()["estudiantes"][0]["pct_logro_final"] == value
    assert client.post(path + '/cerrar-nota', headers=headers(teacher), json={"estudiante_id": student.id, "nota_final": 60, "justificacion": "  "}).status_code == 422


def test_citation_lifecycle(client, prepared):
    teacher, course, student, _ = prepared
    path = f'/api/asignaturas/{course.id}/citas'
    response = client.post(path, headers=headers(teacher), json={"estudiante_id": student.id, "fecha": "2030-11-20T13:00:00Z", "bloque": "10:00 - 10:15"})
    assert response.status_code == 200
    identifier = response.json()['id']
    assert client.put(f'{path}/{identifier}', headers=headers(teacher), json={"estado": "realizada", "acuerdos": "Defendió la metodología"}).json()['estado'] == 'realizada'
    assert client.get(path, headers=headers(teacher)).json()[0]['acuerdos'] == 'Defendió la metodología'


@pytest.mark.parametrize('provider', ['ollama', 'openai', 'anthropic'])
def test_llm_provider_requests(provider, monkeypatch):
    monkeypatch.setattr(settings, 'LLM_PROVIDER', provider)
    monkeypatch.setattr(settings, 'LLM_API_KEY', 'test-key')
    monkeypatch.setattr(settings, 'LLM_BASE_URL', 'https://example.test/v1')
    captured = []
    def handler(request):
        captured.append(request)
        content = '{"ok": true}'
        body = {'message': {'content': content}} if provider == 'ollama' else {'choices': [{'message': {'content': content}}]} if provider == 'openai' else {'content': [{'type': 'text', 'text': content}]}
        return httpx.Response(200, json=body)
    original = httpx.AsyncClient
    monkeypatch.setattr(llm_service.httpx, 'AsyncClient', lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs))
    assert asyncio.run(llm_service.request_json('JSON', 'Pregunta')) == {'ok': True}
    assert len(captured) == 1
    assert captured[0].url.path.endswith({'ollama': '/api/chat', 'openai': '/chat/completions', 'anthropic': '/messages'}[provider])


def test_csv_bom_and_missing_values(client, seeded_teacher):
    teacher, course = seeded_teacher['teacher'], seeded_teacher['course']
    response = client.post(f'/api/asignaturas/{course.id}/estudiantes/csv', headers=headers(teacher), files={'file': ('students.csv', '\ufeffnombre,correo,rut\nMaría,maria@example.cl\nFalta\n'.encode('utf-8'), 'text/csv')})
    assert response.status_code == 200
    assert response.json()['cargados_exitosamente'] == 1
    assert len(response.json()['errores']) == 1


def test_teacher_websocket_requires_authentication(client, seeded_teacher):
    from starlette.websockets import WebSocketDisconnect
    course = seeded_teacher['course']
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f'/ws/panel/{course.id}'):
            pass
    teacher = seeded_teacher['teacher']
    token = create_access_token({'sub': str(teacher.id)})
    with client.websocket_connect(f'/ws/panel/{course.id}?token={token}') as ws:
        ws.send_json({'type': 'PING', 'ts': 1})
        assert ws.receive_json()['type'] == 'PONG'


def test_real_pdf_upload_and_invalid_batch(client, db_session, seeded_teacher, tmp_path, monkeypatch):
    import pymupdf
    teacher, course = seeded_teacher['teacher'], seeded_teacher['course']
    monkeypatch.setattr(settings, 'WORKS_DIR', tmp_path)
    monkeypatch.setattr(settings, 'LLM_PROVIDER', 'mock')
    student = models.Estudiante(nombre='María Pérez', correo='maria.perez@example.cl', asignatura_id=course.id)
    db_session.add(student); db_session.commit()
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72,72), 'Arquitectura del sistema. Usamos una base de datos relacional para preservar la consistencia.')
    pdf = document.tobytes(); document.close()
    response = client.post(f'/api/asignaturas/{course.id}/trabajos/upload', headers=headers(teacher), data={'estudiante_id': student.id}, files={'file': ('../../informe.pdf', pdf, 'application/pdf')})
    assert response.status_code == 200
    result = client.get(f'/api/asignaturas/{course.id}/estudiantes/{student.id}/evaluacion', headers=headers(teacher)).json()
    questions = client.get(f"/api/evaluaciones/{result['evaluacion_id']}/preguntas", headers=headers(teacher)).json()
    assert len(questions) == 15
    assert sum(q['seleccionada'] for q in questions) == 5
    assert len(list(tmp_path.rglob('*.pdf'))) == 1
    # An invalid document in a batch must be reported as a failure.
    response = client.post(f'/api/asignaturas/{course.id}/trabajos/batch', headers=headers(teacher), files=[('files', ('maria.perez.pdf', b'not a pdf', 'application/pdf'))])
    assert response.status_code == 200
    assert response.json()['asociados_y_evaluados'] == 0
    assert response.json()['no_asociados']


def test_edit_questions_and_validate_selection(client, db_session, seeded_teacher):
    teacher, course = seeded_teacher['teacher'], seeded_teacher['course']
    student = models.Estudiante(nombre='Alumno', correo='edit@example.cl', asignatura_id=course.id)
    student.trabajo = models.Trabajo(markdown='Informe', estado='analizado')
    student.trabajo.evaluacion = models.Evaluacion(nota=5, pct_ia=10, feedback={}, desglose={})
    question = models.Pregunta(texto='Original', alternativas=[{'id':'A','texto':'Correcta','es_correcta':True},{'id':'B','texto':'Otra','es_correcta':False}])
    student.trabajo.evaluacion.preguntas.append(question)
    db_session.add(student); db_session.commit()
    assert client.put(f'/api/preguntas/{question.id}', headers=headers(teacher), json={'texto':'Editada'}).json()['texto'] == 'Editada'
    assert client.put(f'/api/preguntas/{question.id}', headers=headers(teacher), json={'alternativas':[{'id':'A','texto':'Una','es_correcta':False},{'id':'B','texto':'Dos','es_correcta':False}]}).status_code == 422
    path = f'/api/evaluaciones/{student.trabajo.evaluacion.id}/seleccionar'
    assert client.post(path, headers=headers(teacher), json={'pregunta_ids':[999999]}).status_code == 422
    assert client.post(path, headers=headers(teacher), json={'pregunta_ids':[question.id]}).status_code == 200


def test_invalid_llm_response_stops_processing(monkeypatch):
    monkeypatch.setattr(settings, 'LLM_PROVIDER', 'openai')
    monkeypatch.setattr(settings, 'LLM_API_KEY', 'test')
    async def invalid(*args, **kwargs):
        return {'porcentaje_logro': 'invalido'}
    monkeypatch.setattr(llm_service, 'request_json', invalid)
    with pytest.raises(llm_service.LLMUnavailable):
        asyncio.run(llm_service.evaluate_submission_llm('# Informe\nResultados y metodología.'))
    with pytest.raises(llm_service.LLMUnavailable):
        asyncio.run(llm_service.generate_question_pool_llm('Informe', pool_size=10))


def test_student_management_and_material_removal(client, seeded_teacher, tmp_path, monkeypatch):
    teacher, course = seeded_teacher['teacher'], seeded_teacher['course']
    auth = headers(teacher); root = f'/api/asignaturas/{course.id}'
    monkeypatch.setattr(settings, 'MATERIALS_DIR', tmp_path)
    created = client.post(root+'/estudiantes', headers=auth, json={'nombre':'Prueba', 'correo':'new@example.cl'})
    assert created.status_code == 200
    sid = created.json()['id']
    assert client.put(f'{root}/estudiantes/{sid}', headers=auth, json={'nombre':'Actualizado','correo':'new@example.cl','rut':'123'}).json()['nombre'] == 'Actualizado'
    assert client.post(root+'/estudiantes', headers=auth, json={'nombre':'Duplicado','correo':'new@example.cl'}).status_code == 409
    material = client.post(root+'/materiales', headers=auth, data={'nombre':'Guía','tipo':'guia'}, files={'file':('guia.md',b'# Material','text/markdown')})
    assert material.status_code == 200
    assert client.delete(f"{root}/materiales/{material.json()['id']}", headers=auth).status_code == 200
    assert client.get(root+'/materiales', headers=auth).json() == []


def test_modern_reports_preserve_course_access(client, db_session, prepared):
    teacher, course, student, token = prepared
    root = f'/api/asignaturas/{course.id}'
    works = client.get(root+'/trabajos', headers=headers(teacher))
    assert works.status_code == 200
    assert works.json()[0]['estudiante_id'] == student.id
    assert client.get(f'/api/trabajos/{student.trabajo.id}', headers=headers(teacher)).json()['markdown']
    other=models.Usuario(nombre='Otro',correo='bridge@example.cl',contrasena=hash_password('password123'),rol='docente')
    db_session.add(other);db_session.commit()
    assert client.get(f'/api/trabajos/{student.trabajo.id}',headers=headers(other)).status_code == 403
    assert client.post(f'/api/trabajos/{student.trabajo.id}/reanalizar',headers=headers(teacher)).status_code == 409


def test_teacher_availability_validation(client, db_session, seeded_teacher):
    auth=headers(seeded_teacher['teacher'])
    data={'day_of_week':0,'start_time':'09:00','end_time':'11:00'}
    response=client.post('/api/disponibilidad',headers=auth,json=data)
    assert response.status_code == 200
    assert client.post('/api/disponibilidad',headers=auth,json=data).status_code == 409
    assert client.post('/api/disponibilidad',headers=auth,json={**data,'start_time':'12:00'}).status_code == 422
    assert client.post('/api/disponibilidad',headers=auth,json={**data,'day_of_week':7}).status_code == 422
    assert len(client.get('/api/disponibilidad',headers=auth).json()) == 1
    assert client.delete(f"/api/disponibilidad/{response.json()['id']}",headers=auth).status_code == 200
    assert client.get('/api/disponibilidad',headers=auth).json() == []


def test_modern_title_persists_and_metrics_require_admin(client, seeded_teacher):
    teacher,course=seeded_teacher['teacher'],seeded_teacher['course']
    response=client.put(f'/api/asignaturas/{course.id}',headers=headers(teacher),json={'parametros':{'titulo_evaluacion':'Defensa de arquitectura'}})
    assert response.status_code == 200
    assert response.json()['parametros']['titulo_evaluacion'] == 'Defensa de arquitectura'
    assert client.get('/api/system/metrics',headers=headers(teacher)).status_code == 403


def test_admin_removes_student_and_revokes_active_flash_link(client, db_session, prepared, seeded_admin):
    teacher, course, student, token = prepared
    assert client.get(f'/api/flash-test/{token}/info').status_code == 200
    assert client.delete(f'/api/asignaturas/{course.id}/estudiantes/{student.id}', headers=headers(seeded_admin)).status_code == 200
    assert client.get(f'/api/flash-test/{token}/info').status_code == 410
    assert client.post(f'/api/flash-test/{token}/start').status_code == 410
    assert all(s['id'] != student.id for s in client.get(f'/api/asignaturas/{course.id}/estudiantes', headers=headers(teacher)).json())
    assert db_session.get(models.Estudiante, student.id) is not None
    assert db_session.query(models.FlashTest).filter_by(token=token).one().estado == 'expirado'
