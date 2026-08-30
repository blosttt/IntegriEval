"""
Flash Test API — accessed by students via a one-time email token (no account required).
"""
import json
import asyncio
import datetime
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.database import get_db, SessionLocal
from app.models.models import (
    Report, FlashTestSession, QuestionBank, Question, Answer, Student, Evaluation
)
from app.schemas.schemas import FlashTokenValidateResponse, FlashTestSessionResponse
from app.services.scheduling import process_flash_test_result
from app.services.audit import log_event

router = APIRouter(prefix="/flash", tags=["flash-test"])

# In-memory timer tracking: { session_id: { "question_id": int, "started_at": datetime } }
ACTIVE_TIMERS: Dict[int, Dict[str, Any]] = {}


# ─────────────────────────────────────────────────────────────────────────────
# TOKEN VALIDATION — Student enters via email link
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/validate/{token}", response_model=FlashTokenValidateResponse)
def validate_flash_token(token: str, db: Session = Depends(get_db)):
    """
    Validates the one-time token from the email link.
    Returns session info needed for the frontend to start the test.
    """
    report = db.query(Report).filter(Report.flash_token == token).first()
    if not report:
        raise HTTPException(status_code=404, detail="Enlace inválido o expirado")

    now = datetime.datetime.utcnow()
    if report.flash_token_expires_at and now > report.flash_token_expires_at:
        raise HTTPException(status_code=410, detail="El enlace del flash test ha expirado")

    if report.flash_completed:
        raise HTTPException(status_code=400, detail="Ya completaste este flash test")

    session = db.query(FlashTestSession).filter(FlashTestSession.report_id == report.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sesión de flash test no encontrada")

    bank = db.query(QuestionBank).filter(QuestionBank.report_id == report.id).first()
    if not bank or not bank.is_approved:
        raise HTTPException(status_code=400, detail="El profesor aún no ha activado tu flash test")

    selected_ids = bank.selected_question_ids or [q.id for q in bank.questions]
    total_questions = len(selected_ids)

    student = db.query(Student).filter(Student.id == report.student_id).first()
    evaluation = db.query(Evaluation).filter(Evaluation.id == report.evaluation_id).first()

    return FlashTokenValidateResponse(
        session_id=session.id,
        student_name=student.name if student else "Estudiante",
        evaluation_title=evaluation.title if evaluation else "",
        total_questions=total_questions,
        time_per_question=evaluation.time_per_question if evaluation else 30,
    )


@router.get("/{session_id}/result", response_model=FlashTestSessionResponse)
def get_flash_result(session_id: int, token: str, db: Session = Depends(get_db)):
    """
    Returns the result of a completed flash session.
    Requires the original flash token for authentication.
    """
    session = db.query(FlashTestSession).filter(FlashTestSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    report = db.query(Report).filter(Report.id == session.report_id).first()
    if not report or report.flash_token != token:
        raise HTTPException(status_code=403, detail="Token inválido")

    if session.status != "completed":
        raise HTTPException(status_code=400, detail="El flash test aún no ha sido completado")

    return session


# ─────────────────────────────────────────────────────────────────────────────
# WEBSOCKET — Timed Question Loop
# ─────────────────────────────────────────────────────────────────────────────

@router.websocket("/ws/{session_id}")
async def flash_test_websocket(websocket: WebSocket, session_id: int, token: str):
    """
    WebSocket for administering the timed flash test.
    Authentication: flash token passed as query param.

    Protocol:
    - Server sends: { type: "question", question_id, text, q_type, options, index, total, limit_seconds }
    - Client sends: { action: "answer", question_id: int, answer: str | null }
    - Server sends: { type: "result", is_correct: bool }
    - Server sends: { type: "timeout" } if time runs out
    - Server sends: { type: "finished", score, percentage_score, classification }
    """
    await websocket.accept()
    db = SessionLocal()

    try:
        # ── Auth via token ────────────────────────────────────────────────
        report = db.query(Report).filter(Report.flash_token == token).first()
        if not report:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token inválido")
            return

        now = datetime.datetime.utcnow()
        if report.flash_token_expires_at and now > report.flash_token_expires_at:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token expirado")
            return

        if report.flash_completed:
            await websocket.send_json({"type": "finished", "message": "Ya completaste este flash test"})
            await websocket.close()
            return

        # ── Load session ──────────────────────────────────────────────────
        session = db.query(FlashTestSession).filter(FlashTestSession.id == session_id).first()
        if not session or session.report_id != report.id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Sesión inválida")
            return

        if session.status == "completed":
            await websocket.send_json({"type": "finished", "message": "Sesión ya completada"})
            await websocket.close()
            return

        if session.status == "pending":
            session.status = "started"
            session.started_at = datetime.datetime.utcnow()
            db.commit()

        # ── Load questions ────────────────────────────────────────────────
        bank = db.query(QuestionBank).filter(QuestionBank.report_id == report.id).first()
        if not bank:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Sin banco de preguntas")
            return

        selected_ids = bank.selected_question_ids or [q.id for q in bank.questions]
        questions = [
            db.query(Question).filter(Question.id == qid).first()
            for qid in selected_ids
        ]
        questions = [q for q in questions if q is not None]

        evaluation = db.query(Evaluation).filter(Evaluation.id == session.evaluation_id).first()

        # ── Question loop ─────────────────────────────────────────────────
        for idx, q in enumerate(questions):
            # Skip already answered (reconnect recovery)
            existing_answer = db.query(Answer).filter(
                Answer.session_id == session.id,
                Answer.question_id == q.id,
            ).first()
            if existing_answer:
                continue

            now = datetime.datetime.utcnow()
            time_limit = q.limit_seconds

            # Timer continuity on reconnect
            if session.id in ACTIVE_TIMERS and ACTIVE_TIMERS[session.id]["question_id"] == q.id:
                started_at = ACTIVE_TIMERS[session.id]["started_at"]
                elapsed = (now - started_at).total_seconds()
                time_remaining = time_limit - elapsed
                if time_remaining <= 0:
                    # Record skipped answer
                    db.add(Answer(
                        session_id=session.id,
                        question_id=q.id,
                        student_answer=None,
                        is_correct=False,
                        response_time_ms=time_limit * 1000,
                    ))
                    db.commit()
                    continue
                else:
                    time_limit = int(time_remaining)
            else:
                ACTIVE_TIMERS[session.id] = {"question_id": q.id, "started_at": now}

            # Send question to client
            await websocket.send_json({
                "type": "question",
                "question_id": q.id,
                "text": q.text,
                "q_type": q.type,
                "options": q.options,
                "index": idx,
                "total": len(questions),
                "limit_seconds": time_limit,
            })

            start_time = datetime.datetime.utcnow()
            student_response = None

            try:
                raw_data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=float(time_limit) + 0.5,
                )
                data = json.loads(raw_data)
                if data.get("action") == "answer" and data.get("question_id") == q.id:
                    student_response = data.get("answer")
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "timeout", "message": "Tiempo agotado"})
            except Exception:
                raise WebSocketDisconnect()

            # Record answer
            end_time = datetime.datetime.utcnow()
            elapsed_ms = int((end_time - start_time).total_seconds() * 1000)
            is_correct = (
                str(student_response).strip() == str(q.correct_answer).strip()
                if student_response is not None else False
            )

            db.add(Answer(
                session_id=session.id,
                question_id=q.id,
                student_answer=student_response,
                is_correct=is_correct,
                response_time_ms=min(elapsed_ms, q.limit_seconds * 1000),
            ))
            db.commit()

            ACTIVE_TIMERS.pop(session.id, None)

            log_event(db, user_id=None, action="flash_answer",
                      entity="answer", entity_id=str(session.id),
                      details={"question_id": q.id, "is_correct": is_correct, "ms": elapsed_ms})

            await websocket.send_json({"type": "result", "is_correct": is_correct})
            await asyncio.sleep(1.0)

        # ── Finalize session ──────────────────────────────────────────────
        final_session = process_flash_test_result(db, session.id)

        await websocket.send_json({
            "type": "finished",
            "score": final_session.score,
            "percentage_score": final_session.percentage_score,
            "classification": final_session.classification,
        })

    except WebSocketDisconnect:
        print(f"[flash_ws] Student disconnected from session {session_id}")
    except Exception as e:
        print(f"[flash_ws] Unexpected error session {session_id}: {e}")
    finally:
        ACTIVE_TIMERS.pop(session_id, None)
        db.close()
        try:
            await websocket.close()
        except Exception:
            pass
