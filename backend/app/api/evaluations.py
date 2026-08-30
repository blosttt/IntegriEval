from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import datetime

from app.core.database import get_db
from app.core.security import get_current_user, require_teacher
from app.models.models import Evaluation, Course, User, Report
from app.schemas.schemas import EvaluationCreate, EvaluationUpdate, EvaluationResponse
from app.services.audit import log_event

router = APIRouter(tags=["evaluations"])


def _assert_teacher_owns_course(course: Course, current_user: User):
    if current_user.role == "teacher" and course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="No eres el docente de este curso")


@router.post("/courses/{course_id}/evaluations", response_model=EvaluationResponse, status_code=status.HTTP_201_CREATED)
def create_evaluation(
    course_id: int,
    eval_in: EvaluationCreate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """Create a new evaluation for a course, with rubric and analysis parameters."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    _assert_teacher_owns_course(course, current_user)

    evaluation = Evaluation(
        course_id=course_id,
        title=eval_in.title,
        prompt_rubric=eval_in.prompt_rubric,
        question_rigor=eval_in.question_rigor,
        pool_size=eval_in.pool_size,
        flash_questions_count=eval_in.flash_questions_count,
        time_per_question=eval_in.time_per_question,
        low_threshold=eval_in.low_threshold,
        high_threshold=eval_in.high_threshold,
        random_review_pct=eval_in.random_review_pct,
        flash_link_ttl_hours=eval_in.flash_link_ttl_hours,
        require_approval=eval_in.require_approval,
    )
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)

    log_event(db, user_id=current_user.id, action="create_evaluation",
              entity="evaluation", entity_id=str(evaluation.id),
              details={"title": evaluation.title, "rigor": evaluation.question_rigor})

    return _enrich(evaluation, db)


@router.get("/courses/{course_id}/evaluations", response_model=List[EvaluationResponse])
def list_course_evaluations(
    course_id: int,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """List all evaluations for a course."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    _assert_teacher_owns_course(course, current_user)

    evals = db.query(Evaluation).filter(Evaluation.course_id == course_id).all()
    return [_enrich(e, db) for e in evals]


@router.get("/evaluations/{evaluation_id}", response_model=EvaluationResponse)
def get_evaluation(
    evaluation_id: int,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")
    _assert_teacher_owns_course(evaluation.course, current_user)
    return _enrich(evaluation, db)


@router.patch("/evaluations/{evaluation_id}", response_model=EvaluationResponse)
def update_evaluation(
    evaluation_id: int,
    eval_in: EvaluationUpdate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """Update evaluation parameters (rubric, thresholds, rigor, etc.)."""
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")
    _assert_teacher_owns_course(evaluation.course, current_user)

    for field, value in eval_in.model_dump(exclude_none=True).items():
        setattr(evaluation, field, value)

    db.commit()
    db.refresh(evaluation)

    log_event(db, user_id=current_user.id, action="update_evaluation",
              entity="evaluation", entity_id=str(evaluation_id),
              details=eval_in.model_dump(exclude_none=True))

    return _enrich(evaluation, db)


@router.delete("/evaluations/{evaluation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_evaluation(
    evaluation_id: int,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")
    _assert_teacher_owns_course(evaluation.course, current_user)

    db.delete(evaluation)
    db.commit()


def _enrich(evaluation: Evaluation, db: Session) -> EvaluationResponse:
    resp = EvaluationResponse.model_validate(evaluation)
    resp.report_count = db.query(Report).filter(Report.evaluation_id == evaluation.id).count()
    return resp
