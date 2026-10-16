from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app import models, schemas
from backend.app.auth import get_current_user, check_course_access
from backend.app.audit import log_audit

router = APIRouter(tags=["Pool de Preguntas"])

@router.get("/api/evaluaciones/{evaluacion_id}/preguntas", response_model=List[schemas.PreguntaOut])
def get_pool_preguntas(
    evaluacion_id: int,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve full question pool generated for an evaluation (RF-008)"""
    evaluacion = db.query(models.Evaluacion).filter(models.Evaluacion.id == evaluacion_id).first()
    if not evaluacion:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")
    check_course_access(evaluacion.trabajo.estudiante.asignatura_id, current_user, db)
    return evaluacion.preguntas

@router.put("/api/preguntas/{pregunta_id}", response_model=schemas.PreguntaOut)
def update_pregunta(
    pregunta_id: int,
    data: schemas.PreguntaUpdate,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Teacher edits question text, options or toggles selection (RF-009)"""
    pregunta = db.query(models.Pregunta).filter(models.Pregunta.id == pregunta_id).first()
    if not pregunta:
        raise HTTPException(status_code=404, detail="Pregunta no encontrada")

    check_course_access(pregunta.evaluacion.trabajo.estudiante.asignatura_id, current_user, db, write=True)
    assert_editable(pregunta.evaluacion, db)
    datos_previos = {"texto": pregunta.texto, "seleccionada": pregunta.seleccionada}

    if data.texto is not None:
        pregunta.texto = data.texto
    if data.alternativas is not None:
        pregunta.alternativas = [a.model_dump() for a in data.alternativas]
    if data.seleccionada is not None:
        pregunta.seleccionada = data.seleccionada
    if data.justificacion_respuesta is not None:
        pregunta.justificacion_respuesta = data.justificacion_respuesta

    db.commit()
    db.refresh(pregunta)

    log_audit(
        db=db,
        accion="EDITAR_PREGUNTA",
        tabla="preguntas",
        registro_id=pregunta.id,
        usuario_id=current_user.id,
        datos_previos=datos_previos,
        datos_nuevos={"texto": pregunta.texto, "seleccionada": pregunta.seleccionada}
    )

    return pregunta

@router.post("/api/evaluaciones/{evaluacion_id}/seleccionar")
def select_questions_for_test(
    evaluacion_id: int,
    req: schemas.SeleccionarPreguntasRequest,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Docente selecciona N preguntas (N <= Pool) para el Flash Test (RF-009)"""
    evaluacion = db.query(models.Evaluacion).filter(models.Evaluacion.id == evaluacion_id).first()
    if not evaluacion:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")

    check_course_access(evaluacion.trabajo.estudiante.asignatura_id, current_user, db, write=True)
    assert_editable(evaluacion, db)
    valid_ids = {q.id for q in evaluacion.preguntas}
    if not req.pregunta_ids or len(set(req.pregunta_ids)) != len(req.pregunta_ids) or not set(req.pregunta_ids) <= valid_ids:
        raise HTTPException(422, "Seleccione preguntas únicas pertenecientes a esta evaluación")
    # Mark all questions for this eval as unselected first
    for q in evaluacion.preguntas:
        q.seleccionada = (q.id in req.pregunta_ids)

    db.commit()

    log_audit(
        db=db,
        accion="SELECCIONAR_PREGUNTAS_TEST",
        tabla="evaluaciones",
        registro_id=evaluacion.id,
        usuario_id=current_user.id,
        datos_nuevos={"seleccionadas_ids": req.pregunta_ids}
    )

    return {
        "status": "success",
        "mensaje": f"Se han seleccionado {len(req.pregunta_ids)} preguntas para el Flash Test"
    }


def assert_editable(evaluacion, db):
    if db.query(models.FlashTest).filter_by(estudiante_id=evaluacion.trabajo.estudiante_id, actividad_id=evaluacion.trabajo.actividad_id).first():
        raise HTTPException(409, "El test ya fue despachado; sus preguntas no pueden modificarse")
