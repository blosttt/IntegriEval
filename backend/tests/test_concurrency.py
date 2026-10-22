from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app import models
from backend.app.database import Base, get_db
from backend.app.routers import panel
from backend.app.auth import create_access_token


def test_concurrent_appointments_cannot_reserve_same_slot(tmp_path):
    engine=create_engine('sqlite:///'+str(tmp_path/'concurrent.db'),connect_args={'check_same_thread':False,'timeout':10})
    Base.metadata.create_all(engine);factory=sessionmaker(bind=engine)
    with factory() as db:
        user=models.Usuario(nombre='Docente',correo='concurrent@example.invalid',contrasena='unused',rol='docente')
        db.add(user);db.flush()
        course=models.Asignatura(nombre='Curso',periodo='S1',ano=2026,docente_id=user.id,parametros={})
        db.add(course);db.flush()
        student=models.Estudiante(nombre='Alumno',correo='concurrent.student@example.invalid',asignatura_id=course.id)
        db.add(student);db.commit()
        course_id,student_id,user_id=course.id,student.id,user.id
    app=FastAPI();app.include_router(panel.router)
    def session():
        with factory() as db:yield db
    app.dependency_overrides[get_db]=session
    h={'Authorization':'Bearer '+create_access_token({'sub':str(user_id)})}
    date=(datetime.now(ZoneInfo('America/Santiago'))+timedelta(days=3)).replace(hour=10,minute=0,second=0,microsecond=0)
    data={'estudiante_id':student_id,'fecha':date.isoformat(),'bloque':'10:00 - 10:30'}
    barrier=Barrier(2)
    with TestClient(app) as first,TestClient(app) as second,ThreadPoolExecutor(max_workers=2) as executor:
        def reserve(client):
            barrier.wait();return client.post(f'/api/asignaturas/{course_id}/citas',headers=h,json=data).status_code
        results=list(executor.map(reserve,[first,second]))
    assert sorted(results)==[200,409]
    with factory() as db:assert db.query(models.Cita).count()==1
    engine.dispose()


def test_expired_session_requires_login(client,seeded_teacher):
    token=create_access_token({'sub':str(seeded_teacher['teacher'].id)},timedelta(seconds=-1))
    assert client.get('/api/auth/me',headers={'Authorization':'Bearer '+token}).status_code==401
