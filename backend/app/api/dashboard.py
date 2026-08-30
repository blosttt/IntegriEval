from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import datetime

from app.core.database import get_db
from app.core.security import require_teacher, require_admin
from app.models.models import (
    Course, Evaluation, FlashTestSession, Report, Student,
    User, AuditLog, Appointment
)
from app.schemas.schemas import AuditLogResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/course/{course_id}/stats")
def get_course_stats(
    course_id: int,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """Returns general stats for a course."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    if current_user.role == "teacher" and course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="No eres el docente de este curso")

    total_students = db.query(Student).filter(Student.course_id == course_id).count()
    evaluations = db.query(Evaluation).filter(Evaluation.course_id == course_id).all()
    eval_ids = [e.id for e in evaluations]

    reports_uploaded = (
        db.query(Report).filter(Report.evaluation_id.in_(eval_ids)).count()
        if eval_ids else 0
    )
    reports_analyzed = (
        db.query(Report).filter(
            Report.evaluation_id.in_(eval_ids),
            Report.analysis_status == "done"
        ).count()
        if eval_ids else 0
    )
    flash_sent = (
        db.query(Report).filter(
            Report.evaluation_id.in_(eval_ids),
            Report.flash_email_sent == True
        ).count()
        if eval_ids else 0
    )
    flash_completed = (
        db.query(Report).filter(
            Report.evaluation_id.in_(eval_ids),
            Report.flash_completed == True
        ).count()
        if eval_ids else 0
    )
    pending_appointments = (
        db.query(Appointment).filter(
            Appointment.evaluation_id.in_(eval_ids),
            Appointment.status == "pending"
        ).count()
        if eval_ids else 0
    )

    return {
        "course_name": course.name,
        "total_students": total_students,
        "total_evaluations": len(evaluations),
        "reports_uploaded": reports_uploaded,
        "reports_analyzed": reports_analyzed,
        "flash_emails_sent": flash_sent,
        "flash_tests_completed": flash_completed,
        "pending_appointments": pending_appointments,
    }


@router.get("/evaluation/{evaluation_id}/stats")
def get_evaluation_stats(
    evaluation_id: int,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """Returns granular stats for an evaluation."""
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")
    if current_user.role == "teacher" and evaluation.course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="No eres el docente de este curso")

    reports = db.query(Report).filter(Report.evaluation_id == evaluation_id).all()
    total_reports = len(reports)

    # AI score distribution
    ai_scores = [r.ai_score_percentage for r in reports if r.ai_score_percentage is not None]
    avg_ai_score = round(sum(ai_scores) / len(ai_scores), 3) if ai_scores else None

    # AI detection distribution
    ai_detections = [r.ai_detected_percentage for r in reports if r.ai_detected_percentage is not None]
    avg_ai_detection = round(sum(ai_detections) / len(ai_detections), 3) if ai_detections else None

    # Flash test results
    flash_sessions = db.query(FlashTestSession).filter(
        FlashTestSession.evaluation_id == evaluation_id,
        FlashTestSession.status == "completed"
    ).all()

    total_flash_completed = len(flash_sessions)
    low_count = sum(1 for s in flash_sessions if s.classification == "low")
    medium_count = sum(1 for s in flash_sessions if s.classification == "medium")
    high_count = sum(1 for s in flash_sessions if s.classification == "high")

    flash_scores = [s.percentage_score for s in flash_sessions if s.percentage_score is not None]
    avg_flash_score = round(sum(flash_scores) / len(flash_scores), 3) if flash_scores else None

    # Appointments
    appointments = db.query(Appointment).filter(Appointment.evaluation_id == evaluation_id).all()

    # Per-student table
    students_data = []
    students = db.query(Student).filter(Student.course_id == evaluation.course_id).all()
    for student in students:
        report = next((r for r in reports if r.student_id == student.id), None)
        flash = next((s for s in flash_sessions if s.student_id == student.id), None)
        appt = next((a for a in appointments if a.student_id == student.id), None)

        students_data.append({
            "student_id": student.id,
            "student_name": student.name,
            "student_email": student.email,
            "report_uploaded": report is not None,
            "analysis_status": report.analysis_status if report else None,
            "ai_score": report.ai_score_percentage if report else None,
            "final_score": report.final_score_percentage if report else None,
            "ai_detected_pct": report.ai_detected_percentage if report else None,
            "flash_email_sent": report.flash_email_sent if report else False,
            "flash_completed": report.flash_completed if report else False,
            "flash_score": flash.percentage_score if flash else None,
            "flash_classification": flash.classification if flash else None,
            "review_required": report.review_required if report else False,
            "review_reason": report.review_reason if report else None,
            "appointment_status": appt.status if appt else None,
            "appointment_time": appt.scheduled_time.isoformat() if appt else None,
        })

    return {
        "evaluation_title": evaluation.title,
        "total_students": len(students),
        "total_reports": total_reports,
        "avg_ai_score": avg_ai_score,
        "avg_ai_detection_pct": avg_ai_detection,
        "flash_test": {
            "completed": total_flash_completed,
            "avg_score": avg_flash_score,
            "distribution": {"low": low_count, "medium": medium_count, "high": high_count},
        },
        "appointments": {
            "total": len(appointments),
            "pending": sum(1 for a in appointments if a.status == "pending"),
            "completed": sum(1 for a in appointments if a.status == "completed"),
        },
        "students": students_data,
    }


@router.get("/review-list/{evaluation_id}")
def get_review_list(
    evaluation_id: int,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """Returns students flagged for office review for a given evaluation."""
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")
    if current_user.role == "teacher" and evaluation.course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sin acceso")

    flagged_reports = db.query(Report).filter(
        Report.evaluation_id == evaluation_id,
        Report.review_required == True
    ).all()

    result = []
    for report in flagged_reports:
        student = db.query(Student).filter(Student.id == report.student_id).first()
        flash = db.query(FlashTestSession).filter(
            FlashTestSession.report_id == report.id
        ).first()
        appt = db.query(Appointment).filter(
            Appointment.evaluation_id == evaluation_id,
            Appointment.student_id == report.student_id
        ).first()

        result.append({
            "report_id": report.id,
            "student_id": report.student_id,
            "student_name": student.name if student else None,
            "student_email": student.email if student else None,
            "review_reason": report.review_reason,
            "ai_score": report.ai_score_percentage,
            "flash_score": flash.percentage_score if flash else None,
            "flash_classification": flash.classification if flash else None,
            "appointment_status": appt.status if appt else "sin_cita",
            "appointment_time": appt.scheduled_time.isoformat() if appt else None,
        })

    return {"evaluation_id": evaluation_id, "review_list": result}


@router.get("/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Audit logs — admin only."""
    logs = (
        db.query(AuditLog)
        .order_by(AuditLog.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    response = []
    for log in logs:
        rl = AuditLogResponse.model_validate(log)
        rl.user_email = log.user.email if log.user else "System"
        response.append(rl)
    return response


@router.get("/system-metrics")
def get_system_metrics(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """System diagnostic metrics — admin only."""
    return {
        "total_users": db.query(User).count(),
        "teachers": db.query(User).filter(User.role == "teacher").count(),
        "students_no_account": db.query(Student).count(),
        "total_reports": db.query(Report).count(),
        "analyses_done": db.query(Report).filter(Report.analysis_status == "done").count(),
        "flash_tests_completed": db.query(FlashTestSession).filter(FlashTestSession.status == "completed").count(),
        "flash_emails_sent": db.query(Report).filter(Report.flash_email_sent == True).count(),
        "appointments_total": db.query(Appointment).count(),
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }
