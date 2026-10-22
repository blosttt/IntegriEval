import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, EmailStr, Field, field_validator
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import update
from sqlalchemy.orm import Session
from backend.app import models
from backend.app.database import get_db
from backend.app.auth import hash_password
from backend.app.config import settings
from backend.app.services.mail_outbox import enqueue
from backend.app.services.scheduling import utc
from backend.app.audit import log_audit

router = APIRouter(prefix='/api/auth', tags=['Recuperación de acceso'])

class Forgot(BaseModel):
    correo: EmailStr

class Reset(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    contrasena: str = Field(min_length=10)

    @field_validator('contrasena')
    @classmethod
    def password_length(cls, value):
        if len(value.encode()) > 72:
            raise ValueError('La contraseña admite hasta 72 bytes UTF-8')
        return value

@router.post('/forgot-password')
async def forgot_password(data: Forgot, db: Session=Depends(get_db)):
    response={'message':'Si la cuenta está activa, recibirás un enlace de recuperación. Si no llega, contacta al administrador.'}
    user=db.query(models.Usuario).filter_by(correo=str(data.correo).lower()).first()
    if not user:
        return response
    status=db.get(models.AccountStatus,user.id)
    if status and not status.active:
        return response
    now=datetime.now(timezone.utc)
    if db.query(models.PasswordReset).filter(models.PasswordReset.usuario_id==user.id, models.PasswordReset.created_at>now-timedelta(minutes=2)).first():
        return response
    token=secrets.token_urlsafe(32)
    db.query(models.PasswordReset).filter_by(usuario_id=user.id,used=False).update({'used':True})
    db.add(models.PasswordReset(usuario_id=user.id,token_hash=hashlib.sha256(token.encode()).hexdigest(),expires_at=now+timedelta(minutes=30)))
    db.commit()
    await enqueue(db,purpose='password_reset',reference_id=user.id,recipient=user.correo,subject='IntegryEval · Recuperar acceso',body=f'Abre este enlace para establecer una nueva contraseña. Caduca en 30 minutos y solo se puede usar una vez:\n{settings.PUBLIC_APP_URL.rstrip("/")}/recuperar?token={token}\nSi no solicitaste este cambio, ignora este correo.')
    return response

@router.post('/reset-password')
def reset_password(data: Reset, db: Session=Depends(get_db)):
    digest=hashlib.sha256(data.token.encode()).hexdigest()
    reset=db.get(models.PasswordReset,digest)
    if not reset or reset.used or utc(reset.expires_at)<=datetime.now(timezone.utc):
        raise HTTPException(400,'El enlace es inválido, ya fue utilizado o ha caducado')
    user=db.get(models.Usuario,reset.usuario_id)
    status=db.get(models.AccountStatus,user.id)
    if status and not status.active:
        raise HTTPException(400,'El enlace no está disponible')
    claimed=db.execute(update(models.PasswordReset).where(models.PasswordReset.token_hash==digest,models.PasswordReset.used==False).values(used=True))
    if claimed.rowcount!=1:
        db.rollback();raise HTTPException(400,'El enlace ya fue utilizado')
    user.contrasena=hash_password(data.contrasena)
    version=db.get(models.CredentialVersion,user.id)
    if version: version.version+=1
    else: db.add(models.CredentialVersion(usuario_id=user.id,version=1))
    db.query(models.PasswordReset).filter_by(usuario_id=user.id,used=False).update({'used':True})
    db.commit()
    log_audit(db,'RECUPERAR_CONTRASENA','usuarios',user.id,user.id)
    return {'message':'Contraseña actualizada. Inicia sesión con tu nueva contraseña.'}
