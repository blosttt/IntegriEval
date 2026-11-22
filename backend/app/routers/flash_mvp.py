from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import AwareDatetime, BaseModel, Field
from sqlalchemy.orm import Session

from backend.app import models as m
from backend.app.activities import assert_activity_open, evaluation_window, lock_question_plan, parameters, test_evaluation
from backend.app.auth import check_course_access, get_current_user
from backend.app.database import get_db
from backend.app.routers.flash_test import get_state

router = APIRouter(tags=["Gestión del Flash Test"])
scope = "/api/asignaturas/{course_id}/flash-test"


class WindowData(BaseModel):
    apertura: AwareDatetime | None = None
    cierre: AwareDatetime | None = None


class FeedbackData(BaseModel):
    texto: str = Field(min_length=1, max_length=5000)


def audit(db, user, action, table, key, data):
    db.add(m.AuditLog(usuario_id=user.id, accion=action, tabla=table, registro_id=key, datos_nuevos=data))


def authorize(course_id, activity_id, user, db, write=False):
    course = check_course_access(course_id, user, db, write=write)
    if write:
        lock_question_plan(course_id, db)
        assert_activity_open(course_id, activity_id, db)
    parameters(course, activity_id, db)


@router.get(scope + "/ventana")
def get_window(course_id: int, actividad_id: int | None = None, user=Depends(get_current_user), db=Depends(get_db)):
    authorize(course_id, actividad_id, user, db)
    window = evaluation_window(db, course_id, actividad_id)
    return WindowData(apertura=window.apertura, cierre=window.cierre) if window else WindowData()


@router.put(scope + "/ventana")
def save_window(course_id: int, data: WindowData, actividad_id: int | None = None,
                user=Depends(get_current_user), db=Depends(get_db)):
    authorize(course_id, actividad_id, user, db, write=True)
    if data.apertura and data.cierre and data.apertura >= data.cierre:
        raise HTTPException(422, "El cierre debe ser posterior a la apertura.")
    window = evaluation_window(db, course_id, actividad_id)
    if not window:
        window = m.EvaluationWindow(asignatura_id=course_id, actividad_key=actividad_id or 0)
        db.add(window)
    window.apertura, window.cierre = data.apertura, data.cierre
    audit(db, user, "CONFIGURAR_VENTANA_FLASH", "asignaturas", course_id,
          {"actividad_id": actividad_id, **data.model_dump(mode="json")})
    db.commit()
    return data


@router.get(scope + "/intentos")
def list_attempts(course_id: int, actividad_id: int | None = None, user=Depends(get_current_user), db=Depends(get_db)):
    authorize(course_id, actividad_id, user, db)
    tests = (db.query(m.FlashTest, m.Estudiante.nombre, m.FlashFeedback.texto)
             .join(m.Estudiante).outerjoin(m.FlashFeedback, m.FlashFeedback.test_id == m.FlashTest.id)
             .filter(m.Estudiante.asignatura_id == course_id, m.FlashTest.actividad_id == actividad_id)
             .order_by(m.Estudiante.nombre, m.FlashTest.id))
    rows = []
    for test, name, feedback in tests:
        if not db.get(m.FlashTestState, test.id):
            continue
        rows.append({"id": test.id, "estudiante_id": test.estudiante_id, "estudiante": name,
                     "estado": test.estado, "puntaje": test.puntaje if test.estado == "completado" else None,
                     "token": test.token, "retroalimentacion": feedback, "nota_cerrada": test.nota_cerrada})
    return rows


def edit_attempt(test_id, user, db):
    test = db.get(m.FlashTest, test_id)
    if not test:
        raise HTTPException(404, "Intento no encontrado.")
    course_id = test.estudiante.asignatura_id
    authorize(course_id, test.actividad_id, user, db, write=True)
    if test.estado != "completado" or not db.get(m.FlashTestState, test_id):
        raise HTTPException(409, "El intento debe estar completado.")
    return test


@router.put("/api/flash-tests/{test_id}/retroalimentacion")
def publish_feedback(test_id: int, data: FeedbackData, user=Depends(get_current_user), db=Depends(get_db)):
    test = edit_attempt(test_id, user, db)
    text = data.texto.strip()
    if not text:
        raise HTTPException(422, "Escribe la retroalimentación antes de publicar.")
    feedback = db.get(m.FlashFeedback, test.id)
    if not feedback:
        feedback = m.FlashFeedback(test_id=test.id)
        db.add(feedback)
    feedback.texto, feedback.usuario_id = text, user.id
    audit(db, user, "PUBLICAR_RETROALIMENTACION_FLASH", "flash_tests", test.id, {})
    db.commit()
    return {"texto": text}


@router.post("/api/flash-tests/{test_id}/repetir")
def repeat_test(test_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    previous = edit_attempt(test_id, user, db)
    attempts = db.query(m.FlashTest).filter_by(estudiante_id=previous.estudiante_id, actividad_id=previous.actividad_id).all()
    if len(attempts) != 1 or previous.nota_cerrada:
        raise HTTPException(409, "Solo se permite un segundo intento y con la nota abierta.")
    student_status = db.get(m.StudentStatus, previous.estudiante_id)
    if student_status and not student_status.active:
        raise HTTPException(409, "El estudiante está retirado del curso.")
    now = datetime.now(timezone.utc)
    window = evaluation_window(db, previous.estudiante.asignatura_id, previous.actividad_id)
    if window and window.cierre and window.cierre <= now:
        raise HTTPException(409, "Amplía la ventana antes de habilitar otro intento.")
    test = m.FlashTest(estudiante_id=previous.estudiante_id, actividad_id=previous.actividad_id,
                       vigencia=now + timedelta(hours=48), tiempo_limite_segundos=previous.tiempo_limite_segundos,
                       estado="pendiente")
    db.add(test)
    db.flush()
    evaluation = test_evaluation(previous, db)
    if evaluation and any(q.seleccionada for q in evaluation.preguntas):
        get_state(test, db)
    else:
        state = db.get(m.FlashTestState, previous.id)
        if db.get(m.AdaptiveSession, previous.id):
            raise HTTPException(409, "Falta el plan de preguntas original para repetir el test.")
        db.add(m.FlashTestState(test_id=test.id, preguntas=state.preguntas, indice=0))
    audit(db, user, "HABILITAR_SEGUNDO_INTENTO", "flash_tests", test.id, {"intento_anterior": previous.id})
    db.commit()
    return {"id": test.id, "token": test.token}
