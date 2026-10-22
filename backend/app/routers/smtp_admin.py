from datetime import datetime, timezone, timedelta
from typing import Literal
from urllib.parse import urlsplit
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, SecretStr, AnyHttpUrl
from sqlalchemy.orm import Session
from backend.app import models
from backend.app.auth import require_admin
from backend.app.database import get_db
from backend.app.audit import log_audit
from backend.app.services import smtp_configuration as config
from backend.app.services.mail_outbox import deliver

router=APIRouter(prefix='/api/admin/correo',tags=['Configuración Gmail'])

class GmailConfig(BaseModel):
    correo: EmailStr
    password: SecretStr | None = None
    port: Literal[587,465] = 587
    public_url: AnyHttpUrl

class TestMail(BaseModel):
    recipient: EmailStr

class EnableMail(BaseModel):
    enabled: bool
    received: bool = False


def public_config(db):
    current=config.snapshot()
    verification=db.get(models.SmtpVerification,1)
    verified=bool(verification and verification.config_hash==config.fingerprint(current))
    return {'host':current['SMTP_HOST'],'port':current['SMTP_PORT'],'security':current['SMTP_SECURITY'],
        'correo':current['SMTP_USER'],'from':current['SMTP_FROM'],'password_configured':bool(current['SMTP_PASSWORD']),
        'enabled':current['SMTP_ENABLED'],'public_url':current['PUBLIC_APP_URL'],'verified':verified,
        'test_recipient':verification.recipient if verified else None,
        'tested_at':verification.verified_at if verified else None}


@router.get('')
def get_config(user=Depends(require_admin),db:Session=Depends(get_db)):
    return public_config(db)


@router.put('')
def save_config(data:GmailConfig,user=Depends(require_admin),db:Session=Depends(get_db)):
    with config.LOCK:
        current=config.snapshot()
        password=data.password.get_secret_value() if data.password is not None else ''
        if '\r' in password or '\n' in password:
            raise HTTPException(422,'La contraseña de aplicación no puede contener saltos de línea')
        if password:
            password=password.replace(' ','')  # Google displays app passwords in groups.
            if len(password)!=16:
                raise HTTPException(422,'Usa la contraseña de aplicación de Google de 16 caracteres')
        elif str(data.correo).lower()!=current['SMTP_USER'].lower():
            raise HTTPException(422,'Indica una contraseña de aplicación al cambiar de cuenta')
        else:
            password=current['SMTP_PASSWORD']
        if not password:
            raise HTTPException(422,'Indica la contraseña de aplicación de Google')
        url=str(data.public_url).rstrip('/')
        parsed=urlsplit(url)
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise HTTPException(422,'La URL de la aplicación no debe incluir credenciales, parámetros ni fragmentos')
        values={'SMTP_HOST':'smtp.gmail.com','SMTP_PORT':data.port,'SMTP_SECURITY':'tls' if data.port==465 else 'starttls',
            'SMTP_USER':str(data.correo).lower(),'SMTP_FROM':str(data.correo).lower(),'SMTP_PASSWORD':password,'PUBLIC_APP_URL':url}
        changed=config.fingerprint(values)!=config.fingerprint(current)
        if changed:values['SMTP_ENABLED']=False
        try:
            config.persist(values)
        except OSError:
            raise HTTPException(503,'No se pudo guardar la configuración en el servidor')
        log_audit(db,'CONFIGURAR_SMTP','configuracion',None,user.id,datos_nuevos={'provider':'gmail','port':data.port,'changed':changed,'enabled':config.snapshot()['SMTP_ENABLED']})
        return public_config(db)


@router.post('/prueba')
async def send_test(data:TestMail,user=Depends(require_admin),db:Session=Depends(get_db)):
    current=config.snapshot()
    if not current['SMTP_USER'] or not current['SMTP_PASSWORD']:
        raise HTTPException(409,'Guarda primero la configuración de Gmail')
    last=db.query(models.MailDelivery).filter(models.MailDelivery.purpose=='smtp_test',models.MailDelivery.reference_id==user.id,
        models.MailDelivery.created_at>datetime.now(timezone.utc)-timedelta(seconds=60)).first()
    if last:raise HTTPException(429,'Espera un minuto antes de enviar otra prueba')
    record=models.MailDelivery(purpose='smtp_test',reference_id=user.id,recipient=str(data.recipient),subject='IntegryEval · Prueba de correo',
        body=f'Esta es una prueba solicitada desde Superadmin. No contiene datos de alumnos.\nAplicación: {current["PUBLIC_APP_URL"]}\nSi recibiste este mensaje, vuelve a IntegryEval y activa los envíos.')
    db.add(record);db.commit()
    await deliver(record,db,force=True,config=current)
    if record.status!='sent':
        log_audit(db,'PROBAR_SMTP','mail_deliveries',record.id,user.id,datos_nuevos={'status':record.status})
        raise HTTPException(502,record.error or 'No se pudo enviar la prueba')
    with config.LOCK:
        # A test on a former configuration cannot validate a newly saved one.
        if config.fingerprint(current)!=config.fingerprint():
            raise HTTPException(409,'La configuración cambió durante la prueba. Repite el envío.')
        verification=db.get(models.SmtpVerification,1)
        if not verification:verification=models.SmtpVerification(id=1);db.add(verification)
        verification.config_hash=config.fingerprint(current);verification.recipient=str(data.recipient);verification.verified_at=datetime.now(timezone.utc)
        db.commit()
    log_audit(db,'PROBAR_SMTP','mail_deliveries',record.id,user.id,datos_nuevos={'status':'sent'})
    return {'message':'Gmail aceptó la prueba. Revisa la bandeja de entrada y spam; después confirma su recepción para activar los envíos.',**public_config(db)}


@router.post('/estado')
def enable_mail(data:EnableMail,user=Depends(require_admin),db:Session=Depends(get_db)):
    with config.LOCK:
        if data.enabled:
            if not data.received:raise HTTPException(422,'Confirma que recibiste el correo de prueba')
            if not public_config(db)['verified']:raise HTTPException(409,'Primero envía una prueba con la configuración actual')
        try:config.persist({'SMTP_ENABLED':data.enabled})
        except OSError:raise HTTPException(503,'No se pudo guardar el estado de los envíos')
        log_audit(db,'ESTADO_SMTP','configuracion',None,user.id,datos_nuevos={'enabled':data.enabled})
        return public_config(db)
