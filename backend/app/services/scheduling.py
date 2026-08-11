import datetime
import random
from sqlalchemy.orm import Session
from app.models.models import EvaluationSession, Evaluation, Appointment, TeacherAvailability, Course, enrollments, User
from app.services.audit import log_event

def process_session_result(db: Session, session_id: int) -> EvaluationSession:
    """
    Evaluates the final score of a session and triggers automatic scheduling
    and random peer verification workflows.
    """
    session = db.query(EvaluationSession).filter(EvaluationSession.id == session_id).first()
    if not session:
        raise ValueError(f"Sesión de evaluación {session_id} no encontrada")

    evaluation = db.query(Evaluation).filter(Evaluation.id == session.evaluation_id).first()
    course = db.query(Course).filter(Course.id == evaluation.course_id).first()
    
    # Calculate score percentage
    total_questions = evaluation.num_questions
    correct_answers = sum(1 for ans in session.answers if ans.is_correct)
    
    percentage = correct_answers / total_questions if total_questions > 0 else 0.0
    session.score = float(correct_answers)
    session.percentage_score = percentage
    session.end_time = datetime.datetime.utcnow()
    
    # Classify result
    if percentage < evaluation.pass_threshold:
        classification = "low"
    elif percentage >= evaluation.excellence_threshold:
        classification = "high"
    else:
        classification = "medium"
        
    session.classification = classification
    session.status = "completed"
    
    db.commit()
    db.refresh(session)
    
    # Log session completion in audit trail
    log_event(
        db,
        user_id=session.student_id,
        action="complete_eval",
        entity="evaluation_session",
        entity_id=str(session.id),
        details={
            "score": session.score,
            "percentage": percentage,
            "classification": classification
        }
    )

    # Trigger actions based on classification
    if classification == "low":
        # Low score: Schedule mandatory oral defense
        schedule_appointment(
            db,
            evaluation_id=evaluation.id,
            student_id=session.student_id,
            teacher_id=course.teacher_id,
            appt_type="defense",
            reason="Resultado bajo el umbral de aprobación"
        )
        
    elif classification == "high":
        # Excellent score: Schedule verification for this student
        schedule_appointment(
            db,
            evaluation_id=evaluation.id,
            student_id=session.student_id,
            teacher_id=course.teacher_id,
            appt_type="random_verification",
            reason="Resultado de excelencia: confirmación de autenticidad"
        )
        
        # Select random peer for verification (anti-fraud deterrence)
        select_and_schedule_random_peer(
            db,
            evaluation=evaluation,
            exclude_student_id=session.student_id,
            teacher_id=course.teacher_id
        )
        
    return session

def find_next_available_slot(db: Session, teacher_id: int) -> datetime.datetime:
    """
    Finds the first free slot in the teacher's weekly availability starting from tomorrow.
    If no availabilities are configured or all slots are taken in the next 14 days,
    returns a fallback slot (3 days from now at 10:00 AM).
    """
    availabilities = db.query(TeacherAvailability).filter(TeacherAvailability.teacher_id == teacher_id).all()
    
    if not availabilities:
        # Fallback: 3 days from now at 10:00 AM
        fallback_date = datetime.datetime.utcnow().date() + datetime.timedelta(days=3)
        return datetime.datetime.combine(fallback_date, datetime.time(10, 0))
        
    # Scan the next 14 days starting tomorrow
    start_date = datetime.date.today() + datetime.timedelta(days=1)
    
    for i in range(14):
        current_date = start_date + datetime.timedelta(days=i)
        # SQLAlchemy stores day_of_week where 0=Monday (Python's weekday() is also 0=Monday)
        day_of_week = current_date.weekday()
        
        # Check if teacher has availability for this day of the week
        day_slots = [a for a in availabilities if a.day_of_week == day_of_week]
        
        for slot in day_slots:
            try:
                hour, minute = map(int, slot.start_time.split(":"))
                candidate_time = datetime.datetime.combine(current_date, datetime.time(hour, minute))
                
                # Check if teacher already has a pending appointment at this exact time
                existing = db.query(Appointment).filter(
                    Appointment.teacher_id == teacher_id,
                    Appointment.scheduled_time == candidate_time,
                    Appointment.status == "pending"
                ).first()
                
                if not existing:
                    return candidate_time
            except Exception:
                continue
                
    # If all slots are full, schedule 4 days from now at 11:00 AM
    fallback_date = datetime.datetime.utcnow().date() + datetime.timedelta(days=4)
    return datetime.datetime.combine(fallback_date, datetime.time(11, 0))

def schedule_appointment(
    db: Session,
    evaluation_id: int,
    student_id: int,
    teacher_id: int,
    appt_type: str,
    reason: str
) -> Appointment:
    """
    Saves a new appointment in the database and logs the audit event.
    """
    scheduled_time = find_next_available_slot(db, teacher_id)
    
    appt = Appointment(
        evaluation_id=evaluation_id,
        student_id=student_id,
        teacher_id=teacher_id,
        type=appt_type,
        scheduled_time=scheduled_time,
        status="pending",
        notes=f"Agendado automáticamente. Motivo: {reason}"
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)
    
    # Audit log
    log_event(
        db,
        user_id=None, # System action
        action=f"auto_schedule_{appt_type}",
        entity="appointment",
        entity_id=str(appt.id),
        details={
            "student_id": student_id,
            "teacher_id": teacher_id,
            "evaluation_id": evaluation_id,
            "scheduled_time": scheduled_time.isoformat()
        }
    )
    
    return appt

def select_and_schedule_random_peer(
    db: Session,
    evaluation: Evaluation,
    exclude_student_id: int,
    teacher_id: int
):
    """
    Selects a random student enrolled in the course (excluding the excel student
    and any students already cited for this evaluation) and schedules a verification meeting.
    """
    # 1. Get all students enrolled in the course
    enrolled_students = db.query(User).join(
        enrollments, enrollments.c.student_id == User.id
    ).filter(
        enrollments.c.course_id == evaluation.course_id,
        User.id != exclude_student_id
    ).all()
    
    if not enrolled_students:
        print("No peers available for random selection in this course.")
        return
        
    # 2. Get students who already have appointments for this evaluation
    already_scheduled_ids = [
        a.student_id for a in db.query(Appointment.student_id).filter(
            Appointment.evaluation_id == evaluation.id
        ).all()
    ]
    
    # 3. Filter candidates
    candidates = [s for s in enrolled_students if s.id not in already_scheduled_ids]
    
    if not candidates:
        # If all candidates already have meetings, we can't schedule another one
        print("All peer students already have appointments scheduled for this evaluation.")
        return
        
    # 4. Pick one randomly
    chosen_peer = random.choice(candidates)
    
    # 5. Schedule appointment
    schedule_appointment(
        db,
        evaluation_id=evaluation.id,
        student_id=chosen_peer.id,
        teacher_id=teacher_id,
        appt_type="random_verification",
        reason="Selección aleatoria disuasiva (compañero con rendimiento excepcional)"
    )
