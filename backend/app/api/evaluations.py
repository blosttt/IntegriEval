from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import datetime

from app.core.database import get_db
from app.core.security import get_current_user, require_teacher, require_staff
from app.models.models import Evaluation, Course, User, Report, QuestionBank, EvaluationSession
from app.schemas.schemas import EvaluationCreate, EvaluationResponse
from app.services.audit import log_event

router = APIRouter(tags=["evaluations"])

@router.post("/courses/{course_id}/evaluations", response_model=EvaluationResponse)
def create_evaluation(
    course_id: int,
    eval_in: EvaluationCreate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
        
    if course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="No eres el docente de este curso")
        
    evaluation = Evaluation(
        course_id=course_id,
        title=eval_in.title,
        prompt_teacher=eval_in.prompt_teacher,
        due_date=eval_in.due_date,
        start_window=eval_in.start_window,
        end_window=eval_in.end_window,
        time_per_question=eval_in.time_per_question,
        num_questions=eval_in.num_questions,
        pass_threshold=eval_in.pass_threshold,
        excellence_threshold=eval_in.excellence_threshold,
        require_approval=eval_in.require_approval
    )
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)
    
    # Audit log
    log_event(
        db,
        user_id=current_user.id,
        action="create_evaluation",
        entity="evaluation",
        entity_id=str(evaluation.id),
        details={"title": evaluation.title}
    )
    
    return evaluation

@router.get("/courses/{course_id}/evaluations", response_model=List[EvaluationResponse])
def get_course_evaluations(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
        
    # Student must be enrolled in course
    if current_user.role == "student" and course not in current_user.enrolled_courses:
        raise HTTPException(status_code=403, detail="No estás inscrito en este curso")
    elif current_user.role == "teacher" and course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="No eres el docente de este curso")
        
    return db.query(Evaluation).filter(Evaluation.course_id == course_id).all()

@router.get("/evaluations/{evaluation_id}", response_model=EvaluationResponse)
def get_evaluation(
    evaluation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")
        
    course = evaluation.course
    if current_user.role == "student" and course not in current_user.enrolled_courses:
        raise HTTPException(status_code=403, detail="No tienes acceso a esta evaluación")
    elif current_user.role == "teacher" and course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes acceso a esta evaluación")
        
    return evaluation

@router.get("/evaluations/{evaluation_id}/status")
def get_evaluation_student_status(
    evaluation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the progress details for the current student for a specific evaluation.
    Only students can query this endpoint.
    """
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Solo los estudiantes pueden consultar su estado")
        
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")
        
    # Check enrollment
    if evaluation.course not in current_user.enrolled_courses:
        raise HTTPException(status_code=403, detail="No estás inscrito en el curso asociado")
        
    now = datetime.datetime.utcnow()
    
    # 1. Report Upload Status
    report = db.query(Report).filter(
        Report.evaluation_id == evaluation_id,
        Report.student_id == current_user.id
    ).first()
    
    # 2. Question Bank Status
    bank = db.query(QuestionBank).filter(
        QuestionBank.evaluation_id == evaluation_id,
        QuestionBank.student_id == current_user.id
    ).first()
    
    bank_ready = False
    if bank:
        # If approval is required, must be approved. Else, just generated is enough.
        if evaluation.require_approval:
            bank_ready = bank.is_generated and bank.is_approved
        else:
            bank_ready = bank.is_generated
            
    # 3. Evaluation Session Status
    session = db.query(EvaluationSession).filter(
        EvaluationSession.evaluation_id == evaluation_id,
        EvaluationSession.student_id == current_user.id
    ).order_by(EvaluationSession.created_at.desc()).first()
    
    session_status = "not_started"
    session_id = None
    result = None
    
    if session:
        session_status = session.status
        session_id = session.id
        if session.status == "completed":
            result = {
                "score": session.score,
                "percentage_score": session.percentage_score,
                "classification": session.classification
            }

    # Time states
    due_date_passed = now > evaluation.due_date
    window_open = evaluation.start_window <= now <= evaluation.end_window
    window_close_passed = now > evaluation.end_window
    
    return {
        "evaluation_id": evaluation_id,
        "title": evaluation.title,
        "due_date": evaluation.due_date,
        "start_window": evaluation.start_window,
        "end_window": evaluation.end_window,
        "report_uploaded": report is not None,
        "report_id": report.id if report else None,
        "bank_ready": bank_ready,
        "session_status": session_status,
        "session_id": session_id,
        "result": result,
        "due_date_passed": due_date_passed,
        "window_open": window_open,
        "window_close_passed": window_close_passed
    }
