from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import require_teacher, require_staff
from app.models.models import QuestionBank, Question, Evaluation, User, Course, Report
from app.schemas.schemas import QuestionBankResponse, QuestionBankReview
from app.services.audit import log_event

router = APIRouter(prefix="/questions", tags=["questions"])

@router.get("/evaluation/{evaluation_id}/student/{student_id}", response_model=QuestionBankResponse)
def get_student_question_bank(
    evaluation_id: int,
    student_id: int,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """
    Retrieves the question bank generated for a specific student and evaluation.
    Only teachers of the course can access this.
    """
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")
        
    course = evaluation.course
    if course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="No eres el docente de este curso")
        
    bank = db.query(QuestionBank).filter(
        QuestionBank.evaluation_id == evaluation_id,
        QuestionBank.student_id == student_id
    ).first()
    
    if not bank:
        raise HTTPException(
            status_code=404, 
            detail="Banco de preguntas no encontrado. El estudiante aún no ha subido su informe o la IA está procesándolo."
        )
        
    return bank

@router.post("/bank/{bank_id}/review", response_model=QuestionBankResponse)
def review_question_bank(
    bank_id: int,
    review: QuestionBankReview,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """
    Allows the teacher to approve and optionally edit the generated questions.
    """
    bank = db.query(QuestionBank).filter(QuestionBank.id == bank_id).first()
    if not bank:
        raise HTTPException(status_code=404, detail="Banco de preguntas no encontrado")
        
    evaluation = bank.evaluation
    if evaluation.course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="No eres el docente de este curso")
        
    if not bank.is_generated:
        raise HTTPException(status_code=400, detail="El banco de preguntas aún no ha terminado de generarse")
        
    # Update and validate questions
    for eq in review.questions:
        q = db.query(Question).filter(Question.id == eq.id, Question.question_bank_id == bank.id).first()
        if not q:
            raise HTTPException(status_code=404, detail=f"Pregunta con ID {eq.id} no pertenece a este banco")
            
        q.text = eq.text
        q.options = eq.options
        q.correct_answer = str(eq.correct_answer)
        q.limit_seconds = eq.limit_seconds
        
    bank.is_approved = review.is_approved
    bank.approved_by_teacher_id = current_user.id if review.is_approved else None
    
    db.commit()
    db.refresh(bank)
    
    # Audit log
    log_event(
        db,
        user_id=current_user.id,
        action="review_bank",
        entity="question_bank",
        entity_id=str(bank.id),
        details={"approved": bank.is_approved, "questions_count": len(bank.questions)}
    )
    
    return bank

@router.post("/evaluation/{evaluation_id}/regenerate/{student_id}", status_code=status.HTTP_202_ACCEPTED)
def regenerate_question_bank(
    evaluation_id: int,
    student_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """
    Allows the teacher to force regeneration of the question bank for a student.
    """
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")
        
    if evaluation.course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="No eres el docente de este curso")
        
    report = db.query(Report).filter(
        Report.evaluation_id == evaluation_id,
        Report.student_id == student_id
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="El estudiante no ha subido ningún informe para esta evaluación")
        
    # Queue generation
    from app.api.reports import generate_bank_questions_in_background
    background_tasks.add_task(
        generate_bank_questions_in_background,
        report_id=report.id,
        evaluation_id=evaluation_id,
        student_id=student_id
    )
    
    # Audit log
    log_event(
        db,
        user_id=current_user.id,
        action="force_regenerate_bank",
        entity="evaluation",
        entity_id=str(evaluation_id),
        details={"student_id": student_id}
    )
    
    return {"message": "La regeneración del banco de preguntas ha sido solicitada en segundo plano."}
