import os
import shutil
import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, status
from sqlalchemy.orm import Session

from app.core.database import get_db, SessionLocal
from app.core.security import get_current_user, require_student
from app.models.models import User, Evaluation, Report, QuestionBank, Question
from app.schemas.schemas import ReportResponse
from app.services.extractor import extract_text
from app.services.ai_service import generate_questions_for_report
from app.services.audit import log_event

router = APIRouter(prefix="/reports", tags=["reports"])

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def generate_bank_questions_in_background(report_id: int, evaluation_id: int, student_id: int):
    """
    Background worker that calls the AI service to parse the report,
    creates the QuestionBank, and inserts the generated questions.
    """
    db = SessionLocal()
    try:
        report = db.query(Report).filter(Report.id == report_id).first()
        evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
        if not report or not evaluation:
            return
            
        # 1. Create or reload QuestionBank
        bank = db.query(QuestionBank).filter(
            QuestionBank.evaluation_id == evaluation_id,
            QuestionBank.student_id == student_id
        ).first()
        
        if not bank:
            bank = QuestionBank(
                evaluation_id=evaluation_id,
                student_id=student_id,
                is_generated=False,
                is_approved=False
            )
            db.add(bank)
            db.commit()
            db.refresh(bank)
        else:
            # If bank exists, delete old questions to regenerate
            db.query(Question).filter(Question.question_bank_id == bank.id).delete()
            bank.is_generated = False
            bank.is_approved = False
            db.commit()
            
        # 2. Call AI service to generate questions (Claude or Mock fallback)
        raw_questions = generate_questions_for_report(
            report_text=report.extracted_text,
            teacher_prompt=evaluation.prompt_teacher,
            num_questions=evaluation.num_questions,
            time_per_question=evaluation.time_per_question
        )
        
        # 3. Save questions to DB
        for rq in raw_questions:
            q = Question(
                question_bank_id=bank.id,
                text=rq["text"],
                type=rq["type"],
                options=rq.get("options"),
                correct_answer=str(rq["correct_answer"]),
                limit_seconds=rq.get("limit_seconds", evaluation.time_per_question)
            )
            db.add(q)
            
        bank.is_generated = True
        db.commit()
        
        # Log system audit event
        log_event(
            db,
            user_id=None,
            action="system_generate_bank",
            entity="question_bank",
            entity_id=str(bank.id),
            details={"student_id": student_id, "questions_count": len(raw_questions)}
        )
        
    except Exception as e:
        db.rollback()
        print(f"[BACKGROUND TASK ERROR] Error generating question bank: {e}")
    finally:
        db.close()

@router.post("/upload", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def upload_report(
    background_tasks: BackgroundTasks,
    evaluation_id: int = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """
    Endpoint for students to upload their report (PDF or DOCX).
    Files are limited to 10MB.
    Triggers question generation in a background thread.
    """
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="La evaluación no existe")
        
    # Check enrollment
    if evaluation.course not in current_user.enrolled_courses:
        raise HTTPException(status_code=403, detail="No estás inscrito en este curso")
        
    # Check deadline
    now = datetime.datetime.utcnow()
    if now > evaluation.due_date:
        raise HTTPException(
            status_code=400,
            detail=f"La fecha límite para entregar este informe ya expiró ({evaluation.due_date})"
        )
        
    # Validate file extension
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".pdf", ".docx", ".doc"]:
        raise HTTPException(
            status_code=400,
            detail="Formato de archivo no soportado. Solo se permiten archivos PDF o Word (.docx)"
        )
        
    # Validate file size (10MB limit)
    # Read file content into memory to check size
    contents = file.file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > 10.0:
        raise HTTPException(
            status_code=400,
            detail=f"El archivo excede el límite de tamaño permitido de 10MB (Tamaño: {size_mb:.2f}MB)"
        )
    file.file.seek(0) # Reset pointer
    
    # Check if a report already exists for this student and evaluation
    existing_report = db.query(Report).filter(
        Report.evaluation_id == evaluation_id,
        Report.student_id == current_user.id
    ).first()
    
    # Save file on disk
    student_upload_dir = os.path.join(UPLOAD_DIR, f"student_{current_user.id}")
    os.makedirs(student_upload_dir, exist_ok=True)
    
    # File naming: eval_{id}_{timestamp}{ext}
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    sanitized_filename = f"eval_{evaluation_id}_{timestamp}{ext}"
    dest_path = os.path.join(student_upload_dir, sanitized_filename)
    
    try:
        with open(dest_path, "wb") as buffer:
            buffer.write(contents)
            
        # Parse text from report
        extracted_text = extract_text(dest_path)
        if not extracted_text or len(extracted_text.strip()) < 50:
            raise HTTPException(
                status_code=400,
                detail="El informe está vacío o tiene muy poco contenido extraíble para generar preguntas válidas"
            )
            
    except HTTPException:
        # Pass through our custom exceptions
        if os.path.exists(dest_path):
            os.remove(dest_path)
        raise
    except Exception as e:
        if os.path.exists(dest_path):
            os.remove(dest_path)
        raise HTTPException(
            status_code=500,
            detail=f"Ocurrió un error al guardar o procesar el documento: {str(e)}"
        )
        
    if existing_report:
        # Delete old file
        if os.path.exists(existing_report.file_path):
            try:
                os.remove(existing_report.file_path)
            except Exception:
                pass
        # Update existing record
        existing_report.file_path = dest_path
        existing_report.extracted_text = extracted_text
        existing_report.uploaded_at = datetime.datetime.utcnow()
        report = existing_report
    else:
        # Create new record
        report = Report(
            evaluation_id=evaluation_id,
            student_id=current_user.id,
            file_path=dest_path,
            extracted_text=extracted_text
        )
        db.add(report)
        
    db.commit()
    db.refresh(report)
    
    # Audit log
    log_event(
        db,
        user_id=current_user.id,
        action="upload_report",
        entity="report",
        entity_id=str(report.id),
        details={"filename": filename, "file_size_mb": size_mb}
    )
    
    # Queue the background generation task
    background_tasks.add_task(
        generate_bank_questions_in_background,
        report_id=report.id,
        evaluation_id=evaluation_id,
        student_id=current_user.id
    )
    
    return report
