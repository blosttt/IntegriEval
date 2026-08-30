"""
Reports API — bulk upload by teacher/assistant, AI analysis background tasks,
question pool management, and flash test email dispatch.
"""
import os
import uuid
import datetime
from typing import List, Optional

from fastapi import (
    APIRouter, Depends, HTTPException, UploadFile, File, Form,
    BackgroundTasks, status
)
from sqlalchemy.orm import Session

from app.core.database import get_db, SessionLocal
from app.core.security import require_teacher, get_current_user
from app.models.models import (
    Report, Evaluation, Student, CourseMaterial, QuestionBank, Question, User
)
from app.schemas.schemas import (
    ReportResponse, ReportScoreUpdate,
    QuestionBankResponse, QuestionResponse, QuestionCreate, QuestionUpdate,
    QuestionSelectPayload,
)
from app.services.extractor import extract_to_markdown
from app.services.ai_service import analyze_report, generate_questions_for_report
from app.services.email_service import send_flash_test_email_sync
from app.services.audit import log_event

router = APIRouter(prefix="/reports", tags=["reports"])

UPLOAD_DIR = "./uploads/reports"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# BACKGROUND TASKS
# ─────────────────────────────────────────────────────────────────────────────

def _run_analysis_and_generate_questions(report_id: int):
    """
    Background task:
    1. Convert document to Markdown.
    2. Analyze against rubric using AI.
    3. Generate question pool.
    4. Save everything to DB.
    """
    db = SessionLocal()
    try:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            return

        evaluation = db.query(Evaluation).filter(Evaluation.id == report.evaluation_id).first()
        if not evaluation:
            return

        # Mark as processing
        report.analysis_status = "processing"
        db.commit()

        # 1. Convert to Markdown
        try:
            md = extract_to_markdown(report.file_path)
            report.markdown_content = md
        except Exception as e:
            print(f"[reports] Markdown extraction error for report {report_id}: {e}")
            md = ""

        # 2. Build material context from CourseMaterial records
        materials = db.query(CourseMaterial).filter(
            CourseMaterial.evaluation_id == evaluation.id
        ).all()
        material_context = "\n\n---\n\n".join(
            m.markdown_content for m in materials if m.markdown_content
        ) or None

        # 3. Run AI analysis
        analysis = analyze_report(
            markdown_text=md or report.markdown_content or "",
            rubric_prompt=evaluation.prompt_rubric,
            material_context=material_context,
        )

        report.ai_score_percentage = analysis.get("score_percentage")
        report.ai_detected_percentage = analysis.get("ai_detected_percentage")
        report.analysis_feedback = analysis.get("feedback")
        report.analysis_breakdown = analysis.get("breakdown")
        report.analysis_status = "done"

        # Set final_score_percentage to AI score initially (teacher can override)
        report.final_score_percentage = report.ai_score_percentage

        db.commit()

        # 4. Generate question pool
        questions_raw = generate_questions_for_report(
            report_text=md or "",
            teacher_prompt=evaluation.prompt_rubric,
            num_questions=evaluation.pool_size,
            time_per_question=evaluation.time_per_question,
            rigor=evaluation.question_rigor,
            material_context=material_context,
        )

        # Create QuestionBank for this report
        bank = db.query(QuestionBank).filter(QuestionBank.report_id == report_id).first()
        if bank:
            db.query(Question).filter(Question.question_bank_id == bank.id).delete()
            bank.is_generated = False
            bank.is_approved = False
            db.commit()
        else:
            bank = QuestionBank(
                report_id=report_id,
                evaluation_id=evaluation.id,
                student_id=report.student_id,
                is_generated=False,
                is_approved=False,
            )
            db.add(bank)
            db.commit()
            db.refresh(bank)

        for rq in questions_raw:
            q = Question(
                question_bank_id=bank.id,
                text=rq["text"],
                type=rq["type"],
                options=rq.get("options"),
                correct_answer=str(rq["correct_answer"]),
                limit_seconds=rq.get("limit_seconds", evaluation.time_per_question),
                is_custom=False,
            )
            db.add(q)

        bank.is_generated = True
        db.commit()

        log_event(db, user_id=None, action="analysis_complete",
                  entity="report", entity_id=str(report_id),
                  details={"score": report.ai_score_percentage, "ai_pct": report.ai_detected_percentage})

    except Exception as e:
        db.rollback()
        report = db.query(Report).filter(Report.id == report_id).first()
        if report:
            report.analysis_status = "error"
            db.commit()
        print(f"[reports] Background analysis error for report {report_id}: {e}")
    finally:
        db.close()


def _send_flash_email_task(report_id: int):
    """Background task: generate flash token, send email, create FlashTestSession."""
    from app.models.models import FlashTestSession
    db = SessionLocal()
    try:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            return
        evaluation = db.query(Evaluation).filter(Evaluation.id == report.evaluation_id).first()
        student = db.query(Student).filter(Student.id == report.student_id).first()

        if not student or not evaluation:
            return

        # Generate unique token
        token = str(uuid.uuid4())
        expires_at = datetime.datetime.utcnow() + datetime.timedelta(hours=evaluation.flash_link_ttl_hours)

        report.flash_token = token
        report.flash_token_expires_at = expires_at
        db.commit()

        # Create FlashTestSession
        existing_session = db.query(FlashTestSession).filter(
            FlashTestSession.report_id == report_id
        ).first()
        if not existing_session:
            flash_session = FlashTestSession(
                report_id=report_id,
                evaluation_id=evaluation.id,
                student_id=student.id,
                status="pending",
            )
            db.add(flash_session)
            db.commit()

        # Send email
        sent = send_flash_test_email_sync(
            student_email=student.email,
            student_name=student.name,
            eval_title=evaluation.title,
            flash_token=token,
            ttl_hours=evaluation.flash_link_ttl_hours,
        )

        report.flash_email_sent = sent
        db.commit()

        log_event(db, user_id=None, action="send_flash_email",
                  entity="report", entity_id=str(report_id),
                  details={"student_email": student.email, "sent": sent})

    except Exception as e:
        print(f"[reports] Email send error for report {report_id}: {e}")
        db.rollback()
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────────────────────
# UPLOAD ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/bulk-upload", status_code=status.HTTP_201_CREATED)
async def bulk_upload_reports(
    background_tasks: BackgroundTasks,
    evaluation_id: int = Form(...),
    # Metadata: JSON array string of {"student_id": int} per file, ordered same as files
    student_ids: str = Form(...),  # JSON: "[1,2,3]"
    files: List[UploadFile] = File(...),
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """
    Upload multiple student reports at once.
    `student_ids` is a JSON array of Student IDs corresponding to each file (same order).
    The teacher should first create/import students, then map them here.
    """
    import json as _json

    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")
    if current_user.role == "teacher" and evaluation.course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="No eres el docente de esta evaluación")

    try:
        sid_list: List[int] = _json.loads(student_ids)
    except Exception:
        raise HTTPException(status_code=400, detail="student_ids debe ser un array JSON válido")

    if len(sid_list) != len(files):
        raise HTTPException(
            status_code=400,
            detail=f"Se recibieron {len(files)} archivos pero {len(sid_list)} IDs de estudiantes"
        )

    created_reports = []

    for idx, (file, student_id) in enumerate(zip(files, sid_list)):
        student = db.query(Student).filter(
            Student.id == student_id,
            Student.course_id == evaluation.course_id
        ).first()
        if not student:
            created_reports.append({
                "index": idx,
                "filename": file.filename,
                "error": f"Estudiante ID {student_id} no encontrado en el curso"
            })
            continue

        filename = file.filename or f"report_{idx}"
        ext = os.path.splitext(filename)[1].lower()
        if ext not in [".pdf", ".docx", ".doc"]:
            created_reports.append({
                "index": idx,
                "filename": filename,
                "error": "Formato no soportado. Solo PDF o DOCX."
            })
            continue

        contents = await file.read()
        size_mb = len(contents) / (1024 * 1024)
        if size_mb > 30.0:
            created_reports.append({
                "index": idx,
                "filename": filename,
                "error": f"Archivo muy grande ({size_mb:.1f}MB). Límite: 30MB."
            })
            continue

        # Save file
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_name = f"eval_{evaluation_id}_student_{student_id}_{timestamp}{ext}"
        dest_path = os.path.join(UPLOAD_DIR, safe_name)
        with open(dest_path, "wb") as f:
            f.write(contents)

        # Upsert report
        existing = db.query(Report).filter(
            Report.evaluation_id == evaluation_id,
            Report.student_id == student_id,
        ).first()

        if existing:
            if os.path.exists(existing.file_path):
                try:
                    os.remove(existing.file_path)
                except Exception:
                    pass
            existing.file_path = dest_path
            existing.analysis_status = "pending"
            existing.flash_email_sent = False
            existing.flash_completed = False
            existing.flash_token = None
            existing.flash_token_expires_at = None
            existing.uploaded_at = datetime.datetime.utcnow()
            report = existing
        else:
            report = Report(
                evaluation_id=evaluation_id,
                student_id=student_id,
                file_path=dest_path,
                analysis_status="pending",
            )
            db.add(report)

        db.commit()
        db.refresh(report)

        # Queue analysis background task
        background_tasks.add_task(_run_analysis_and_generate_questions, report.id)

        log_event(db, user_id=current_user.id, action="upload_report",
                  entity="report", entity_id=str(report.id),
                  details={"student_id": student_id, "filename": filename})

        created_reports.append({
            "index": idx,
            "filename": filename,
            "report_id": report.id,
            "student_id": student_id,
            "student_name": student.name,
            "status": "queued_for_analysis",
        })

    return {"results": created_reports}


@router.post("/upload-single", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def upload_single_report(
    background_tasks: BackgroundTasks,
    evaluation_id: int = Form(...),
    student_id: int = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """Upload a single report for a specific student."""
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")
    if current_user.role == "teacher" and evaluation.course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="No eres el docente de esta evaluación")

    student = db.query(Student).filter(
        Student.id == student_id,
        Student.course_id == evaluation.course_id
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado en este curso")

    filename = file.filename or "report"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".pdf", ".docx", ".doc"]:
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF o Word (.docx)")

    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > 30.0:
        raise HTTPException(
            status_code=400,
            detail=f"El archivo excede el límite de 30MB ({size_mb:.1f}MB)"
        )

    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_name = f"eval_{evaluation_id}_student_{student_id}_{timestamp}{ext}"
    dest_path = os.path.join(UPLOAD_DIR, safe_name)
    with open(dest_path, "wb") as f:
        f.write(contents)

    existing = db.query(Report).filter(
        Report.evaluation_id == evaluation_id,
        Report.student_id == student_id,
    ).first()

    if existing:
        if os.path.exists(existing.file_path):
            try:
                os.remove(existing.file_path)
            except Exception:
                pass
        existing.file_path = dest_path
        existing.analysis_status = "pending"
        existing.flash_email_sent = False
        existing.flash_completed = False
        existing.flash_token = None
        existing.flash_token_expires_at = None
        existing.uploaded_at = datetime.datetime.utcnow()
        report = existing
    else:
        report = Report(
            evaluation_id=evaluation_id,
            student_id=student_id,
            file_path=dest_path,
            analysis_status="pending",
        )
        db.add(report)

    db.commit()
    db.refresh(report)

    background_tasks.add_task(_run_analysis_and_generate_questions, report.id)

    log_event(db, user_id=current_user.id, action="upload_report",
              entity="report", entity_id=str(report.id),
              details={"student_id": student_id, "filename": filename})

    return _enrich_report(report, db)


# ─────────────────────────────────────────────────────────────────────────────
# READ ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/evaluation/{evaluation_id}", response_model=List[ReportResponse])
def list_reports(
    evaluation_id: int,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """List all reports for an evaluation with their analysis status."""
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")
    if current_user.role == "teacher" and evaluation.course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="No eres el docente de esta evaluación")

    reports = db.query(Report).filter(Report.evaluation_id == evaluation_id).all()
    return [_enrich_report(r, db) for r in reports]


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(
    report_id: int,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """Get detailed analysis for a single report."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")

    evaluation = report.evaluation
    if current_user.role == "teacher" and evaluation.course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sin acceso a este reporte")

    return _enrich_report(report, db)


@router.get("/{report_id}/markdown")
def get_report_markdown(
    report_id: int,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """Return the Markdown content of the converted report for preview."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    if current_user.role == "teacher" and report.evaluation.course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sin acceso")
    return {"report_id": report_id, "markdown": report.markdown_content or ""}


# ─────────────────────────────────────────────────────────────────────────────
# TEACHER ACTIONS
# ─────────────────────────────────────────────────────────────────────────────

@router.patch("/{report_id}/score", response_model=ReportResponse)
def update_report_score(
    report_id: int,
    payload: ReportScoreUpdate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """Teacher manually overrides the AI-assigned score."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    if current_user.role == "teacher" and report.evaluation.course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sin acceso")

    report.teacher_score_override = payload.teacher_score_override
    report.final_score_percentage = payload.teacher_score_override
    db.commit()
    db.refresh(report)

    log_event(db, user_id=current_user.id, action="override_score",
              entity="report", entity_id=str(report_id),
              details={"new_score": payload.teacher_score_override})

    return _enrich_report(report, db)


@router.post("/{report_id}/reanalyze", status_code=status.HTTP_202_ACCEPTED)
def reanalyze_report(
    report_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """Re-run the AI analysis for a report (resets analysis_status to pending)."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    if current_user.role == "teacher" and report.evaluation.course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sin acceso")

    report.analysis_status = "pending"
    db.commit()
    background_tasks.add_task(_run_analysis_and_generate_questions, report_id)

    return {"message": "Análisis reiniciado en background", "report_id": report_id}


# ─────────────────────────────────────────────────────────────────────────────
# QUESTION POOL MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{report_id}/questions", response_model=QuestionBankResponse)
def get_question_bank(
    report_id: int,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """Get the question pool for a report."""
    report = _get_report_for_teacher(report_id, current_user, db)
    bank = db.query(QuestionBank).filter(QuestionBank.report_id == report_id).first()
    if not bank:
        raise HTTPException(status_code=404, detail="El banco de preguntas aún no ha sido generado")
    return bank


@router.patch("/{report_id}/questions/{question_id}", response_model=QuestionResponse)
def update_question(
    report_id: int,
    question_id: int,
    payload: QuestionUpdate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """Edit a question in the pool."""
    _get_report_for_teacher(report_id, current_user, db)
    bank = _get_bank(report_id, db)

    q = db.query(Question).filter(
        Question.id == question_id,
        Question.question_bank_id == bank.id,
    ).first()
    if not q:
        raise HTTPException(status_code=404, detail="Pregunta no encontrada")

    if payload.text is not None:
        q.text = payload.text
    if payload.options is not None:
        q.options = payload.options
    if payload.correct_answer is not None:
        q.correct_answer = payload.correct_answer
    if payload.limit_seconds is not None:
        q.limit_seconds = payload.limit_seconds

    db.commit()
    db.refresh(q)
    return q


@router.post("/{report_id}/questions", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
def create_custom_question(
    report_id: int,
    payload: QuestionCreate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """Add a custom (teacher-created) question to the pool."""
    _get_report_for_teacher(report_id, current_user, db)
    bank = _get_bank(report_id, db)

    q = Question(
        question_bank_id=bank.id,
        text=payload.text,
        type=payload.type,
        options=payload.options,
        correct_answer=payload.correct_answer,
        limit_seconds=payload.limit_seconds,
        is_custom=True,
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    return q


@router.delete("/{report_id}/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(
    report_id: int,
    question_id: int,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """Remove a question from the pool."""
    _get_report_for_teacher(report_id, current_user, db)
    bank = _get_bank(report_id, db)

    q = db.query(Question).filter(
        Question.id == question_id,
        Question.question_bank_id == bank.id,
    ).first()
    if not q:
        raise HTTPException(status_code=404, detail="Pregunta no encontrada")

    db.delete(q)
    db.commit()


@router.post("/{report_id}/questions/select-random", response_model=QuestionBankResponse)
def select_random_questions(
    report_id: int,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """
    Randomly selects N questions (flash_questions_count from evaluation)
    from the pool as the set to send to the student.
    """
    import random as _random
    report = _get_report_for_teacher(report_id, current_user, db)
    bank = _get_bank(report_id, db)

    n = report.evaluation.flash_questions_count
    all_ids = [q.id for q in bank.questions]

    if len(all_ids) < n:
        selected = all_ids
    else:
        selected = _random.sample(all_ids, n)

    bank.selected_question_ids = selected
    db.commit()
    db.refresh(bank)
    return bank


@router.post("/{report_id}/questions/select", response_model=QuestionBankResponse)
def select_questions_manual(
    report_id: int,
    payload: QuestionSelectPayload,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """Manually select which question IDs to include in the flash test."""
    _get_report_for_teacher(report_id, current_user, db)
    bank = _get_bank(report_id, db)

    valid_ids = {q.id for q in bank.questions}
    invalid = [qid for qid in payload.question_ids if qid not in valid_ids]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"IDs de preguntas inválidos: {invalid}"
        )

    bank.selected_question_ids = payload.question_ids
    db.commit()
    db.refresh(bank)
    return bank


@router.post("/{report_id}/send-flash", status_code=status.HTTP_202_ACCEPTED)
def send_flash_test(
    report_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """
    Approve the question set and send the flash test invitation email to the student.
    Requires: bank must be generated, and questions must be selected.
    """
    _get_report_for_teacher(report_id, current_user, db)
    bank = _get_bank(report_id, db)

    if not bank.is_generated:
        raise HTTPException(status_code=400, detail="El banco de preguntas aún no está listo")

    if not bank.selected_question_ids:
        raise HTTPException(
            status_code=400,
            detail="Debes seleccionar las preguntas antes de enviar el flash test"
        )

    # Mark bank as approved
    bank.is_approved = True
    bank.approved_by_teacher_id = current_user.id
    bank.approved_at = datetime.datetime.utcnow()
    db.commit()

    # Queue email task
    background_tasks.add_task(_send_flash_email_task, report_id)

    log_event(db, user_id=current_user.id, action="send_flash_test",
              entity="report", entity_id=str(report_id),
              details={"questions_selected": len(bank.selected_question_ids)})

    return {"message": "Flash test enviado en background", "report_id": report_id}


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _get_report_for_teacher(report_id: int, current_user: User, db: Session) -> Report:
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    if current_user.role == "teacher" and report.evaluation.course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sin acceso a este reporte")
    return report


def _get_bank(report_id: int, db: Session) -> QuestionBank:
    bank = db.query(QuestionBank).filter(QuestionBank.report_id == report_id).first()
    if not bank:
        raise HTTPException(status_code=404, detail="Banco de preguntas no generado aún")
    return bank


def _enrich_report(report: Report, db: Session) -> ReportResponse:
    """Builds a ReportResponse with student info and bank status."""
    student = db.query(Student).filter(Student.id == report.student_id).first()
    bank = db.query(QuestionBank).filter(QuestionBank.report_id == report.id).first()

    return ReportResponse(
        id=report.id,
        evaluation_id=report.evaluation_id,
        student_id=report.student_id,
        student_name=student.name if student else None,
        student_email=student.email if student else None,
        file_path=report.file_path,
        uploaded_at=report.uploaded_at,
        analysis_status=report.analysis_status,
        ai_score_percentage=report.ai_score_percentage,
        ai_detected_percentage=report.ai_detected_percentage,
        analysis_feedback=report.analysis_feedback,
        analysis_breakdown=report.analysis_breakdown,
        teacher_score_override=report.teacher_score_override,
        final_score_percentage=report.final_score_percentage,
        flash_email_sent=report.flash_email_sent or False,
        flash_completed=report.flash_completed or False,
        flash_token_expires_at=report.flash_token_expires_at,
        review_required=report.review_required or False,
        review_reason=report.review_reason,
        bank_generated=bank.is_generated if bank else False,
        bank_approved=bank.is_approved if bank else False,
    )
