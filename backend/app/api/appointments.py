from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import datetime

from app.core.database import get_db
from app.core.security import get_current_user, require_teacher, require_staff
from app.models.models import Appointment, User, TeacherAvailability, EvaluationSession, Course
from app.schemas.schemas import (
    AppointmentResponse, AppointmentFeedback, 
    TeacherAvailabilityCreate, TeacherAvailabilityResponse
)
from app.services.audit import log_event

router = APIRouter(prefix="/appointments", tags=["appointments"])

@router.get("/", response_model=List[AppointmentResponse])
def get_appointments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns appointments depending on the user's role:
    - Students see their own appointments.
    - Teachers see appointments assigned to them.
    - Admins see all appointments.
    """
    if current_user.role == "student":
        appts = db.query(Appointment).filter(Appointment.student_id == current_user.id).all()
    elif current_user.role == "teacher":
        appts = db.query(Appointment).filter(Appointment.teacher_id == current_user.id).all()
    else: # admin
        appts = db.query(Appointment).all()
        
    response = []
    for a in appts:
        ra = AppointmentResponse.from_orm(a)
        ra.student_name = a.student.name
        ra.teacher_name = a.teacher.name
        ra.evaluation_title = a.evaluation.title
        response.append(ra)
        
    return response

@router.post("/{appt_id}/feedback", response_model=AppointmentResponse)
def submit_appointment_feedback(
    appt_id: int,
    feedback: AppointmentFeedback,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """
    Allows the teacher to complete the defense/verification, record feedback notes,
    and optionally adjust the evaluation session score.
    """
    appt = db.query(Appointment).filter(Appointment.id == appt_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
        
    if appt.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permisos para evaluar esta cita")
        
    appt.status = feedback.status
    appt.notes = feedback.notes
    
    # If the teacher adjusted the score, locate the student's session and update it
    if feedback.adjusted_score is not None:
        session = db.query(EvaluationSession).filter(
            EvaluationSession.evaluation_id == appt.evaluation_id,
            EvaluationSession.student_id == appt.student_id
        ).order_by(EvaluationSession.created_at.desc()).first()
        
        if session:
            old_score = session.score
            # Ensure adjusted_score does not exceed total questions
            total_questions = appt.evaluation.num_questions
            session.score = float(feedback.adjusted_score)
            session.percentage_score = float(feedback.adjusted_score) / total_questions if total_questions > 0 else 0.0
            
            # Recalculate classification based on adjusted score
            if session.percentage_score < appt.evaluation.pass_threshold:
                session.classification = "low"
            elif session.percentage_score >= appt.evaluation.excellence_threshold:
                session.classification = "high"
            else:
                session.classification = "medium"
                
            log_event(
                db,
                user_id=current_user.id,
                action="adjust_score",
                entity="evaluation_session",
                entity_id=str(session.id),
                details={
                    "old_score": old_score,
                    "new_score": session.score,
                    "notes": feedback.notes
                }
            )
            
    db.commit()
    db.refresh(appt)
    
    # Audit log for meeting closure
    log_event(
        db,
        user_id=current_user.id,
        action=f"complete_appointment",
        entity="appointment",
        entity_id=str(appt.id),
        details={"status": appt.status, "notes": appt.notes}
    )
    
    response = AppointmentResponse.from_orm(appt)
    response.student_name = appt.student.name
    response.teacher_name = appt.teacher.name
    response.evaluation_title = appt.evaluation.title
    return response

@router.post("/{appt_id}/reschedule", response_model=AppointmentResponse)
def reschedule_appointment(
    appt_id: int,
    payload: dict, # {"new_time": "ISO-string"}
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Allows rescheduling a pending appointment.
    """
    appt = db.query(Appointment).filter(Appointment.id == appt_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
        
    # Check permissions: student or teacher of the appt
    if current_user.role == "student" and appt.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="No puedes reprogramar esta cita")
    elif current_user.role == "teacher" and appt.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="No puedes reprogramar esta cita")
        
    new_time_str = payload.get("new_time")
    if not new_time_str:
        raise HTTPException(status_code=400, detail="Falta el campo 'new_time'")
        
    try:
        new_time = datetime.datetime.fromisoformat(new_time_str.replace("Z", "+00:00"))
        # Strip timezone info for SQLite compatibility if naive datetimes are used
        new_time = new_time.replace(tzinfo=None)
    except Exception:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Utilice formato ISO 8601.")
        
    appt.scheduled_time = new_time
    appt.status = "pending" # reset if it was cancelled
    appt.notes = f"Reprogramado por {current_user.name} ({current_user.role})."
    
    db.commit()
    db.refresh(appt)
    
    log_event(
        db,
        user_id=current_user.id,
        action="reschedule_appointment",
        entity="appointment",
        entity_id=str(appt.id),
        details={"new_time": new_time.isoformat()}
    )
    
    response = AppointmentResponse.from_orm(appt)
    response.student_name = appt.student.name
    response.teacher_name = appt.teacher.name
    response.evaluation_title = appt.evaluation.title
    return response

# --- AVAILABILITY ENDPOINTS ---

@router.post("/availability", response_model=TeacherAvailabilityResponse, status_code=status.HTTP_201_CREATED)
def add_availability(
    avail_in: TeacherAvailabilityCreate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """
    Creates a weekly recurring availability slot for the teacher.
    """
    # Check for duplicate
    existing = db.query(TeacherAvailability).filter(
        TeacherAvailability.teacher_id == current_user.id,
        TeacherAvailability.day_of_week == avail_in.day_of_week,
        TeacherAvailability.start_time == avail_in.start_time
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Ya definiste este horario de disponibilidad")
        
    avail = TeacherAvailability(
        teacher_id=current_user.id,
        day_of_week=avail_in.day_of_week,
        start_time=avail_in.start_time,
        end_time=avail_in.end_time
    )
    db.add(avail)
    db.commit()
    db.refresh(avail)
    
    return avail

@router.get("/availability", response_model=List[TeacherAvailabilityResponse])
def get_my_availability(
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """
    Returns the availability slots of the logged-in teacher.
    """
    return db.query(TeacherAvailability).filter(TeacherAvailability.teacher_id == current_user.id).all()

@router.delete("/availability/{avail_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_availability(
    avail_id: int,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """
    Deletes an availability slot.
    """
    avail = db.query(TeacherAvailability).filter(
        TeacherAvailability.id == avail_id,
        TeacherAvailability.teacher_id == current_user.id
    ).first()
    
    if not avail:
        raise HTTPException(status_code=404, detail="Horario de disponibilidad no encontrado")
        
    db.delete(avail)
    db.commit()
    return
