import asyncio
import json
import pymupdf
from sqlalchemy.orm import Session
from backend.app import models as m
from backend.app.auth import create_access_token
from backend.app.config import settings
from backend.app.services.upload_worker import process_one


def auth(user):
    return {'Authorization':'Bearer '+create_access_token({'sub':str(user.id)})}

def pdf_bytes():
    document=pymupdf.open();page=document.new_page();page.insert_text((72,72),'Arquitectura del proyecto y pruebas. La base de datos relacional conserva los registros de auditoria.')
    content=document.tobytes();document.close();return content

def test_queue_processes_pdf_and_preserves_result(client,db_session,seeded_teacher,tmp_path,monkeypatch):
    monkeypatch.setattr(settings,'UPLOAD_DIR',tmp_path)
    monkeypatch.setattr(settings,'WORKS_DIR',tmp_path/'works')
    monkeypatch.setattr(settings,'LLM_PROVIDER','mock')
    teacher,course=seeded_teacher['teacher'],seeded_teacher['course'];h=auth(teacher)
    student=m.Estudiante(nombre='Alumno',correo='queue@example.invalid',asignatura_id=course.id)
    db_session.add(student);db_session.commit()
    path=f'/api/asignaturas/{course.id}/cargas'
    response=client.post(path,headers=h,data={'estudiante_ids':json.dumps([student.id])},files={'files':('informe.pdf',pdf_bytes(),'application/pdf')})
    assert response.status_code==200,response.text
    job=response.json()['items'][0]
    assert job['status']=='pending' and 'file_path' not in job
    assert client.post(path,headers=h,data={'estudiante_ids':json.dumps([student.id])},files={'files':('otro.pdf',pdf_bytes(),'application/pdf')}).status_code==409
    assert client.put(f'/api/asignaturas/{course.id}/actividades/0/estado',headers=h,json={'estado':'cerrada'}).status_code==409
    factory=lambda:Session(bind=db_session.bind)
    assert asyncio.run(process_one(factory))
    db_session.expire_all()
    status=client.get(path,headers=h).json()[0]
    assert status['status']=='completed',status
    assert status['attempts']==1
    assert db_session.query(m.Trabajo).filter_by(estudiante_id=student.id).one().evaluacion is not None
    assert client.post(path+f"/{job['id']}/cancelar",headers=h).status_code==409

def test_cancel_retry_and_revoked_access(client,db_session,seeded_teacher,tmp_path,monkeypatch):
    monkeypatch.setattr(settings,'UPLOAD_DIR',tmp_path)
    teacher,course=seeded_teacher['teacher'],seeded_teacher['course'];h=auth(teacher)
    student=m.Estudiante(nombre='Alumno',correo='queue.cancel@example.invalid',asignatura_id=course.id)
    db_session.add(student);db_session.commit()
    root=f'/api/asignaturas/{course.id}/cargas'
    result=client.post(root,headers=h,data={'estudiante_ids':json.dumps([student.id])},files={'files':('informe.pdf',pdf_bytes(),'application/pdf')}).json()
    job_id=result['items'][0]['id']
    assert client.post(root+f'/{job_id}/cancelar',headers=h).json()['status']=='cancelled'
    assert client.post(root+f'/{job_id}/reintentar',headers=h).json()['status']=='pending'
    db_session.add(m.AccountStatus(usuario_id=teacher.id,active=False));db_session.commit()
    assert asyncio.run(process_one(lambda:Session(bind=db_session.bind)))
    db_session.expire_all()
    assert db_session.get(m.UploadJob,job_id).status=='failed'
    assert db_session.query(m.Trabajo).count()==0

def test_queue_rejects_invalid_pdf_without_saving(client,db_session,seeded_teacher,tmp_path,monkeypatch):
    monkeypatch.setattr(settings,'UPLOAD_DIR',tmp_path)
    teacher,course=seeded_teacher['teacher'],seeded_teacher['course']
    student=m.Estudiante(nombre='Alumno',correo='queue.invalid@example.invalid',asignatura_id=course.id)
    db_session.add(student);db_session.commit()
    response=client.post(f'/api/asignaturas/{course.id}/cargas',headers=auth(teacher),data={'estudiante_ids':json.dumps([student.id])},files={'files':('fake.pdf',b'Not PDF','application/pdf')})
    assert response.status_code==422
    assert db_session.query(m.UploadJob).count()==0
    assert not list(tmp_path.rglob('*.pdf'))
