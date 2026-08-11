from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import datetime

from app.core.database import get_db
from app.core.security import require_teacher, require_admin, require_staff
from app.models.models import Course, Evaluation, EvaluationSession, Answer, Report, User, AuditLog, Appointment, Question
from app.schemas.schemas import AuditLogResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/course/{course_id}/stats")
def get_course_stats(
    course_id: int,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """
    Returns general stats for a course. Only accessible by the course teacher.
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
        
    if course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="No eres el docente de este curso")
        
    total_students = len(course.students)
    evaluations = db.query(Evaluation).filter(Evaluation.course_id == course_id).all()
    eval_ids = [e.id for e in evaluations]
    
    # Reports uploaded
    reports_uploaded = db.query(Report).filter(Report.evaluation_id.in_(eval_ids)).count() if eval_ids else 0
    
    # Sessions completed
    sessions_completed = db.query(EvaluationSession).filter(
        EvaluationSession.evaluation_id.in_(eval_ids),
        EvaluationSession.status == "completed"
    ).all() if eval_ids else []
    
    total_sessions = len(sessions_completed)
    
    # Calculations
    avg_score = 0.0
    pass_rate = 0.0
    if total_sessions > 0:
        avg_score = sum(s.percentage_score for s in sessions_completed) / total_sessions
        passed_count = sum(1 for s in sessions_completed if s.classification != "low")
        pass_rate = passed_count / total_sessions
        
    # Pending appointments
    pending_appts = db.query(Appointment).filter(
        Appointment.evaluation_id.in_(eval_ids),
        Appointment.status == "pending"
    ).count() if eval_ids else 0
    
    # Student overview
    students_data = []
    for student in course.students:
        # Check if student completed any evaluation
        completed_evals = []
        for ev in evaluations:
            sess = db.query(EvaluationSession).filter(
                EvaluationSession.evaluation_id == ev.id,
                EvaluationSession.student_id == student.id
            ).order_by(EvaluationSession.created_at.desc()).first()
            
            status = "No entregado"
            score_str = "-"
            
            rep = db.query(Report).filter(Report.evaluation_id == ev.id, Report.student_id == student.id).first()
            if rep:
                status = "Pendiente Prueba"
                
            if sess:
                status = sess.status
                if sess.status == "completed":
                    status = "Rendida"
                    score_str = f"{int(sess.score)}/{ev.num_questions} ({int(sess.percentage_score*100)}%)"
                    
            completed_evals.append({
                "evaluation_id": ev.id,
                "evaluation_title": ev.title,
                "status": status,
                "score": score_str
            })
            
        students_data.append({
            "id": student.id,
            "name": student.name,
            "email": student.email,
            "evaluations": completed_evals
        })
        
    return {
        "course_name": course.name,
        "total_students": total_students,
        "reports_uploaded": reports_uploaded,
        "sessions_completed": total_sessions,
        "avg_score_percentage": avg_score,
        "pass_rate_percentage": pass_rate,
        "pending_appointments": pending_appts,
        "students": students_data
    }

@router.get("/evaluation/{evaluation_id}/stats")
def get_evaluation_stats(
    evaluation_id: int,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """
    Returns granular stats for an evaluation, including question metrics.
    """
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")
        
    if evaluation.course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="No eres el docente de este curso")
        
    sessions = db.query(EvaluationSession).filter(
        EvaluationSession.evaluation_id == evaluation_id,
        EvaluationSession.status == "completed"
    ).all()
    
    total_sessions = len(sessions)
    
    avg_score = 0.0
    pass_rate = 0.0
    low_count = 0
    medium_count = 0
    high_count = 0
    
    if total_sessions > 0:
        avg_score = sum(s.percentage_score for s in sessions) / total_sessions
        for s in sessions:
            if s.classification == "low":
                low_count += 1
            elif s.classification == "medium":
                medium_count += 1
            elif s.classification == "high":
                high_count += 1
        pass_rate = (medium_count + high_count) / total_sessions
        
    # Question analysis (granular items)
    # Get all answers linked to sessions of this evaluation
    session_ids = [s.id for s in sessions]
    
    question_stats = []
    if session_ids:
        answers = db.query(Answer).filter(Answer.session_id.in_(session_ids)).all()
        
        # Since questions are generated per student, we can summarize by question difficulty or category
        # Or, we can group questions by their templates / keywords or text.
        # To make it simple and readable, we can list the questions with the highest failure rates:
        questions_map = {}
        for ans in answers:
            q_id = ans.question_id
            if q_id not in questions_map:
                q = db.query(Question).filter(Question.id == q_id).first()
                questions_map[q_id] = {
                    "text": q.text if q else "Pregunta eliminada",
                    "type": q.type if q else "-",
                    "total_answers": 0,
                    "correct_answers": 0,
                    "total_time_ms": 0
                }
            
            stats = questions_map[q_id]
            stats["total_answers"] += 1
            if ans.is_correct:
                stats["correct_answers"] += 1
            if ans.response_time_ms:
                stats["total_time_ms"] += ans.response_time_ms
                
        # Format questions stats list
        for q_id, stats in questions_map.items():
            tot = stats["total_answers"]
            correct_rate = stats["correct_answers"] / tot if tot > 0 else 0.0
            avg_time_s = (stats["total_time_ms"] / tot / 1000) if tot > 0 else 0.0
            
            question_stats.append({
                "question_id": q_id,
                "text": stats["text"],
                "type": stats["type"],
                "total_responses": tot,
                "correct_rate": correct_rate,
                "avg_response_time_seconds": round(avg_time_s, 2),
                # If correct rate is low (e.g. < 40%), flag as problematic
                "is_problematic": correct_rate < 0.40 and tot >= 1
            })
            
    # Sort question stats: lowest correct rate first (highest failure rate)
    question_stats.sort(key=lambda x: x["correct_rate"])
    
    return {
        "evaluation_title": evaluation.title,
        "total_completed": total_sessions,
        "avg_score_percentage": round(avg_score, 2),
        "pass_rate_percentage": round(pass_rate, 2),
        "distribution": {
            "low": low_count,
            "medium": medium_count,
            "high": high_count
        },
        "questions_performance": question_stats
    }

@router.get("/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Returns audit logs for administration monitoring. Only accessible by admins.
    """
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()
    
    response = []
    for l in logs:
        rl = AuditLogResponse.from_orm(l)
        if l.user:
            rl.user_email = l.user.email
        else:
            rl.user_email = "System (Automático)"
        response.append(rl)
        
    return response

@router.get("/system-metrics")
def get_system_metrics(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Returns system diagnostic metrics: total users, total institutions, database size estimation,
    API LLM invocation counts, error logs.
    """
    users_count = db.query(User).count()
    teachers_count = db.query(User).filter(User.role == "teacher").count()
    students_count = db.query(User).filter(User.role == "student").count()
    
    # Count generated banks (corresponds to LLM calls)
    llm_calls = db.query(AuditLog).filter(AuditLog.action == "system_generate_bank").count()
    
    # Calculate mock vs real Claude calls
    mock_calls = db.query(AuditLog).filter(
        AuditLog.action == "system_generate_bank",
        AuditLog.details.like("%mock%") # simple query filter helper
    ).count() # approximation
    
    # Error rate (approximated from system logs)
    system_errors = db.query(AuditLog).filter(AuditLog.action.like("%error%")).count()
    
    return {
        "total_users": users_count,
        "teachers": teachers_count,
        "students": students_count,
        "llm_invocations": llm_calls,
        "system_errors": system_errors,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
