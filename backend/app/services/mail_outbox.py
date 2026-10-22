"""Persistent delivery records; no credentials or links are exposed in list responses."""
from email.message import EmailMessage
from datetime import datetime, timezone
import aiosmtplib
from backend.app import models
from backend.app.config import settings


async def deliver(record, db, force=False, config=None):
    from backend.app.services.smtp_configuration import snapshot
    from backend.app.services.smtp_transport import send_message, is_demo_recipient
    if record.status == 'sent':
        return record
    current=config or snapshot()
    record.attempts += 1
    if is_demo_recipient(record.recipient):
        record.status, record.error = 'disabled', 'Dirección de demostración: no se envían correos'
    elif (not force and not current['SMTP_ENABLED']) or not current['SMTP_USER'] or not current['SMTP_PASSWORD']:
        record.status, record.error = 'disabled', 'SMTP no configurado o desactivado'
    else:
        message = EmailMessage()
        message['From'] = current['SMTP_FROM'] or current['SMTP_USER']
        message['To'], message['Subject'] = record.recipient, record.subject.replace('\r',' ').replace('\n',' ')
        message.set_content(record.body)
        try:
            rejected,_ = await send_message(message,current)
            if rejected:raise ValueError('El destinatario fue rechazado')
            record.status, record.error = 'sent', None
            record.sent_at = datetime.now(timezone.utc)
        except aiosmtplib.errors.SMTPAuthenticationError:
            record.status, record.error = 'failed', 'Gmail rechazó la autenticación. Revisa la cuenta, la contraseña de aplicación y las políticas de Google Workspace.'
        except Exception:
            record.status, record.error = 'failed', 'El servidor SMTP rechazó el envío o no respondió. Revisa la conexión y la configuración.'
    db.commit()
    return record


async def enqueue(db, **values):
    record = models.MailDelivery(**values)
    db.add(record)
    db.commit()
    return await deliver(record, db)


async def appointment_notice(appointment, db):
    db.query(models.MailDelivery).filter(models.MailDelivery.reference_id==appointment.id, models.MailDelivery.purpose.in_(['appointment','reminder']), models.MailDelivery.status.in_(['pending','disabled','failed'])).update({'status':'cancelled','error':'Aviso reemplazado por una actualización de la cita'})
    student = appointment.estudiante
    from zoneinfo import ZoneInfo
    date = appointment.fecha.replace(tzinfo=timezone.utc) if appointment.fecha.tzinfo is None else appointment.fecha
    local = date.astimezone(ZoneInfo(settings.APP_TIMEZONE))
    return await enqueue(db, asignatura_id=student.asignatura_id, estudiante_id=student.id,
        purpose='appointment', reference_id=appointment.id, recipient=student.correo,
        subject='IntegryEval · Actualización de cita de revisión',
        body=f'Hola {student.nombre},\nTu cita está {appointment.estado}.\nFecha: {local:%d/%m/%Y %H:%M} ({settings.APP_TIMEZONE}).\nBloque: {appointment.bloque}.\nContacta al docente si necesitas un cambio.')


async def send_due_reminders(db, now=None):
    if not settings.SMTP_ENABLED:
        return 0
    from datetime import timedelta
    from zoneinfo import ZoneInfo
    from sqlalchemy.exc import IntegrityError
    from backend.app.services.scheduling import utc
    now = now or datetime.now(timezone.utc)
    appointments=db.query(models.Cita).filter(models.Cita.estado=='programada',models.Cita.fecha>now,models.Cita.fecha<=now+timedelta(hours=24)).all()
    sent=0
    for appointment in appointments:
        key=(appointment.id,appointment.fecha)
        if db.get(models.ReminderClaim,key):
            continue
        try:
            db.add(models.ReminderClaim(cita_id=appointment.id,fecha_cita=appointment.fecha));db.commit()
        except IntegrityError:
            db.rollback();continue
        student=appointment.estudiante
        local=utc(appointment.fecha).astimezone(ZoneInfo(settings.APP_TIMEZONE))
        await enqueue(db,asignatura_id=student.asignatura_id,estudiante_id=student.id,purpose='reminder',reference_id=appointment.id,recipient=student.correo,subject='IntegryEval · Recordatorio de revisión',body=f'Hola {student.nombre}, recuerda tu revisión el {local:%d/%m/%Y %H:%M} ({settings.APP_TIMEZONE}), bloque {appointment.bloque}.')
        sent+=1
    return sent


async def reminder_loop(session_factory):
    import asyncio
    import logging
    while True:
        try:
            with session_factory() as db:
                await send_due_reminders(db)
        except Exception:
            logging.getLogger(__name__).exception('No se pudieron preparar los recordatorios')
        await asyncio.sleep(60)
