from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import update
from sqlalchemy.orm import Session
from backend.app import models
from backend.app.auth import get_current_user, check_course_access
from backend.app.activities import assert_activity_open
from backend.app.database import get_db
from backend.app.audit import log_audit
from backend.app.services.development import score_details, refresh_score

router = APIRouter(tags=['Revisión de desarrollo'])


def public_review(test, db):
    state = db.get(models.FlashTestState, test.id)
    reviews = {item.pregunta_id: item for item in db.query(models.DevelopmentReview).filter_by(test_id=test.id)}
    questions = []
    for question in state.preguntas if state else []:
        if question.get('tipo') != 'desarrollo':
            continue
        review = reviews.get(question['id'])
        answer = (test.respuestas or {}).get(str(question['id']), '') or ''
        questions.append({**question, 'respuesta': answer, 'puntaje': review.puntaje if review else (0 if not answer.strip() else None),
                          'comentario': review.comentario if review else '', 'sin_respuesta': not answer.strip()})
    return {'test_id': test.id, 'estado': test.estado, 'nota_cerrada': test.nota_cerrada,
            'estudiante_nombre': test.estudiante.nombre, 'preguntas': questions,
            'revision_pendiente': bool(state and score_details(test, state, db)['revision_pendiente']), 'puntaje': test.puntaje}


@router.get('/api/evaluaciones/{evaluation_id}/desarrollo')
def get_development(evaluation_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    evaluation = db.get(models.Evaluacion, evaluation_id)
    if not evaluation:
        raise HTTPException(404, 'Evaluación no encontrada')
    work = evaluation.trabajo
    check_course_access(work.estudiante.asignatura_id, user, db)
    test = db.query(models.FlashTest).filter_by(estudiante_id=work.estudiante_id, actividad_id=work.actividad_id).order_by(models.FlashTest.id.desc()).first()
    if not test or test.estado != 'completado':
        return {'test_id': None, 'preguntas': [], 'estado': test.estado if test else 'sin_despacho'}
    return public_review(test, db)


class ReviewItem(BaseModel):
    pregunta_id: int
    puntaje: float = Field(ge=0, le=100, allow_inf_nan=False)
    comentario: str = Field(min_length=1, max_length=2000)


class ReviewData(BaseModel):
    revisiones: list[ReviewItem] = Field(min_length=1, max_length=30)


def _review_development(test_id, data, user, db):
    test = db.get(models.FlashTest, test_id)
    if not test:
        raise HTTPException(404, 'Flash Test no encontrado')
    course_id = test.estudiante.asignatura_id
    check_course_access(course_id, user, db, write=True)
    assert_activity_open(course_id, test.actividad_id, db)
    # Serialize review and grade-closing writes on SQLite before rechecking state.
    db.execute(update(models.FlashTest).where(models.FlashTest.id == test_id).values(estado=models.FlashTest.estado))
    db.refresh(test)
    if test.estado != 'completado' or test.nota_cerrada:
        raise HTTPException(409, 'El test debe estar completado y su nota abierta para revisar desarrollo')
    state = db.get(models.FlashTestState, test_id)
    valid = {question['id'] for question in state.preguntas if question.get('tipo') == 'desarrollo'} if state else set()
    ids = [item.pregunta_id for item in data.revisiones]
    if len(ids) != len(set(ids)) or not set(ids) <= valid or any(not item.comentario.strip() for item in data.revisiones):
        raise HTTPException(422, 'Selecciona preguntas de desarrollo del test y justifica cada puntaje')
    for item in data.revisiones:
        if not ((test.respuestas or {}).get(str(item.pregunta_id)) or '').strip():
            raise HTTPException(422, 'Una pregunta sin respuesta conserva cero puntos')
    before = []
    for item in data.revisiones:
        review = db.get(models.DevelopmentReview, (test_id, item.pregunta_id))
        before.append({'pregunta_id': item.pregunta_id, 'puntaje': review.puntaje if review else None})
        if review is None:
            review = models.DevelopmentReview(test_id=test_id, pregunta_id=item.pregunta_id)
            db.add(review)
        review.puntaje = item.puntaje
        review.comentario = item.comentario.strip()
        review.usuario_id = user.id
        review.reviewed_at = datetime.now(timezone.utc)
    db.flush()
    refresh_score(test, state, db)
    db.commit()
    log_audit(db, 'REVISAR_DESARROLLO', 'flash_tests', test.id, user.id,
              datos_previos={'revisiones': before}, datos_nuevos={'revisiones': [item.model_dump() for item in data.revisiones], 'puntaje_flash': test.puntaje})
    return public_review(test, db)


@router.put('/api/flash-tests/{test_id}/desarrollo')
async def review_development(test_id: int, data: ReviewData, user=Depends(get_current_user), db: Session = Depends(get_db)):
    from starlette.concurrency import run_in_threadpool
    def save():
        try:
            return _review_development(test_id, data, user, db)
        except Exception:
            db.rollback()
            raise
    result = await run_in_threadpool(save)
    from backend.app.routers.flash_test import notify_result
    await notify_result(db.get(models.FlashTest, test_id))
    return result
