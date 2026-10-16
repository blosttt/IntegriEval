from datetime import datetime, timedelta, timezone
from backend.app import models as m
from backend.app.auth import create_access_token


def test_multiple_evaluations_keep_work_tests_and_results_separate(client, db_session, seeded_teacher):
    teacher, course = seeded_teacher['teacher'], seeded_teacher['course']
    headers={'Authorization':'Bearer '+create_access_token({'sub':str(teacher.id)})}
    root=f'/api/asignaturas/{course.id}'
    data={'titulo':'Segundo informe','parametros':{'pool_size':10,'num_preguntas_test':1}}
    activity=client.post(root+'/actividades',headers=headers,json=data)
    assert activity.status_code==200, activity.text
    aid=activity.json()['id']
    student=m.Estudiante(nombre='Alumno',correo='multiple@example.invalid',asignatura_id=course.id)
    db_session.add(student); db_session.flush()
    for activity_id, score in ((None,80),(aid,40)):
        work=m.Trabajo(estudiante_id=student.id,actividad_id=activity_id,markdown='Contenido de informe',estado='analizado')
        db_session.add(work);db_session.flush()
        evaluation=m.Evaluacion(trabajo_id=work.id,nota=score,pct_ia=10,feedback={},desglose={'porcentaje_logro':f'{score}%'})
        db_session.add(evaluation);db_session.flush()
        db_session.add(m.Pregunta(evaluacion_id=evaluation.id,texto='¿Cuál?',alternativas=[{'id':'A','texto':'Correcta','es_correcta':True},{'id':'B','texto':'Otra','es_correcta':False}],seleccionada=True))
    db_session.commit()
    assert len(client.get(root+'/actividades',headers=headers).json())==2
    original=client.get(root+'/trabajos',headers=headers).json()
    second=client.get(root+f'/trabajos?actividad_id={aid}',headers=headers).json()
    assert len(original)==len(second)==1
    assert original[0]['id']!=second[0]['id']
    assert client.get(root+'/panel',headers=headers).json()['estudiantes'][0]['pct_logro']==80
    assert client.get(root+f'/panel?actividad_id={aid}',headers=headers).json()['estudiantes'][0]['pct_logro']==40
    first=client.post(root+'/flash-test/despacho',headers=headers,json=[student.id])
    second=client.post(root+f'/flash-test/despacho?actividad_id={aid}',headers=headers,json=[student.id])
    assert first.status_code==second.status_code==200
    assert first.json()['items'][0]['token']!=second.json()['items'][0]['token']
    assert db_session.query(m.Cita).count()==0  # No automatic scheduling.
    when=(datetime.now(timezone.utc)+timedelta(days=5)).replace(hour=10,minute=0,second=0,microsecond=0)
    appointment=client.post(root+'/citas',headers=headers,json={'estudiante_id':student.id,'actividad_id':aid,'fecha':when.isoformat(),'bloque':'10:00 - 10:30'})
    assert appointment.status_code==200,appointment.text
    assert appointment.json()['actividad_id']==aid
    changed=when+timedelta(days=1)
    assert client.put(root+f"/citas/{appointment.json()['id']}",headers=headers,json={'fecha':changed.isoformat(),'bloque':'10:00 - 10:30'}).status_code==200
    assert client.get(root+'/panel',headers=headers).json()['estudiantes'][0]['cita_id'] is None
    assert client.get(root+f'/panel?actividad_id={aid}',headers=headers).json()['estudiantes'][0]['cita_id']==appointment.json()['id']


def test_evaluation_cannot_be_used_across_courses(client, db_session, seeded_teacher):
    teacher, course=seeded_teacher['teacher'],seeded_teacher['course']
    headers={'Authorization':'Bearer '+create_access_token({'sub':str(teacher.id)})}
    other=m.Asignatura(nombre='Otro',periodo='S1',ano=2026,docente_id=teacher.id)
    db_session.add(other);db_session.flush()
    activity=m.Actividad(asignatura_id=other.id,titulo='Privada',parametros={})
    db_session.add(activity);db_session.commit()
    root=f'/api/asignaturas/{course.id}'
    assert client.get(root+f'/panel?actividad_id={activity.id}',headers=headers).status_code==404
    assert client.get(root+f'/trabajos?actividad_id={activity.id}',headers=headers).status_code==404
    assert client.put(root+f'/actividades/{activity.id}',headers=headers,json={'titulo':'Intento','parametros':{}}).status_code==404


def test_sqlite_upgrade_keeps_existing_history_and_allows_second_work(tmp_path):
    from sqlalchemy import create_engine, text, inspect
    from backend.app.migrations import upgrade_activities
    engine=create_engine('sqlite:///'+str(tmp_path/'legacy.db'))
    with engine.begin() as con:
        con.exec_driver_sql('CREATE TABLE trabajos (id INTEGER PRIMARY KEY, estudiante_id INTEGER NOT NULL UNIQUE, pdf_path TEXT, markdown TEXT, estado TEXT, fecha_entrega DATETIME)')
        con.exec_driver_sql("INSERT INTO trabajos VALUES (7,1,NULL,'Informe original','analizado',NULL)")
        con.exec_driver_sql('CREATE TABLE flash_tests (id INTEGER PRIMARY KEY)')
        con.exec_driver_sql('CREATE TABLE citas (id INTEGER PRIMARY KEY)')
        con.exec_driver_sql('CREATE TABLE actividades (id INTEGER PRIMARY KEY)')
        con.exec_driver_sql('CREATE TABLE estudiantes (id INTEGER PRIMARY KEY)')
        con.exec_driver_sql('INSERT INTO estudiantes VALUES (1)')
        con.exec_driver_sql('INSERT INTO actividades VALUES (2)')
    upgrade_activities(engine)
    upgrade_activities(engine)  # Idempotent upgrade.
    with engine.begin() as con:
        assert con.execute(text('SELECT markdown FROM trabajos WHERE id=7')).scalar()=='Informe original'
        con.exec_driver_sql("INSERT INTO trabajos (estudiante_id,actividad_id,markdown) VALUES (1,2,'Segundo informe')")
        assert con.execute(text('SELECT COUNT(*) FROM trabajos')).scalar()==2
    assert 'actividad_id' in {c['name'] for c in inspect(engine).get_columns('citas')}
    assert len(list(tmp_path.glob('*.bak')))==1


def test_upload_second_evaluation_does_not_replace_dispatched_work(client, db_session, seeded_teacher, tmp_path, monkeypatch):
    import pymupdf
    from backend.app.config import settings
    monkeypatch.setattr(settings,'WORKS_DIR',tmp_path)
    monkeypatch.setattr(settings,'LLM_PROVIDER','mock')
    teacher, course=seeded_teacher['teacher'],seeded_teacher['course']
    h={'Authorization':'Bearer '+create_access_token({'sub':str(teacher.id)})}
    student=m.Estudiante(nombre='Alumno',correo='second.upload@example.invalid',asignatura_id=course.id)
    db_session.add(student);db_session.flush()
    work=m.Trabajo(estudiante_id=student.id,markdown='Original',estado='analizado')
    activity=m.Actividad(asignatura_id=course.id,titulo='Nueva',parametros={'pool_size':10,'num_preguntas_test':2})
    db_session.add_all([work,activity,m.FlashTest(estudiante_id=student.id)]);db_session.commit()
    original_id=work.id
    document=pymupdf.open();page=document.new_page();page.insert_text((72,72),'Arquitectura y metodologia del proyecto. Justificamos el uso de una base relacional y pruebas de integracion.')
    pdf=document.tobytes();document.close()
    response=client.post(f'/api/asignaturas/{course.id}/trabajos/upload',headers=h,data={'estudiante_id':student.id,'actividad_id':activity.id},files={'file':('informe.pdf',pdf,'application/pdf')})
    assert response.status_code==200,response.text
    assert response.json()['trabajo_id']!=original_id
    db_session.expire_all()
    assert db_session.get(m.Trabajo,original_id).markdown=='Original'
    assert db_session.query(m.Trabajo).filter_by(estudiante_id=student.id).count()==2
