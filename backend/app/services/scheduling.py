from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import re
from fastapi import HTTPException
from backend.app import models
from backend.app.config import settings


def utc(date):
    return date.replace(tzinfo=timezone.utc) if date.tzinfo is None else date.astimezone(timezone.utc)


def validate_slot(db, teacher_id, student_id, date, block, exclude_id=None):
    if not re.fullmatch(r'\d{2}:\d{2} - \d{2}:\d{2}', block):
        raise HTTPException(422, 'Usa un bloque HH:MM - HH:MM')
    try:
        start, end = [datetime.strptime(t, '%H:%M').time() for t in block.split(' - ')]
    except ValueError:
        raise HTTPException(422, 'Horario inválido')
    local = utc(date).astimezone(ZoneInfo(settings.APP_TIMEZONE))
    if end <= start or local.time().replace(second=0, microsecond=0, tzinfo=None) != start:
        raise HTTPException(422, 'El bloque debe coincidir con el inicio y terminar después')
    if utc(date) <= datetime.now(timezone.utc):
        raise HTTPException(422, 'La cita debe tener una fecha futura')
    slots = db.query(models.TeacherAvailability).filter_by(usuario_id=teacher_id).all()
    if slots and not any(s.day_of_week == local.weekday() and s.start_time <= start.strftime('%H:%M') and s.end_time >= end.strftime('%H:%M') for s in slots):
        raise HTTPException(409, 'La cita está fuera de la disponibilidad del docente')
    finish = utc(date) + timedelta(minutes=(end.hour * 60 + end.minute) - (start.hour * 60 + start.minute))
    # Serialize SQLite writers before checking overlapping intervals.
    from sqlalchemy import update
    db.execute(update(models.Usuario).where(models.Usuario.id==teacher_id).values(nombre=models.Usuario.nombre))
    candidates = db.query(models.Cita).filter(models.Cita.estado == 'programada', (models.Cita.docente_id == teacher_id) | (models.Cita.estudiante_id == student_id)).all()
    for appointment in candidates:
        if appointment.id == exclude_id:
            continue
        try:
            a, b = [datetime.strptime(t, '%H:%M') for t in appointment.bloque.split(' - ')]
            duration = max(1, int((b-a).total_seconds()/60))
        except ValueError:
            duration = 15
        other = utc(appointment.fecha)
        if utc(date) < other + timedelta(minutes=duration) and finish > other:
            raise HTTPException(409, 'El docente o el alumno ya tiene una cita en ese horario')
