from datetime import datetime, timezone, timedelta
import json
import pytest
from sqlalchemy import create_engine, inspect, text
from backend.app import models as m
from backend.app.auth import create_access_token
from backend.app.migrations import upgrade_questions


def headers(user):
    return {'Authorization': 'Bearer ' + create_access_token({'sub': str(user.id)})}


@pytest.fixture
def pool(client, db_session, seeded_teacher):
    teacher, course = seeded_teacher['teacher'], seeded_teacher['course']
    student = m.Estudiante(nombre='Alumno sintético', correo='desarrollo@example.invalid', asignatura_id=course.id)
    student.trabajo = m.Trabajo(markdown='Informe técnico', estado='analizado')
    student.trabajo.evaluacion = m.Evaluacion(nota=5, pct_ia=0, feedback={}, desglose={'porcentaje_logro':'75%'})
    db_session.add(student); db_session.commit()
    evaluation = student.trabajo.evaluacion
    choice = client.post(f'/api/evaluaciones/{evaluation.id}/preguntas', headers=headers(teacher), json={
        'texto':'Selección', 'seleccionada':True,
        'alternativas':[{'id':'A','texto':'Correcta','es_correcta':True},{'id':'B','texto':'Otra','es_correcta':False}],
    })
    development = client.post(f'/api/evaluaciones/{evaluation.id}/preguntas', headers=headers(teacher), json={
        'texto':'Explica tu método', 'tipo':'desarrollo', 'seleccionada':True,
        'criterios_evaluacion':'CRITERIO_PRIVADO', 'respuesta_referencia':'REFERENCIA_PRIVADA',
    })
    assert choice.status_code == development.status_code == 200
    return {'teacher':teacher,'course':course,'student':student,'evaluation':evaluation,
            'choice':choice.json(),'development':development.json()}


def dispatch(client, pool):
    response = client.post(f"/api/asignaturas/{pool['course'].id}/flash-test/despacho", headers=headers(pool['teacher']))
    assert response.status_code == 200 and response.json()['total_despachados'] == 1
    return response.json()['items'][0]['token']


def reach_development(client, pool):
    token = dispatch(client, pool)
    root = f'/api/flash-test/{token}'
    assert client.post(root+'/start').status_code == 200
    assert client.post(root+'/answer', json={'question_id':pool['choice']['id'],'answer':'A'}).status_code == 200
    return root, token


def test_create_update_development_and_option_validation(client, pool):
    question = pool['development']
    assert question['tipo'] == 'desarrollo' and question['alternativas'] == []
    endpoint = f"/api/preguntas/{question['id']}"
    auth = headers(pool['teacher'])
    assert client.put(endpoint, headers=auth, json={'criterios_evaluacion':'Nueva pauta','texto':'Nueva pregunta'}).status_code == 200
    assert client.put(endpoint, headers=auth, json={'criterios_evaluacion':'   '}).status_code == 422
    assert client.put(f"/api/preguntas/{pool['choice']['id']}", headers=auth, json={'alternativas':[]}).status_code == 422
    base = f"/api/evaluaciones/{pool['evaluation'].id}/preguntas"
    assert client.post(base, headers=auth, json={'texto':'Sin pauta','tipo':'desarrollo'}).status_code == 422
    assert client.post(base, headers=auth, json={'texto':' ','tipo':'desarrollo','criterios_evaluacion':'Pauta'}).status_code == 422


def test_private_rubric_not_sent_to_student(client, pool):
    token = dispatch(client, pool)
    response = client.get(f'/api/flash-test/{token}/info')
    payload = json.dumps(response.json())
    assert 'REFERENCIA_PRIVADA' not in payload and 'CRITERIO_PRIVADO' not in payload
    assert 'respuesta_referencia' not in payload and 'criterios_evaluacion' not in payload and 'es_correcta' not in payload
    assert response.json()['preguntas'][1]['tipo'] == 'desarrollo'
    assert client.get(f"/api/evaluaciones/{pool['evaluation'].id}/desarrollo").status_code == 401
    assert client.put(f"/api/preguntas/{pool['development']['id']}", headers=headers(pool['teacher']), json={'texto':'Cambio'}).status_code == 409


def test_draft_recovery_submission_manual_review_and_grade_closure(client, db_session, pool):
    root, token = reach_development(client, pool)
    question = pool['development']['id']
    assert client.post(root+'/draft', json={'question_id':question,'answer':'Mi borrador'}).status_code == 200
    recovered = client.get(root+'/info').json()
    assert recovered['pregunta_actual'] == 1 and recovered['respuestas'][str(question)] == 'Mi borrador'
    assert client.post(root+'/answer', json={'question_id':question,'answer':' '}).status_code == 422
    assert client.post(root+'/draft', json={'question_id':question,'answer':'x'*5001}).status_code == 422
    result = client.post(root+'/answer', json={'question_id':question,'answer':'Respuesta final escrita'}).json()
    assert result['estado'] == 'completado' and result['puntaje'] is None
    response = client.post(root+'/submit', json={'token':token,'respuestas':{}}).json()
    assert response['revision_pendiente'] and response['desarrollo_pendientes'] == 1
    assert response['respuestas_correctas'] == 1 and response['porcentaje_logro'] is None
    course, teacher = pool['course'], pool['teacher']
    panel = client.get(f'/api/asignaturas/{course.id}/panel',headers=headers(teacher)).json()['estudiantes'][0]
    assert panel['desarrollo_pendiente'] and panel['puntaje_flash'] is None
    close = f'/api/asignaturas/{course.id}/cerrar-nota'
    close_data = {'estudiante_id':pool['student'].id,'nota_final':75,'justificacion':'Criterio pedagógico'}
    assert client.post(close, headers=headers(teacher), json=close_data).status_code == 409
    review = client.get(f"/api/evaluaciones/{pool['evaluation'].id}/desarrollo", headers=headers(teacher)).json()
    assert review['preguntas'][0]['respuesta'] == 'Respuesta final escrita'
    assert review['preguntas'][0]['criterios_evaluacion'] == 'CRITERIO_PRIVADO'
    route = f"/api/flash-tests/{review['test_id']}/desarrollo"
    data = {'revisiones':[{'pregunta_id':question,'puntaje':50,'comentario':'Explica parte del método; falta justificar las decisiones.'}]}
    reviewed = client.put(route, headers=headers(teacher), json=data)
    assert reviewed.status_code == 200 and reviewed.json()['puntaje'] == 75
    final = client.post(root+'/submit', json={'token':token,'respuestas':{}}).json()
    assert not final['revision_pendiente'] and final['porcentaje_logro'] == 75
    assert client.post(close, headers=headers(teacher), json=close_data).status_code == 200
    assert client.put(route, headers=headers(teacher), json=data).status_code == 409
    assert db_session.query(m.AuditLog).filter_by(accion='REVISAR_DESARROLLO').count() == 1


@pytest.mark.parametrize('draft, pending, score', [('',False,50),('Texto al vencer',True,None)])
def test_timeout_preserves_saved_text_or_counts_blank_as_zero(client, db_session, pool, draft, pending, score):
    root, token = reach_development(client, pool)
    question = pool['development']['id']
    assert client.post(root+'/draft', json={'question_id':question,'answer':draft}).status_code == 200
    test = db_session.query(m.FlashTest).filter_by(token=token).one()
    state = db_session.get(m.FlashTestState, test.id)
    state.inicio_pregunta = datetime.now(timezone.utc) - timedelta(seconds=test.tiempo_limite_segundos+1)
    db_session.commit()
    info = client.get(root+'/info').json()
    assert info['estado'] == 'completado'
    result = client.post(root+'/submit', json={'token':token,'respuestas':{}}).json()
    assert result['revision_pendiente'] == pending and result['porcentaje_logro'] == score
    assert client.post(root+'/draft', json={'question_id':question,'answer':'Cambio tardío'}).status_code == 409
    assert client.get(root+'/info').json()['respuestas'][str(question)] == draft


def test_drafts_cannot_change_other_questions_or_choices(client, pool):
    token = dispatch(client, pool)
    root = f'/api/flash-test/{token}'
    assert client.post(root+'/draft',json={'question_id':pool['development']['id'],'answer':'Antes de iniciar'}).status_code == 409
    client.post(root+'/start')
    assert client.post(root+'/draft',json={'question_id':pool['development']['id'],'answer':'Pregunta futura'}).status_code == 409
    assert client.post(root+'/draft',json={'question_id':pool['choice']['id'],'answer':'No es desarrollo'}).status_code == 409


def test_manual_review_enforces_course_and_question_ids(client, db_session, pool):
    root, token = reach_development(client, pool)
    client.post(root+'/answer',json={'question_id':pool['development']['id'],'answer':'Explicación'})
    test = db_session.query(m.FlashTest).filter_by(token=token).one()
    route = f'/api/flash-tests/{test.id}/desarrollo'
    other = m.Usuario(nombre='Otro docente',correo='other@example.invalid',contrasena='unused',rol='docente')
    db_session.add(other); db_session.commit()
    data = {'revisiones':[{'pregunta_id':pool['development']['id'],'puntaje':80,'comentario':'Justificado'}]}
    assert client.put(route,headers=headers(other),json=data).status_code == 403
    for field, value in [('pregunta_id',pool['choice']['id']),('puntaje',101),('comentario',' ')]:
        bad = {'revisiones':[{**data['revisiones'][0],field:value}]}
        assert client.put(route,headers=headers(pool['teacher']),json=bad).status_code == 422


def test_review_is_independent_of_current_question_type_and_snapshot(client, db_session, pool):
    root, token = reach_development(client, pool)
    # Published wording and rubric come from the immutable dispatch snapshot.
    question = db_session.get(m.Pregunta,pool['development']['id'])
    question.criterios_evaluacion = 'Cambio directo de fixture'
    db_session.commit()
    client.post(root+'/answer',json={'question_id':question.id,'answer':'A'})
    review = client.get(f"/api/evaluaciones/{pool['evaluation'].id}/desarrollo",headers=headers(pool['teacher'])).json()
    assert review['preguntas'][0]['criterios_evaluacion'] == 'CRITERIO_PRIVADO'
    assert review['revision_pendiente'] and review['puntaje'] is None


def test_old_question_migration_preserves_data_and_is_idempotent(tmp_path):
    engine = create_engine('sqlite:///' + str(tmp_path/'legacy.db'))
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE preguntas (id INTEGER PRIMARY KEY, texto TEXT, alternativas JSON)'))
        connection.execute(text("INSERT INTO preguntas VALUES (1, 'Pregunta antigua', '[]')"))
    upgrade_questions(engine); upgrade_questions(engine)
    assert {'tipo','respuesta_referencia','criterios_evaluacion'} <= {column['name'] for column in inspect(engine).get_columns('preguntas')}
    with engine.connect() as connection:
        assert connection.execute(text('SELECT texto,tipo FROM preguntas')).one() == ('Pregunta antigua','alternativas')
    assert len(list(tmp_path.glob('legacy.db.before-development-*.bak'))) == 1
    engine.dispose()


def test_legacy_completed_score_is_returned_without_regrading(client, db_session, pool):
    client.put(f"/api/preguntas/{pool['development']['id']}", headers=headers(pool['teacher']), json={'seleccionada':False})
    token = dispatch(client, pool)
    root = f'/api/flash-test/{token}'
    client.post(root+'/start')
    client.post(root+'/answer',json={'question_id':pool['choice']['id'],'answer':'A'})
    test = db_session.query(m.FlashTest).filter_by(token=token).one()
    test.puntaje = 87.5  # Imported historical score remains authoritative.
    db_session.commit()
    result = client.post(root+'/submit',json={'token':token,'respuestas':{}}).json()
    assert result['puntaje'] == result['porcentaje_logro'] == 87.5
