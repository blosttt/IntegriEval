import asyncio
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import pytest
from backend.app import models as m
from backend.app.auth import create_access_token, verify_password
from backend.app.config import settings

def auth(user):
    return {'Authorization':'Bearer '+create_access_token({'sub':str(user.id)})}

def setup_student(db, course):
    student=m.Estudiante(nombre='=Demo',correo='ops@example.invalid',asignatura_id=course.id)
    db.add(student);db.commit();return student

def future_slot(day=5):
    return (datetime.now(ZoneInfo('America/Santiago'))+timedelta(days=day)).replace(hour=10,minute=0,second=0,microsecond=0)

def test_recovery_single_use_revokes_sessions(client,db_session,seeded_teacher,monkeypatch):
    monkeypatch.setattr(settings,'SMTP_ENABLED',False)
    teacher=seeded_teacher['teacher'];headers=auth(teacher)
    response=client.post('/api/auth/forgot-password',json={'correo':teacher.correo})
    unknown=client.post('/api/auth/forgot-password',json={'correo':'missing@example.cl'})
    assert response.json()==unknown.json()
    assert 'token' not in response.text
    delivery=db_session.query(m.MailDelivery).filter_by(purpose='password_reset').one()
    assert delivery.status=='disabled'
    token=re.search(r'token=([\w-]+)',delivery.body).group(1)
    assert db_session.query(m.PasswordReset).one().token_hash!=token
    assert client.post('/api/auth/forgot-password',json={'correo':teacher.correo}).status_code==200
    assert db_session.query(m.PasswordReset).count()==1
    reset=client.post('/api/auth/reset-password',json={'token':token,'contrasena':'NewPassword123!'})
    assert reset.status_code==200,reset.text
    assert client.get('/api/auth/me',headers=headers).status_code==401
    assert client.post('/api/auth/reset-password',json={'token':token,'contrasena':'AnotherPassword123!'}).status_code==400
    login=client.post('/api/auth/login',json={'correo':teacher.correo,'contrasena':'NewPassword123!'})
    assert login.status_code==200
    assert client.get('/api/auth/me',headers={'Authorization':'Bearer '+login.json()['access_token']}).status_code==200

def test_agenda_overlap_availability_and_notice_replacement(client,db_session,seeded_teacher,monkeypatch):
    monkeypatch.setattr(settings,'SMTP_ENABLED',False)
    teacher,course=seeded_teacher['teacher'],seeded_teacher['course'];student=setup_student(db_session,course)
    day=future_slot();h=auth(teacher);root=f'/api/asignaturas/{course.id}/citas'
    db_session.add(m.TeacherAvailability(usuario_id=teacher.id,day_of_week=day.weekday(),start_time='10:00',end_time='12:00'));db_session.commit()
    data={'estudiante_id':student.id,'fecha':day.isoformat(),'bloque':'10:00 - 10:30'}
    first=client.post(root,headers=h,json=data);assert first.status_code==200,first.text
    assert client.post(root,headers=h,json=data).status_code==409
    assert client.post(root,headers=h,json={**data,'fecha':day.replace(hour=9).isoformat(),'bloque':'09:00 - 09:30'}).status_code==409
    changed=client.put(root+f"/{first.json()['id']}",headers=h,json={'fecha':day.replace(hour=11).isoformat(),'bloque':'11:00 - 11:30'})
    assert changed.status_code==200,changed.text
    records=db_session.query(m.MailDelivery).order_by(m.MailDelivery.id).all()
    assert [r.status for r in records]==['cancelled','disabled']

def test_close_archive_reopen_and_export(client,db_session,seeded_teacher):
    teacher,course=seeded_teacher['teacher'],seeded_teacher['course'];student=setup_student(db_session,course)
    h=auth(teacher);root=f'/api/asignaturas/{course.id}'
    assert client.put(root+'/actividades/0/estado',headers=h,json={'estado':'archivada'}).status_code==200
    assert client.get(root+'/actividades',headers=h).json()[0]['estado']=='archivada'
    assert client.put(root+'/actividades/0',headers=h,json={'titulo':'Cambio','parametros':{}}).status_code==409
    assert client.post(root+'/flash-test/despacho',headers=h,json=[student.id]).status_code==409
    csv=client.get(root+'/exportar',headers=h)
    assert csv.status_code==200 and "'=Demo" in csv.text
    pdf=client.get(root+'/exportar?formato=pdf',headers=h)
    assert pdf.status_code==200 and pdf.content.startswith(b'%PDF')
    assert client.put(root+'/actividades/0/estado',headers=h,json={'estado':'abierta'}).status_code==200
    assert client.put(root+'/actividades/0',headers=h,json={'titulo':'Cambio','parametros':{}}).status_code==200

def test_outbox_permissions_and_no_body_leak(client,db_session,seeded_teacher):
    teacher,course=seeded_teacher['teacher'],seeded_teacher['course'];h=auth(teacher)
    db_session.add(m.MailDelivery(asignatura_id=course.id,purpose='appointment',recipient='x@example.invalid',subject='Aviso',body='PRIVATE TOKEN'))
    db_session.commit()
    response=client.get(f'/api/asignaturas/{course.id}/correos',headers=h)
    assert response.status_code==200 and 'PRIVATE TOKEN' not in response.text
    other=m.Usuario(nombre='Otro',correo='other.ops@example.cl',contrasena='unused',rol='docente');db_session.add(other);db_session.commit()
    assert client.get(f'/api/asignaturas/{course.id}/correos',headers=auth(other)).status_code==403

def test_reminder_is_only_prepared_once(db_session,seeded_teacher,monkeypatch):
    from backend.app.services import mail_outbox
    monkeypatch.setattr(settings,'SMTP_ENABLED',True)
    teacher,course=seeded_teacher['teacher'],seeded_teacher['course'];student=setup_student(db_session,course)
    date=datetime.now(ZoneInfo('America/Santiago'))+timedelta(hours=3)
    db_session.add(m.Cita(estudiante_id=student.id,docente_id=teacher.id,fecha=date,bloque='10:00 - 10:15'));db_session.commit()
    async def no_network(record,db):
        record.status='sent';record.attempts=1;db.commit();return record
    monkeypatch.setattr(mail_outbox,'deliver',no_network)
    assert asyncio.run(mail_outbox.send_due_reminders(db_session))==1
    assert asyncio.run(mail_outbox.send_due_reminders(db_session))==0
    assert db_session.query(m.MailDelivery).filter_by(purpose='reminder').count()==1

def test_scanned_pdf_requires_ocr(tmp_path,monkeypatch):
    import pymupdf
    from backend.app.services.pdf_service import extract_pdf_to_markdown
    monkeypatch.setattr(settings,'OCR_ENABLED',False)
    document=pymupdf.open();document.new_page();path=tmp_path/'scan.pdf';document.save(path);document.close()
    with pytest.raises(ValueError,match='OCR'):
        extract_pdf_to_markdown(str(path))


def test_real_ocr_when_language_data_installed(tmp_path,monkeypatch):
    from pathlib import Path
    import pymupdf
    from backend.app.services.pdf_service import extract_pdf_to_markdown
    if not settings.TESSDATA_PREFIX or not (Path(settings.TESSDATA_PREFIX)/'spa.traineddata').is_file():
        pytest.skip('Los datos de idioma de OCR son una dependencia opcional del entorno')
    monkeypatch.setattr(settings,'OCR_ENABLED',True)
    source=pymupdf.open();page=source.new_page();page.insert_text((72,100),'Arquitectura y metodologia del proyecto.',fontsize=18)
    image=page.get_pixmap(matrix=pymupdf.Matrix(2,2)).tobytes('png')
    scan=pymupdf.open();page=scan.new_page();page.insert_image(page.rect,stream=image)
    path=tmp_path/'image-only.pdf';scan.save(path);scan.close();source.close()
    assert 'Arquitectura' in extract_pdf_to_markdown(str(path))


def test_llm_fallback_is_explicit(monkeypatch):
    from backend.app.services import llm_service
    monkeypatch.setattr(settings,'LLM_PROVIDER','ollama')
    async def offline(*args,**kwargs):
        raise TimeoutError('Unavailable')
    monkeypatch.setattr(llm_service,'request_json',offline)
    result=asyncio.run(llm_service.evaluate_submission_llm('Informe de ejemplo sobre arquitectura y pruebas.'))
    assert result[0]['motor_analisis']=='mock' and result[0]['fallback_ia'] is True
    questions=asyncio.run(llm_service.generate_question_pool_llm('Informe de ejemplo',pool_size=10))
    assert all(q['_motor']=='mock' for q in questions)
