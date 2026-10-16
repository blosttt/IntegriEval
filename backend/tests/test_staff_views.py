from backend.app import models
from backend.app.auth import create_access_token, hash_password


def auth(user):
    return {'Authorization': 'Bearer ' + create_access_token({'sub': str(user.id)})}


def assistant(db, course):
    user = models.Usuario(nombre='Ayudante de pruebas', correo='assistant.views@example.cl', contrasena=hash_password('Password123!'), rol='ayudante')
    db.add(user)
    db.flush()
    db.add(models.CourseAssistant(asignatura_id=course.id, usuario_id=user.id))
    db.commit()
    return user


def test_assistant_can_evaluate_but_cannot_change_roster(client, db_session, seeded_teacher, tmp_path, monkeypatch):
    from backend.app.config import settings
    course = seeded_teacher['course']
    user = assistant(db_session, course)
    student = models.Estudiante(nombre='Alumno del curso', correo='readonly@example.cl', asignatura_id=course.id)
    db_session.add(student)
    db_session.commit()
    h, root = auth(user), f'/api/asignaturas/{course.id}'
    assert client.get(root+'/estudiantes', headers=h).status_code == 200
    assert client.post(root+'/estudiantes', headers=h, json={'nombre':'Otro','correo':'new@example.cl'}).status_code == 403
    assert client.put(root+f'/estudiantes/{student.id}', headers=h, json={'nombre':'Cambio','correo':student.correo}).status_code == 403
    assert client.delete(root+f'/estudiantes/{student.id}', headers=h).status_code == 403
    assert client.post(root+'/estudiantes/csv', headers=h, files={'file':('students.csv',b'nombre,correo\nOtro,other@example.cl','text/csv')}).status_code == 403
    assert client.put(root, headers=h, json={'parametros':{'prompt_custom':'Pauta preparada por el ayudante'}}).status_code == 200
    assert client.put(root, headers=h, json={'nombre':'Cambio de asignatura'}).status_code == 403
    monkeypatch.setattr(settings, 'MATERIALS_DIR', tmp_path)
    material = client.post(root+'/materiales', headers=h, data={'nombre':'Guía','tipo':'guia'}, files={'file':('guia.md',b'# Contexto academico','text/markdown')})
    assert material.status_code == 200
    assert client.delete(root+f"/materiales/{material.json()['id']}", headers=h).status_code == 200
    assert client.post('/api/disponibilidad', headers=h, json={'day_of_week':2,'start_time':'10:00','end_time':'11:00'}).status_code == 200


def test_superadmin_profile_scope_does_not_impersonate_teacher(client, db_session, seeded_admin, seeded_teacher):
    teacher, course = seeded_teacher['teacher'], seeded_teacher['course']
    other = models.Usuario(nombre='Docente sin relación', correo='unrelated.views@example.cl', contrasena=hash_password('Password123!'), rol='docente')
    db_session.add(other)
    db_session.flush()
    other_course = models.Asignatura(nombre='Otro curso', periodo='S1', ano=2027, docente_id=other.id)
    db_session.add(other_course)
    db_session.commit()
    path = f'/api/admin/profesores/{teacher.id}'
    assert client.get(path+'/asignaturas', headers=auth(teacher)).status_code == 403
    assert client.get(path+'/asignaturas', headers=auth(seeded_admin)).json()[0]['id'] == course.id
    assert all(c['id'] != other_course.id for c in client.get(path+'/asignaturas', headers=auth(seeded_admin)).json())
    assert client.get('/api/auth/me', headers=auth(seeded_admin)).json()['rol'] == 'admin'
    assert client.put(f'/api/asignaturas/{course.id}', headers=auth(seeded_admin), json={'nombre':'Administrado en vista del docente'}).status_code == 200
    logs = client.get('/api/audit', headers=auth(seeded_admin)).json()
    record = next(log for log in logs if log['accion'] == 'ACTUALIZAR_PARAMETROS_ASIGNATURA')
    assert record['usuario_id'] == seeded_admin.id


def test_admin_can_create_assistant_and_manage_their_courses(client, db_session, seeded_admin):
    h = auth(seeded_admin)
    user = client.post('/api/admin/profesores', headers=h, json={'nombre':'Nuevo ayudante','correo':'created.assistant@example.cl','contrasena':'Password123!','rol':'ayudante'})
    assert user.status_code == 200
    uid = user.json()['id']
    assert user.json()['rol'] == 'ayudante'
    course = client.post(f'/api/admin/profesores/{uid}/asignaturas', headers=h, json={'nombre':'Curso de ayudantía','periodo':'S2','ano':2027})
    assert course.status_code == 200
    cid = course.json()['id']
    login = client.post('/api/auth/login', json={'correo':'created.assistant@example.cl','contrasena':'Password123!'})
    ah = {'Authorization': 'Bearer ' + login.json()['access_token']}
    assert any(c['id'] == cid for c in client.get('/api/asignaturas', headers=ah).json())
    assert client.get(f'/api/admin/profesores/{uid}/asignaturas', headers=h).json()[0]['id'] == cid
    assert client.delete(f'/api/admin/asignaturas/{cid}/profesores/{uid}', headers=h).status_code == 200
    assert client.get(f'/api/asignaturas/{cid}/panel', headers=ah).status_code == 403


def test_admin_edits_teacher_availability_without_changing_owner(client, db_session, seeded_admin, seeded_teacher):
    tid = seeded_teacher['teacher'].id
    path = f'/api/admin/profesores/{tid}/disponibilidad'
    created = client.post(path, headers=auth(seeded_admin), json={'day_of_week':3,'start_time':'10:00','end_time':'12:00'})
    assert created.status_code == 200
    assert created.json()['usuario_id'] == tid
    assert client.get(path, headers=auth(seeded_teacher['teacher'])).status_code == 403
    assert len(client.get('/api/disponibilidad', headers=auth(seeded_teacher['teacher'])).json()) == 1
    assert client.delete(path+f"/{created.json()['id']}", headers=auth(seeded_admin)).status_code == 200
