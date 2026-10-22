from pathlib import Path
import json
import pytest
from dotenv import dotenv_values
from backend.app import models
from backend.app.auth import create_access_token
from backend.app.config import settings
from backend.app.services import smtp_configuration
from backend.app.services import smtp_transport


def auth(user):
    return {'Authorization':'Bearer '+create_access_token({'sub':str(user.id)})}


@pytest.fixture
def isolated_config(tmp_path,monkeypatch):
    path=tmp_path/'.env'
    path.write_text('LLM_PROVIDER=ollama\nPRESERVE_VALUE="keep-me"\n',encoding='utf-8')
    monkeypatch.setattr(smtp_configuration,'ENV_PATH',path)
    for key in smtp_configuration.CONFIG_KEYS:
        monkeypatch.setattr(settings,key,getattr(settings,key))
    monkeypatch.setattr(settings,'SMTP_USER','')
    monkeypatch.setattr(settings,'SMTP_PASSWORD','')
    monkeypatch.setattr(settings,'SMTP_FROM','')
    monkeypatch.setattr(settings,'SMTP_SECURITY','starttls')
    return path


def data(**overrides):
    return {'correo':'sender@example.com','password':'abcd efgh ijkl mnop','port':587,'public_url':'https://integryeval.example.com',**overrides}


def test_only_admin_can_configure_mail(client,seeded_teacher,isolated_config):
    h=auth(seeded_teacher['teacher'])
    assert client.get('/api/admin/correo',headers=h).status_code==403
    assert client.put('/api/admin/correo',headers=h,json=data()).status_code==403
    assert 'SMTP_PASSWORD' not in isolated_config.read_text()


def test_config_preserves_env_and_hides_password(client,db_session,seeded_admin,isolated_config):
    response=client.put('/api/admin/correo',headers=auth(seeded_admin),json=data())
    assert response.status_code==200,response.text
    assert response.json()['password_configured']
    assert response.json()['enabled'] is False
    assert response.json()['verified'] is False
    assert 'abcdefghijklmnop' not in response.text
    assert 'abcdefghijklmnop' not in client.get('/api/admin/correo',headers=auth(seeded_admin)).text
    values=dotenv_values(isolated_config)
    assert values['LLM_PROVIDER']=='ollama' and values['PRESERVE_VALUE']=='keep-me'
    assert values['SMTP_PASSWORD']=='abcdefghijklmnop'
    assert values['SMTP_HOST']=='smtp.gmail.com' and values['SMTP_SECURITY']=='starttls'
    logs=[row.datos_nuevos for row in db_session.query(models.AuditLog).all()]
    assert 'abcdefghijklmnop' not in json.dumps(logs)
    saved=client.put('/api/admin/correo',headers=auth(seeded_admin),json=data(password=None))
    assert saved.status_code==200 and dotenv_values(isolated_config)['SMTP_PASSWORD']=='abcdefghijklmnop'


def test_test_mail_required_before_activation(client,seeded_admin,isolated_config,monkeypatch):
    h=auth(seeded_admin)
    assert client.put('/api/admin/correo',headers=h,json=data()).status_code==200
    assert client.post('/api/admin/correo/estado',headers=h,json={'enabled':True,'received':True}).status_code==409
    captured=[]
    async def fake_send(message,**kwargs):
        captured.append((message,kwargs));return {},'accepted'
    monkeypatch.setattr(smtp_transport.aiosmtplib,'send',fake_send)
    response=client.post('/api/admin/correo/prueba',headers=h,json={'recipient':'recipient@example.com'})
    assert response.status_code==200,response.text
    assert response.json()['verified'] and not response.json()['enabled']
    assert len(captured)==1 and str(captured[0][0]['To'])=='recipient@example.com'
    assert captured[0][1]['start_tls'] and captured[0][1]['validate_certs'] and not captured[0][1]['use_tls']
    assert client.post('/api/admin/correo/estado',headers=h,json={'enabled':True}).status_code==422
    assert client.post('/api/admin/correo/estado',headers=h,json={'enabled':True,'received':True}).json()['enabled']
    assert dotenv_values(isolated_config)['SMTP_ENABLED']=='true'
    assert client.post('/api/admin/correo/prueba',headers=h,json={'recipient':'recipient@example.com'}).status_code==429
    # A new account cannot inherit the preceding account's password or verification.
    assert client.put('/api/admin/correo',headers=h,json=data(correo='other@example.com',password=None)).status_code==422
    changed=client.put('/api/admin/correo',headers=h,json=data(public_url='https://new.example.com',password=None)).json()
    assert not changed['enabled'] and not changed['verified']


def test_tls_465_and_authentication_error_are_safe(client,seeded_admin,isolated_config,monkeypatch):
    h=auth(seeded_admin)
    assert client.put('/api/admin/correo',headers=h,json=data(port=465)).status_code==200
    captured=[]
    async def rejected(message,**kwargs):
        captured.append(kwargs)
        raise smtp_transport.aiosmtplib.errors.SMTPAuthenticationError(535,'secret=abcdefghijklmnop')
    monkeypatch.setattr(smtp_transport.aiosmtplib,'send',rejected)
    response=client.post('/api/admin/correo/prueba',headers=h,json={'recipient':'recipient@example.com'})
    assert response.status_code==502
    assert 'abcdefghijklmnop' not in response.text
    assert captured[0]['use_tls'] and not captured[0]['start_tls']
    assert not client.get('/api/admin/correo',headers=h).json()['verified']


def test_failed_save_does_not_change_runtime_or_env(client,seeded_admin,isolated_config,monkeypatch):
    original=isolated_config.read_text()
    def fail(*args,**kwargs):raise OSError('disk error')
    monkeypatch.setattr(smtp_configuration.os,'replace',fail)
    response=client.put('/api/admin/correo',headers=auth(seeded_admin),json=data())
    assert response.status_code==503
    assert isolated_config.read_text()==original
    assert settings.SMTP_USER=='' and settings.SMTP_PASSWORD==''
    assert not list(isolated_config.parent.glob('.smtp-*.tmp'))


def test_demo_addresses_never_receive_mail(db_session,monkeypatch,isolated_config):
    import asyncio
    from backend.app.services.mail_outbox import deliver
    monkeypatch.setattr(settings,'SMTP_ENABLED',True)
    monkeypatch.setattr(settings,'SMTP_USER','sender@example.com')
    monkeypatch.setattr(settings,'SMTP_PASSWORD','abcdefghijklmnop')
    async def unexpected(*args,**kwargs):raise AssertionError('No debe contactar SMTP')
    monkeypatch.setattr(smtp_transport.aiosmtplib,'send',unexpected)
    record=models.MailDelivery(purpose='test',recipient='demo@example.invalid',subject='Demo',body='Demo')
    db_session.add(record);db_session.commit()
    asyncio.run(deliver(record,db_session))
    assert record.status=='disabled' and 'demostración' in record.error
