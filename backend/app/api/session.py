import json
import asyncio
import datetime
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.database import get_db, SessionLocal, settings
from app.core.security import get_current_user, require_student
from app.models.models import EvaluationSession, Evaluation, QuestionBank, Question, Answer, User, Course
from app.schemas.schemas import EvaluationSessionStart, EvaluationSessionResponse
from app.services.scheduling import process_session_result
from app.services.audit import log_event
from jose import jwt, JWTError

router = APIRouter(prefix="/session", tags=["evaluation-session"])

# In-memory tracking of active question starts to prevent cheating via page reload/disconnections.
# format: { session_id: { "question_id": int, "started_at": datetime } }
ACTIVE_QUESTION_TIMERS: Dict[int, Dict[str, Any]] = {}

@router.post("/start", response_model=EvaluationSessionResponse)
def start_evaluation_session(
    payload: EvaluationSessionStart,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    """
    Initializes a timed evaluation session.
    Validates deadline, active windows, report uploads, and checks for double submissions.
    """
    evaluation_id = payload.evaluation_id
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    
    if not evaluation:
        raise HTTPException(status_code=404, detail="La evaluación no existe")
        
    # Check enrollment
    if evaluation.course not in current_user.enrolled_courses:
        raise HTTPException(status_code=403, detail="No estás inscrito en este curso")
        
    # Check evaluation time window
    now = datetime.datetime.utcnow()
    if now < evaluation.start_window:
        raise HTTPException(
            status_code=400,
            detail=f"La ventana de evaluación aún no abre. Inicia el {evaluation.start_window}"
        )
    if now > evaluation.end_window:
        raise HTTPException(
            status_code=400,
            detail=f"La ventana de evaluación ya cerró el {evaluation.end_window}"
        )
        
    # Verify report is uploaded
    from app.models.models import Report
    report = db.query(Report).filter(
        Report.evaluation_id == evaluation_id,
        Report.student_id == current_user.id
    ).first()
    if not report:
        raise HTTPException(
            status_code=400,
            detail="Debes subir tu informe antes de iniciar la evaluación"
        )
        
    # Verify QuestionBank is generated and approved
    bank = db.query(QuestionBank).filter(
        QuestionBank.evaluation_id == evaluation_id,
        QuestionBank.student_id == current_user.id
    ).first()
    
    if not bank or not bank.is_generated:
        raise HTTPException(
            status_code=400,
            detail="Tu cuestionario personalizado aún se está generando. Por favor espera unos momentos."
        )
        
    if evaluation.require_approval and not bank.is_approved:
        raise HTTPException(
            status_code=400,
            detail="Tu cuestionario aún está pendiente de aprobación por el profesor"
        )
        
    # Check if a session already exists
    existing_session = db.query(EvaluationSession).filter(
        EvaluationSession.evaluation_id == evaluation_id,
        EvaluationSession.student_id == current_user.id
    ).first()
    
    if existing_session:
        if existing_session.status == "completed":
            raise HTTPException(
                status_code=400,
                detail="Ya has completado esta evaluación. Solo se permite un intento."
            )
        # If it was started but not completed, allow resuming
        return existing_session

    # Create new session
    session = EvaluationSession(
        evaluation_id=evaluation_id,
        student_id=current_user.id,
        status="started",
        start_time=datetime.datetime.utcnow()
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # Audit log
    log_event(
        db,
        user_id=current_user.id,
        action="start_eval",
        entity="evaluation_session",
        entity_id=str(session.id),
        details={"evaluation_title": evaluation.title}
    )
    
    return session

@router.get("/{session_id}/status", response_model=EvaluationSessionResponse)
def get_session_status(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(EvaluationSession).filter(EvaluationSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
        
    if current_user.role == "student" and session.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes acceso a esta sesión")
        
    return session

async def authenticate_ws_user(token: str, db: Session) -> User:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return db.query(User).filter(User.email == email).first()
    except JWTError:
        return None

@router.websocket("/ws/{session_id}")
async def evaluation_websocket(websocket: WebSocket, session_id: int, token: str):
    """
    WebSocket endpoint for administering the timed evaluation.
    Commands/actions:
    - Client connects -> sends active/next question
    - Client sends {"action": "answer", "question_id": int, "answer": str}
    - Server automatically advances when time runs out.
    """
    await websocket.accept()
    db = SessionLocal()
    
    # 1. Authenticate user from query parameter
    user = await authenticate_ws_user(token, db)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token inválido")
        db.close()
        return
        
    # 2. Fetch session and validate ownership
    session = db.query(EvaluationSession).filter(EvaluationSession.id == session_id).first()
    if not session:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Sesión no encontrada")
        db.close()
        return
        
    if session.student_id != user.id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Acceso denegado")
        db.close()
        return
        
    if session.status == "completed":
        await websocket.send_json({"type": "finished", "message": "Evaluación ya completada"})
        await websocket.close()
        db.close()
        return
        
    # 3. Retrieve bank and questions
    bank = db.query(QuestionBank).filter(
        QuestionBank.evaluation_id == session.evaluation_id,
        QuestionBank.student_id == user.id
    ).first()
    
    if not bank or not bank.questions:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Preguntas no generadas")
        db.close()
        return
        
    questions = bank.questions
    
    # 4. Main session loop
    try:
        for idx, q in enumerate(questions):
            # Check if this question was already answered (allows recovery from disconnect)
            existing_answer = db.query(Answer).filter(
                Answer.session_id == session.id,
                Answer.question_id == q.id
            ).first()
            
            if existing_answer:
                # Question already resolved, skip to next
                continue
                
            # Anti-cheat connection interruption management:
            # Check if there is an in-memory timer for this question.
            # If they disconnected and reconnected, we check if the time has already run out.
            now = datetime.datetime.utcnow()
            time_limit = q.limit_seconds
            
            if session.id in ACTIVE_QUESTION_TIMERS and ACTIVE_QUESTION_TIMERS[session.id]["question_id"] == q.id:
                started_at = ACTIVE_QUESTION_TIMERS[session.id]["started_at"]
                elapsed = (now - started_at).total_seconds()
                time_remaining = time_limit - elapsed
                
                if time_remaining <= 0:
                    # Time has already expired during disconnection. Mark as skipped and continue.
                    db_ans = Answer(
                        session_id=session.id,
                        question_id=q.id,
                        student_answer=None,
                        is_correct=False,
                        response_time_ms=time_limit * 1000
                    )
                    db.add(db_ans)
                    db.commit()
                    continue
                else:
                    time_limit = int(time_remaining)
            else:
                # New question. Start timer.
                ACTIVE_QUESTION_TIMERS[session.id] = {
                    "question_id": q.id,
                    "started_at": now
                }
                
            # Send question payload to client
            await websocket.send_json({
                "type": "question",
                "question_id": q.id,
                "text": q.text,
                "q_type": q.type,
                "options": q.options,
                "index": idx,
                "total": len(questions),
                "limit_seconds": time_limit
            })
            
            start_time = datetime.datetime.utcnow()
            student_response = None
            
            try:
                # Wait for client response. Timeout is strictly controlled on the server.
                # Adding 0.5s network buffer to ensure graceful socket timing
                raw_data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=float(time_limit) + 0.5
                )
                data = json.loads(raw_data)
                
                if data.get("action") == "answer" and data.get("question_id") == q.id:
                    student_response = data.get("answer")
                    
            except asyncio.TimeoutError:
                # Time's up
                await websocket.send_json({"type": "timeout", "message": "Tiempo agotado"})
            except Exception as e:
                # Socket error / parse error
                print(f"WS error: {e}")
                raise WebSocketDisconnect()
                
            # Record final answer
            end_time = datetime.datetime.utcnow()
            elapsed_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Check correctness
            is_correct = False
            if student_response is not None:
                # Clean strings for evaluation
                is_correct = (str(student_response).strip() == str(q.correct_answer).strip())
                
            db_ans = Answer(
                session_id=session.id,
                question_id=q.id,
                student_answer=student_response,
                is_correct=is_correct,
                response_time_ms=min(elapsed_ms, q.limit_seconds * 1000)
            )
            db.add(db_ans)
            db.commit()
            
            # Clean timer from memory
            ACTIVE_QUESTION_TIMERS.pop(session.id, None)
            
            # Audit log answer
            log_event(
                db,
                user_id=user.id,
                action="answer_question",
                entity="answer",
                entity_id=str(db_ans.id),
                details={"question_id": q.id, "is_correct": is_correct, "time_ms": elapsed_ms}
            )
            
            # Notify result to UI
            await websocket.send_json({
                "type": "result",
                "is_correct": is_correct
            })
            
            # 1 second buffer before the next question
            await asyncio.sleep(1.0)
            
        # 5. Complete Session & Trigger Scheduling Flow
        session = db.query(EvaluationSession).filter(EvaluationSession.id == session_id).first()
        process_session_result(db, session.id)
        
        # Reload to get final details
        db.refresh(session)
        
        await websocket.send_json({
            "type": "finished",
            "score": session.score,
            "percentage_score": session.percentage_score,
            "classification": session.classification
        })
        
    except WebSocketDisconnect:
        print(f"WS disconnect for session {session_id}")
    except Exception as e:
        print(f"WS unexpected exception: {e}")
    finally:
        # Clean memory on connection close
        ACTIVE_QUESTION_TIMERS.pop(session_id, None)
        db.close()
        try:
            await websocket.close()
        except Exception:
            pass
