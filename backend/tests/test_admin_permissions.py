from backend.app import models
from backend.app.auth import create_access_token, hash_password


def auth(user):
    return {'Authorization': 'Bearer ' + create_access_token({'sub': str(user.id)})}


def test_only_admin_creates_courses_and_accounts(client, seeded_teacher, seeded_admin):
    teacher = seeded_teacher['teacher']
    course = {'nombre': 'Curso administrado', 'periodo': 'Semestre 1', 'ano': 2027}
    assert client.post('/api/asignaturas', headers=auth(teacher), json=course).status_code == 403
    created = client.post('/api/asignaturas', headers=auth(seeded_admin), json=course)
    assert created.status_code == 200
    identifier = created.json()['id']
    assert all(c['id'] != identifier for c in client.get('/api/asignaturas', headers=auth(teacher)).json())
    assert client.post('/api/auth/register', json={'nombre': 'No autorizado', 'correo': 'public@example.cl', 'contrasena': 'password123'}).status_code == 401
    assert client.post('/api/admin/profesores', headers=auth(teacher), json={'nombre': 'No autorizado', 'correo': 'new@example.cl', 'contrasena': 'password123'}).status_code == 403
    assert client.get('/api/admin/profesores', headers=auth(teacher)).status_code == 403


def test_assignment_grants_and_removal_revokes_all_course_access(client, seeded_admin, seeded_teacher):
    teacher = seeded_teacher['teacher']
    course = client.post('/api/asignaturas', headers=auth(seeded_admin), json={'nombre': 'Asignación', 'periodo': 'S1', 'ano': 2027}).json()
    cid = course['id']
    assert client.get(f'/api/asignaturas/{cid}/estudiantes', headers=auth(teacher)).status_code == 403
    assert client.post(f'/api/admin/asignaturas/{cid}/profesores', headers=auth(seeded_admin), json={'usuario_id': teacher.id}).status_code == 200
    assert any(c['id'] == cid for c in client.get('/api/asignaturas', headers=auth(teacher)).json())
    student = client.post(f'/api/asignaturas/{cid}/estudiantes', headers=auth(teacher), json={'nombre': 'Alumno asignado', 'correo': 'assigned@example.cl'})
    assert student.status_code == 200
    sid = student.json()['id']
    assert client.put(f'/api/asignaturas/{cid}/estudiantes/{sid}', headers=auth(teacher), json={'nombre': 'Alumno editado', 'correo': 'assigned@example.cl'}).status_code == 200
    assert client.put(f'/api/asignaturas/{cid}', headers=auth(teacher), json={'nombre': 'Renombrar curso'}).status_code == 403
    assert client.put(f'/api/asignaturas/{cid}', headers=auth(teacher), json={'parametros': {'prompt_custom': 'Pauta docente'}}).status_code == 200
    assert client.delete(f'/api/admin/asignaturas/{cid}/profesores/{teacher.id}', headers=auth(seeded_admin)).status_code == 200
    assert client.get(f'/api/asignaturas/{cid}/panel', headers=auth(teacher)).status_code == 403
    assert client.put(f'/api/asignaturas/{cid}/estudiantes/{sid}', headers=auth(teacher), json={'nombre': 'Intento', 'correo': 'assigned@example.cl'}).status_code == 403


def test_removing_legacy_owner_does_not_leave_access(client, seeded_admin, seeded_teacher):
    course, teacher = seeded_teacher['course'], seeded_teacher['teacher']
    assert client.delete(f'/api/admin/asignaturas/{course.id}/profesores/{teacher.id}', headers=auth(seeded_admin)).status_code == 200
    assert client.get(f'/api/asignaturas/{course.id}', headers=auth(teacher)).status_code == 403
    assert client.get(f'/api/asignaturas/{course.id}', headers=auth(seeded_admin)).status_code == 200


def test_teacher_edit_deactivate_and_restore_revokes_existing_token(client, seeded_admin):
    data = {'nombre': 'Docente nuevo', 'correo': 'managed@example.cl', 'contrasena': 'Password123!'}
    created = client.post('/api/admin/profesores', headers=auth(seeded_admin), json=data)
    assert created.status_code == 200
    uid = created.json()['id']
    login = client.post('/api/auth/login', json={'correo': data['correo'], 'contrasena': data['contrasena']})
    assert login.status_code == 200
    headers = {'Authorization': 'Bearer ' + login.json()['access_token']}
    assert client.delete(f'/api/admin/profesores/{uid}', headers=auth(seeded_admin)).status_code == 200
    assert client.get('/api/auth/me', headers=headers).status_code == 403
    assert client.post('/api/auth/login', json={'correo': data['correo'], 'contrasena': data['contrasena']}).status_code == 403
    assert client.put(f'/api/admin/profesores/{uid}', headers=auth(seeded_admin), json={'nombre': 'Nombre editado', 'correo': data['correo'], 'active': True}).status_code == 200
    assert client.get('/api/auth/me', headers=headers).json()['nombre'] == 'Nombre editado'


def test_multiple_teachers_are_independently_assigned(client, db_session, seeded_admin, seeded_teacher):
    course = seeded_teacher['course']
    other = models.Usuario(nombre='Segundo docente', correo='second@example.cl', contrasena=hash_password('password123'), rol='docente')
    db_session.add(other)
    db_session.commit()
    assert client.post(f'/api/admin/asignaturas/{course.id}/profesores', headers=auth(seeded_admin), json={'usuario_id': other.id}).status_code == 200
    assert client.get(f'/api/asignaturas/{course.id}/panel', headers=auth(other)).status_code == 200
    assert client.get(f'/api/asignaturas/{course.id}/panel', headers=auth(seeded_teacher['teacher'])).status_code == 200
    assert len(client.get(f'/api/admin/asignaturas/{course.id}/profesores', headers=auth(seeded_admin)).json()) == 2


def test_archiving_course_hides_it_and_keeps_history(client, db_session, seeded_admin, seeded_teacher):
    course = seeded_teacher['course']
    assert client.delete(f'/api/admin/asignaturas/{course.id}', headers=auth(seeded_admin)).status_code == 200
    assert db_session.get(models.Asignatura, course.id) is not None
    assert client.get(f'/api/asignaturas/{course.id}', headers=auth(seeded_teacher['teacher'])).status_code == 404
    assert all(c['id'] != course.id for c in client.get('/api/asignaturas', headers=auth(seeded_admin)).json())
