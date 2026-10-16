from typing import Optional, Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy.orm import Session
from backend.app import models, schemas
from backend.app.auth import require_admin, hash_password
from backend.app.database import get_db
from backend.app.audit import log_audit

router = APIRouter(prefix="/api/admin", tags=["Administración académica"])


class TeacherData(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    correo: EmailStr
    contrasena: Optional[str] = Field(default=None, min_length=6)
    active: bool = True
    rol: Optional[Literal["docente", "ayudante"]] = None

    @field_validator("contrasena")
    @classmethod
    def password_length(cls, value):
        if value is not None and len(value.encode('utf-8')) > 72:
            raise ValueError('La contraseña admite hasta 72 bytes UTF-8')
        return value


def teacher_info(user, db):
    status = db.get(models.AccountStatus, user.id)
    ids = {row.asignatura_id for row in db.query(models.CourseTeacher).filter_by(usuario_id=user.id)}
    ids.update(row.asignatura_id for row in db.query(models.CourseAssistant).filter_by(usuario_id=user.id))
    ids.update(row.id for row in db.query(models.Asignatura).filter_by(docente_id=user.id))
    return {"id": user.id, "nombre": user.nombre, "correo": user.correo, "rol": user.rol,
            "active": status.active if status else True, "asignaturas": sorted(ids)}


@router.get('/profesores')
def list_teachers(admin=Depends(require_admin), db: Session = Depends(get_db)):
    return [teacher_info(u, db) for u in db.query(models.Usuario).filter(models.Usuario.rol.in_(['docente','ayudante'])).order_by(models.Usuario.nombre).all()]


@router.post('/profesores')
def create_teacher(data: TeacherData, admin=Depends(require_admin), db: Session = Depends(get_db)):
    if not data.contrasena:
        raise HTTPException(422, 'Indique una contraseña inicial')
    if db.query(models.Usuario).filter_by(correo=str(data.correo).lower()).first():
        raise HTTPException(409, 'El correo ya está registrado')
    user = models.Usuario(nombre=data.nombre, correo=str(data.correo).lower(), contrasena=hash_password(data.contrasena), rol=data.rol or 'docente')
    db.add(user)
    db.flush()
    db.add(models.AccountStatus(usuario_id=user.id, active=data.active))
    db.commit()
    log_audit(db, 'CREAR_PROFESOR', 'usuarios', user.id, admin.id, datos_nuevos={'nombre': user.nombre, 'correo': user.correo})
    return teacher_info(user, db)


@router.put('/profesores/{teacher_id}')
def edit_teacher(teacher_id: int, data: TeacherData, admin=Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(models.Usuario).filter(models.Usuario.id == teacher_id, models.Usuario.rol.in_(['docente','ayudante'])).first()
    if not user:
        raise HTTPException(404, 'Profesor no encontrado')
    if db.query(models.Usuario).filter(models.Usuario.correo == str(data.correo).lower(), models.Usuario.id != teacher_id).first():
        raise HTTPException(409, 'El correo ya está registrado')
    before = teacher_info(user, db)
    user.nombre, user.correo = data.nombre, str(data.correo).lower()
    if data.rol and data.rol != user.rol:
        raise HTTPException(422, "Para conservar los permisos de las asignaciones no se puede cambiar el rol de una cuenta existente")
    if data.contrasena:
        user.contrasena = hash_password(data.contrasena)
    status = db.get(models.AccountStatus, user.id)
    if status:
        status.active = data.active
    else:
        db.add(models.AccountStatus(usuario_id=user.id, active=data.active))
    db.commit()
    after = teacher_info(user, db)
    log_audit(db, 'EDITAR_PROFESOR', 'usuarios', user.id, admin.id, before, {**after, 'contrasena_modificada': bool(data.contrasena)})
    return after


@router.delete('/profesores/{teacher_id}')
def deactivate_teacher(teacher_id: int, admin=Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(models.Usuario).filter(models.Usuario.id == teacher_id, models.Usuario.rol.in_(['docente','ayudante'])).first()
    if not user:
        raise HTTPException(404, 'Profesor no encontrado')
    data = TeacherData(nombre=user.nombre, correo=user.correo, active=False)
    return edit_teacher(teacher_id, data, admin, db)


class TeacherAssignment(BaseModel):
    usuario_id: int


@router.get('/asignaturas/{course_id}/profesores')
def course_teachers(course_id: int, admin=Depends(require_admin), db: Session = Depends(get_db)):
    course = db.get(models.Asignatura, course_id)
    if not course:
        raise HTTPException(404, 'Asignatura no encontrada')
    ids = {m.usuario_id for m in db.query(models.CourseTeacher).filter_by(asignatura_id=course_id)}
    ids.update(m.usuario_id for m in db.query(models.CourseAssistant).filter_by(asignatura_id=course_id))
    ids.add(course.docente_id)
    return [teacher_info(u, db) for u in db.query(models.Usuario).filter(models.Usuario.id.in_(ids), models.Usuario.rol.in_(['docente','ayudante'])).all()]


@router.post('/asignaturas/{course_id}/profesores')
def assign_teacher(course_id: int, data: TeacherAssignment, admin=Depends(require_admin), db: Session = Depends(get_db)):
    course = db.get(models.Asignatura, course_id)
    user = db.query(models.Usuario).filter(models.Usuario.id == data.usuario_id, models.Usuario.rol.in_(['docente','ayudante'])).first()
    if not course or (course.parametros or {}).get('_archived'):
        raise HTTPException(404, 'Asignatura no encontrada')
    if not user:
        raise HTTPException(404, 'Profesor no encontrado')
    if not teacher_info(user, db)['active']:
        raise HTTPException(409, 'El profesor está desactivado')
    membership_model = models.CourseAssistant if user.rol == "ayudante" else models.CourseTeacher
    if not db.get(membership_model, (course_id, user.id)):
        db.add(membership_model(asignatura_id=course_id, usuario_id=user.id))
        db.commit()
        log_audit(db, 'ASIGNAR_PROFESOR', 'asignaturas', course_id, admin.id, datos_nuevos={'usuario_id': user.id})
    return {'status': 'success'}


@router.delete('/asignaturas/{course_id}/profesores/{teacher_id}')
def unassign_teacher(course_id: int, teacher_id: int, admin=Depends(require_admin), db: Session = Depends(get_db)):
    course = db.get(models.Asignatura, course_id)
    if not course:
        raise HTTPException(404, 'Asignatura no encontrada')
    membership = db.get(models.CourseTeacher, (course_id, teacher_id))
    if membership:
        db.delete(membership)
    assistant = db.get(models.CourseAssistant, (course_id, teacher_id))
    if assistant:
        db.delete(assistant)
    if course.docente_id == teacher_id:
        course.docente_id = admin.id
    db.commit()
    log_audit(db, 'RETIRAR_PROFESOR', 'asignaturas', course_id, admin.id, datos_previos={'usuario_id': teacher_id})
    return {'status': 'success'}


@router.delete('/asignaturas/{course_id}')
def archive_course(course_id: int, admin=Depends(require_admin), db: Session = Depends(get_db)):
    course = db.get(models.Asignatura, course_id)
    if not course:
        raise HTTPException(404, 'Asignatura no encontrada')
    course.parametros = {**(course.parametros or {}), '_archived': True}
    db.commit()
    log_audit(db, 'ARCHIVAR_ASIGNATURA', 'asignaturas', course_id, admin.id)
    return {'status': 'success'}


@router.get('/profesores/{teacher_id}')
def teacher_profile(teacher_id: int, admin=Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(models.Usuario).filter(models.Usuario.id == teacher_id, models.Usuario.rol.in_(['docente', 'ayudante'])).first()
    if not user:
        raise HTTPException(404, 'Docente o ayudante no encontrado')
    return teacher_info(user, db)


@router.get('/profesores/{teacher_id}/asignaturas')
def teacher_courses(teacher_id: int, admin=Depends(require_admin), db: Session = Depends(get_db)):
    from backend.app.routers.asignaturas import get_user_asignaturas
    user = db.query(models.Usuario).filter(models.Usuario.id == teacher_id, models.Usuario.rol.in_(['docente', 'ayudante'])).first()
    if not user:
        raise HTTPException(404, 'Docente o ayudante no encontrado')
    return get_user_asignaturas(user, db)


@router.get('/profesores/{teacher_id}/disponibilidad')
def teacher_availability(teacher_id: int, admin=Depends(require_admin), db: Session = Depends(get_db)):
    teacher_profile(teacher_id, admin, db)
    return db.query(models.TeacherAvailability).filter_by(usuario_id=teacher_id).all()


@router.post('/profesores/{teacher_id}/asignaturas', response_model=schemas.AsignaturaOut)
def create_assigned_course(teacher_id: int, data: schemas.AsignaturaCreate, admin=Depends(require_admin), db: Session = Depends(get_db)):
    profile = teacher_profile(teacher_id, admin, db)
    if not profile['active']:
        raise HTTPException(409, 'Active la cuenta antes de asignarle una nueva asignatura')
    course = models.Asignatura(nombre=data.nombre, periodo=data.periodo, ano=data.ano, docente_id=admin.id,
                               parametros=(data.parametros or schemas.ParametrosConfig()).model_dump())
    db.add(course)
    db.flush()
    membership = models.CourseAssistant if profile['rol'] == 'ayudante' else models.CourseTeacher
    db.add(membership(asignatura_id=course.id, usuario_id=teacher_id))
    db.commit()
    log_audit(db, 'CREAR_ASIGNATURA_ASIGNADA', 'asignaturas', course.id, admin.id,
              datos_nuevos={'profesor_id': teacher_id, 'nombre': course.nombre})
    return schemas.AsignaturaOut.model_validate(course)


@router.post('/profesores/{teacher_id}/disponibilidad')
def create_teacher_availability(teacher_id: int, data: dict, admin=Depends(require_admin), db: Session = Depends(get_db)):
    from backend.app.routers.gestion import AvailabilityData
    from pydantic import ValidationError
    teacher_profile(teacher_id, admin, db)
    try:
        value = AvailabilityData.model_validate(data)
    except ValidationError as exc:
        raise HTTPException(422, 'Día u horario inválido') from exc
    if value.start_time >= value.end_time:
        raise HTTPException(422, 'El término debe ser posterior al inicio')
    if db.query(models.TeacherAvailability).filter(models.TeacherAvailability.usuario_id == teacher_id, models.TeacherAvailability.day_of_week == value.day_of_week, models.TeacherAvailability.start_time < value.end_time, models.TeacherAvailability.end_time > value.start_time).first():
        raise HTTPException(409, 'El horario se superpone con otro bloque')
    item = models.TeacherAvailability(usuario_id=teacher_id, **value.model_dump())
    db.add(item)
    db.commit()
    log_audit(db, 'ADMIN_CREAR_DISPONIBILIDAD', 'teacher_availability', item.id, admin.id, datos_nuevos={'profesor_id': teacher_id, **value.model_dump()})
    db.refresh(item)
    return item


@router.delete('/profesores/{teacher_id}/disponibilidad/{availability_id}')
def delete_teacher_availability(teacher_id: int, availability_id: int, admin=Depends(require_admin), db: Session = Depends(get_db)):
    item = db.query(models.TeacherAvailability).filter_by(usuario_id=teacher_id, id=availability_id).first()
    if not item:
        raise HTTPException(404, 'Horario no encontrado para este docente')
    db.delete(item)
    db.commit()
    log_audit(db, 'ADMIN_RETIRAR_DISPONIBILIDAD', 'teacher_availability', availability_id, admin.id, datos_previos={'profesor_id': teacher_id})
    return {'status': 'success'}
