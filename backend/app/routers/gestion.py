"""Course-scoped administration and oral defense lifecycle."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from backend.app import models, schemas
from backend.app.database import get_db
from backend.app.auth import get_current_user, check_course_access, check_roster_access
from backend.app.audit import log_audit

router = APIRouter(tags=["Gestión de asignaturas"])


class StudentData(BaseModel):
    nombre: str = Field(min_length=1, max_length=150)
    correo: EmailStr
    rut: Optional[str] = Field(default=None, max_length=20)


class AssistantData(BaseModel):
    correo: EmailStr


@router.post("/api/asignaturas/{course_id}/estudiantes", response_model=schemas.EstudianteOut)
def create_student(course_id: int, data: StudentData, user=Depends(get_current_user), db: Session = Depends(get_db)):
    check_roster_access(course_id, user, db)
    if db.query(models.Estudiante).filter_by(asignatura_id=course_id, correo=str(data.correo).lower()).first():
        raise HTTPException(409, "El estudiante ya está inscrito")
    student = models.Estudiante(**data.model_dump(), asignatura_id=course_id)
    student.correo = student.correo.lower()
    db.add(student)
    db.commit()
    log_audit(db, "CREAR_ESTUDIANTE", "estudiantes", student.id, user.id, datos_nuevos=data.model_dump())
    return student


@router.put("/api/asignaturas/{course_id}/estudiantes/{student_id}", response_model=schemas.EstudianteOut)
def update_student(course_id: int, student_id: int, data: StudentData, user=Depends(get_current_user), db: Session = Depends(get_db)):
    check_roster_access(course_id, user, db)
    student = db.query(models.Estudiante).filter_by(id=student_id, asignatura_id=course_id).first()
    if not student:
        raise HTTPException(404, "Estudiante no encontrado")
    duplicate = db.query(models.Estudiante).filter(models.Estudiante.asignatura_id == course_id, models.Estudiante.correo == str(data.correo).lower(), models.Estudiante.id != student_id).first()
    if duplicate:
        raise HTTPException(409, "El correo ya está inscrito")
    before = {"nombre": student.nombre, "correo": student.correo, "rut": student.rut}
    for key, value in data.model_dump().items():
        setattr(student, key, value.lower() if key == "correo" else value)
    db.commit()
    log_audit(db, "EDITAR_ESTUDIANTE", "estudiantes", student.id, user.id, before, data.model_dump())
    return student


@router.get("/api/asignaturas/{course_id}/ayudantes")
def list_assistants(course_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    check_course_access(course_id, user, db)
    return [{"id": u.id, "nombre": u.nombre, "correo": u.correo} for u in db.query(models.Usuario).join(models.CourseAssistant, models.CourseAssistant.usuario_id == models.Usuario.id).filter(models.CourseAssistant.asignatura_id == course_id).all()]


@router.post("/api/asignaturas/{course_id}/ayudantes")
def assign_assistant(course_id: int, data: AssistantData, user=Depends(get_current_user), db: Session = Depends(get_db)):
    check_course_access(course_id, user, db, write=True)
    if user.rol != "admin":
        raise HTTPException(403, "Solo el administrador puede asignar ayudantes")
    assistant = db.query(models.Usuario).filter_by(correo=str(data.correo), rol="ayudante").first()
    if not assistant:
        raise HTTPException(404, "No existe un usuario ayudante con ese correo")
    if not db.get(models.CourseAssistant, (course_id, assistant.id)):
        db.add(models.CourseAssistant(asignatura_id=course_id, usuario_id=assistant.id))
        db.commit()
        log_audit(db, "ASIGNAR_AYUDANTE", "asignaturas", course_id, user.id, datos_nuevos={"usuario_id": assistant.id})
    return {"status": "success"}


@router.delete("/api/asignaturas/{course_id}/ayudantes/{assistant_id}")
def remove_assistant(course_id: int, assistant_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    check_course_access(course_id, user, db, write=True)
    if user.rol != "admin":
        raise HTTPException(403, "Solo el administrador puede retirar ayudantes")
    membership = db.get(models.CourseAssistant, (course_id, assistant_id))
    if not membership:
        raise HTTPException(404, "Ayudante no asignado")
    db.delete(membership)
    db.commit()
    log_audit(db, "RETIRAR_AYUDANTE", "asignaturas", course_id, user.id, datos_previos={"usuario_id": assistant_id})
    return {"status": "success"}


@router.get("/api/asignaturas/{course_id}/citas", response_model=list[schemas.CitaOut])
def list_appointments(course_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    check_course_access(course_id, user, db)
    return [schemas.CitaOut(**{**schemas.CitaOut.model_validate(c).model_dump(), "estudiante_nombre": c.estudiante.nombre}) for c in db.query(models.Cita).join(models.Estudiante).filter(models.Estudiante.asignatura_id == course_id).order_by(models.Cita.fecha).all()]


@router.put("/api/asignaturas/{course_id}/citas/{appointment_id}", response_model=schemas.CitaOut)
def update_appointment(course_id: int, appointment_id: int, data: schemas.CitaUpdate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    check_course_access(course_id, user, db, write=True)
    appointment = db.query(models.Cita).join(models.Estudiante).filter(models.Cita.id == appointment_id, models.Estudiante.asignatura_id == course_id).first()
    if not appointment:
        raise HTTPException(404, "Cita no encontrada")
    before = {"estado": appointment.estado, "fecha": str(appointment.fecha), "bloque": appointment.bloque, "acuerdos": appointment.acuerdos}
    values = data.model_dump(exclude_unset=True)
    if any(value is None for key, value in values.items() if key != "acuerdos"):
        raise HTTPException(422, "Fecha, bloque y estado no pueden ser nulos")
    for key, value in values.items():
        setattr(appointment, key, value)
    db.commit()
    log_audit(db, "ACTUALIZAR_DEFENSA_ORAL", "citas", appointment.id, user.id, before, data.model_dump(mode="json", exclude_unset=True))
    return appointment


@router.delete("/api/asignaturas/{course_id}/materiales/{material_id}")
def delete_material(course_id: int, material_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    check_course_access(course_id, user, db, write=True)
    material = db.query(models.Material).filter_by(id=material_id, asignatura_id=course_id).first()
    if not material:
        raise HTTPException(404, "Material no encontrado")
    before = {"nombre": material.nombre, "tipo": material.tipo}
    db.delete(material)
    db.commit()
    log_audit(db, "ELIMINAR_MATERIAL", "materiales", material_id, user.id, datos_previos=before)
    return {"status": "success"}


@router.get("/api/asignaturas/{course_id}/trabajos", response_model=list[schemas.TrabajoOut])
def list_works(course_id: int, actividad_id: int | None = None, user=Depends(get_current_user), db: Session = Depends(get_db)):
    check_course_access(course_id, user, db)
    from backend.app.activities import parameters
    parameters(db.get(models.Asignatura, course_id), actividad_id, db)
    return db.query(models.Trabajo).join(models.Estudiante).filter(models.Trabajo.actividad_id == actividad_id, models.Estudiante.asignatura_id == course_id, ~models.Estudiante.id.in_(db.query(models.StudentStatus.estudiante_id).filter_by(active=False))).all()


@router.get("/api/trabajos/{work_id}", response_model=schemas.TrabajoOut)
def get_work(work_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    work = db.get(models.Trabajo, work_id)
    if not work:
        raise HTTPException(404, "Informe no encontrado")
    check_course_access(work.estudiante.asignatura_id, user, db)
    return work


@router.post("/api/trabajos/{work_id}/reanalizar")
async def reanalyze_work(work_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    work = db.get(models.Trabajo, work_id)
    if not work:
        raise HTTPException(404, "Informe no encontrado")
    course_id = work.estudiante.asignatura_id
    check_course_access(course_id, user, db, write=True)
    from backend.app.routers.trabajos import assert_work_editable, process_and_evaluate_trabajo
    assert_work_editable(work.estudiante_id, db, work.actividad_id)
    await process_and_evaluate_trabajo(work.id, course_id, db, user.id)
    return {"status": "success"}


@router.delete("/api/asignaturas/{course_id}/estudiantes/{student_id}")
def delete_student(course_id: int, student_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    check_roster_access(course_id, user, db)
    student = db.query(models.Estudiante).filter_by(id=student_id, asignatura_id=course_id).first()
    if not student:
        raise HTTPException(404, "Estudiante no encontrado")
    if student.flash_tests and user.rol != "admin":
        raise HTTPException(409, "Solicite al administrador retirar un estudiante con verificaciones despachadas")
    before = {"nombre": student.nombre, "correo": student.correo}
    status = db.get(models.StudentStatus, student.id)
    if status:
        status.active = False
    else:
        db.add(models.StudentStatus(estudiante_id=student.id, active=False))
    for test in student.flash_tests:
        if test.estado in {"pendiente", "en_progreso"}:
            test.estado = "expirado"
    db.commit()
    log_audit(db, "RETIRAR_ESTUDIANTE", "estudiantes", student_id, user.id, datos_previos=before)
    return {"status": "success"}


@router.post("/api/evaluaciones/{evaluation_id}/preguntas", response_model=schemas.PreguntaOut)
def add_question(evaluation_id: int, data: schemas.PreguntaCreate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    evaluation = db.get(models.Evaluacion, evaluation_id)
    if not evaluation:
        raise HTTPException(404, "Evaluación no encontrada")
    check_course_access(evaluation.trabajo.estudiante.asignatura_id, user, db, write=True)
    from backend.app.routers.preguntas import assert_editable
    assert_editable(evaluation, db)
    if len(evaluation.preguntas) >= 30:
        raise HTTPException(422, "El pool admite hasta 30 preguntas")
    question = models.Pregunta(evaluacion_id=evaluation_id, **data.model_dump())
    db.add(question)
    db.commit()
    log_audit(db, "CREAR_PREGUNTA", "preguntas", question.id, user.id, datos_nuevos=data.model_dump())
    return question


@router.delete("/api/preguntas/{question_id}")
def delete_question(question_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    question = db.get(models.Pregunta, question_id)
    if not question:
        raise HTTPException(404, "Pregunta no encontrada")
    evaluation = question.evaluacion
    check_course_access(evaluation.trabajo.estudiante.asignatura_id, user, db, write=True)
    from backend.app.routers.preguntas import assert_editable
    assert_editable(evaluation, db)
    if len(evaluation.preguntas) <= 1:
        raise HTTPException(409, "Debe conservar al menos una pregunta")
    before = {"texto": question.texto}
    db.delete(question)
    db.commit()
    log_audit(db, "ELIMINAR_PREGUNTA", "preguntas", question_id, user.id, datos_previos=before)
    return {"status": "success"}


class AvailabilityData(BaseModel):
    day_of_week: int = Field(ge=0, le=6)
    start_time: str = Field(pattern=r"^(?:[01][0-9]|2[0-3]):[0-5][0-9]$")
    end_time: str = Field(pattern=r"^(?:[01][0-9]|2[0-3]):[0-5][0-9]$")


@router.get("/api/disponibilidad")
def list_availability(user=Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(models.TeacherAvailability).filter_by(usuario_id=user.id).all()


@router.post("/api/disponibilidad")
def add_availability(data: AvailabilityData, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.rol not in {"docente", "ayudante", "admin"}:
        raise HTTPException(403, "Solo docentes, ayudantes y administradores pueden editar horarios")
    if data.start_time >= data.end_time:
        raise HTTPException(422, "La hora de término debe ser posterior al inicio")
    overlap = db.query(models.TeacherAvailability).filter(models.TeacherAvailability.usuario_id == user.id, models.TeacherAvailability.day_of_week == data.day_of_week, models.TeacherAvailability.start_time < data.end_time, models.TeacherAvailability.end_time > data.start_time).first()
    if overlap:
        raise HTTPException(409, "El horario se superpone con otro bloque")
    item = models.TeacherAvailability(usuario_id=user.id, **data.model_dump())
    db.add(item)
    db.commit()
    log_audit(db, "CREAR_DISPONIBILIDAD", "teacher_availability", item.id, user.id, datos_nuevos=data.model_dump())
    db.refresh(item)
    return item


@router.delete("/api/disponibilidad/{availability_id}")
def remove_availability(availability_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(models.TeacherAvailability).filter_by(id=availability_id, usuario_id=user.id).first()
    if not item:
        raise HTTPException(404, "Horario no encontrado")
    db.delete(item)
    db.commit()
    log_audit(db, "ELIMINAR_DISPONIBILIDAD", "teacher_availability", availability_id, user.id)
    return {"status": "success"}


@router.get("/api/system/metrics")
def system_metrics(user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.rol != "admin":
        raise HTTPException(403, "Se requiere rol administrador")
    return {"total_users": db.query(models.Usuario).count(), "teachers": db.query(models.Usuario).filter_by(rol="docente").count(),
            "students": db.query(models.Estudiante).count(), "llm_invocations": db.query(models.AuditLog).filter_by(accion="EVALUACION_GENERADA").count(),
            "system_errors": db.query(models.Trabajo).filter_by(estado="error").count()}
