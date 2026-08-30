import datetime
import random
from sqlalchemy.orm import Session
from app.models.models import (
    FlashTestSession, Evaluation, Appointment, TeacherAvailability, Report, Student, User
)
from app.services.audit import log_event
from app.services.email_service import send_appointment_email_sync


def process_flash_test_result(db: Session, flash_session_id: int) -> FlashTestSession:
    """
    Calculates the final score of a completed flash test session,
    classifies the result, and triggers appointment scheduling when needed.
    """
    session = db.query(FlashTestSession).filter(FlashTestSession.id == flash_session_id).first()
    if not session:
        raise ValueError(f"FlashTestSession {flash_session_id} not found")

    evaluation = db.query(Evaluation).filter(Evaluation.id == session.evaluation_id).first()
    report = db.query(Report).filter(Report.id == session.report_id).first()
    student = db.query(Student).filter(Student.id == session.student_id).first()
    course = evaluation.course

    # Count correct answers
    total_answered = len(session.answers)
    correct = sum(1 for a in session.answers if a.is_correct)

    # Total is based on questions actually sent (selected pool)
    bank = report.question_bank if report else None
    total_questions = len(bank.selected_question_ids) if (bank and bank.selected_question_ids) else total_answered
    if total_questions == 0:
        total_questions = evaluation.flash_questions_count

    percentage = correct / total_questions if total_questions > 0 else 0.0

    session.score = float(correct)
    session.percentage_score = round(percentage, 4)
    session.completed_at = datetime.datetime.utcnow()

    # Classify
    if percentage < evaluation.low_threshold:
        classification = "low"
    elif percentage >= evaluation.high_threshold:
        classification = "high"
    else:
        classification = "medium"

    session.classification = classification
    session.status = "completed"

    # Mark report as flash completed
    if report:
        report.flash_completed = True
        report.review_required = False
        report.review_reason = None

    db.commit()
    db.refresh(session)

    # Log
    log_event(
        db,
        user_id=None,
        action="complete_flash_test",
        entity="flash_test_session",
        entity_id=str(session.id),
        details={
            "score": session.score,
            "percentage": percentage,
            "classification": classification,
            "student_id": session.student_id,
        },
    )

    # ── Routing to office ─────────────────────────────────────────────────
    reason = None
    if classification == "low":
        reason = "low_flash"
    elif classification == "high":
        reason = "high_flash"
    else:
        # Random selection
        if random.random() < evaluation.random_review_pct:
            reason = "random"

    if reason and report:
        report.review_required = True
        report.review_reason = reason
        db.commit()

        appt = schedule_appointment(
            db,
            evaluation_id=evaluation.id,
            student_id=session.student_id,
            teacher_id=course.teacher_id,
            appt_type=_appt_type_from_reason(reason),
            reason=_reason_label(reason),
        )

        # Send appointment email
        if student:
            teacher = db.query(User).filter(User.id == course.teacher_id).first()
            scheduled_str = appt.scheduled_time.strftime("%A %d de %B de %Y, %H:%M hrs")
            send_appointment_email_sync(
                student_email=student.email,
                student_name=student.name,
                eval_title=evaluation.title,
                professor_name=teacher.name if teacher else "Profesor",
                scheduled_time_str=scheduled_str,
                appointment_type=appt.type,
                notes=appt.notes or "",
            )

    return session


def _appt_type_from_reason(reason: str) -> str:
    mapping = {
        "low_flash": "defense",
        "high_flash": "high_score_verification",
        "random": "random_verification",
        "ai_suspicion": "defense",
    }
    return mapping.get(reason, "defense")


def _reason_label(reason: str) -> str:
    labels = {
        "low_flash": "Resultado bajo el umbral mínimo en el flash test",
        "high_flash": "Resultado de excelencia — verificación de autenticidad",
        "random": "Selección aleatoria como parte del proceso de verificación",
        "ai_suspicion": "Indicadores elevados de contenido generado por IA",
    }
    return labels.get(reason, "Revisión requerida")


def find_next_available_slot(db: Session, teacher_id: int) -> datetime.datetime:
    """
    Finds the first free slot in the teacher's weekly availability starting tomorrow.
    Falls back to 3 days from now at 10:00 AM if no slots configured.
    """
    availabilities = db.query(TeacherAvailability).filter(
        TeacherAvailability.teacher_id == teacher_id
    ).all()

    if not availabilities:
        fallback = datetime.datetime.utcnow().date() + datetime.timedelta(days=3)
        return datetime.datetime.combine(fallback, datetime.time(10, 0))

    start_date = datetime.date.today() + datetime.timedelta(days=1)

    for i in range(14):
        current_date = start_date + datetime.timedelta(days=i)
        day_of_week = current_date.weekday()
        day_slots = [a for a in availabilities if a.day_of_week == day_of_week]

        for slot in day_slots:
            try:
                hour, minute = map(int, slot.start_time.split(":"))
                candidate = datetime.datetime.combine(current_date, datetime.time(hour, minute))
                existing = db.query(Appointment).filter(
                    Appointment.teacher_id == teacher_id,
                    Appointment.scheduled_time == candidate,
                    Appointment.status == "pending",
                ).first()
                if not existing:
                    return candidate
            except Exception:
                continue

    fallback = datetime.datetime.utcnow().date() + datetime.timedelta(days=4)
    return datetime.datetime.combine(fallback, datetime.time(11, 0))


def schedule_appointment(
    db: Session,
    evaluation_id: int,
    student_id: int,
    teacher_id: int,
    appt_type: str,
    reason: str,
) -> Appointment:
    """Creates and persists a new appointment. Returns the created appointment."""
    scheduled_time = find_next_available_slot(db, teacher_id)

    appt = Appointment(
        evaluation_id=evaluation_id,
        student_id=student_id,
        teacher_id=teacher_id,
        type=appt_type,
        scheduled_time=scheduled_time,
        status="pending",
        notes=f"Agendado automáticamente. Motivo: {reason}",
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)

    log_event(
        db,
        user_id=None,
        action=f"auto_schedule_{appt_type}",
        entity="appointment",
        entity_id=str(appt.id),
        details={
            "student_id": student_id,
            "teacher_id": teacher_id,
            "evaluation_id": evaluation_id,
            "scheduled_time": scheduled_time.isoformat(),
            "reason": reason,
        },
    )
    return appt
