import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Request, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app import models, schemas
from backend.app.config import settings
from backend.app.auth import get_current_user, check_course_access
from backend.app.services.email_service import send_flash_test_email
from backend.app.services.websocket_mgr import ws_manager
from backend.app.audit import log_audit

router = APIRouter(tags=["Flash Test en Tiempo Real"])

def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

@router.post("/api/asignaturas/{asignatura_id}/flash-test/despacho", response_model=schemas.FlashTestDispatchResponse)
async def dispatch_flash_tests(
    asignatura_id: int,
    request: Request,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Despacho masivo o individual de tokens UUIDv4 con vigencia 48h vía Gmail SMTP (RF-010, RN-001).
    """
    course = check_course_access(asignatura_id, current_user, db)
    students = db.query(models.Estudiante).filter(models.Estudiante.asignatura_id == asignatura_id).all()
    
    course_params = course.parametros or {}
    tiempo_segundos = int(course_params.get("tiempo_test_segundos", 60))
    base_url = str(request.base_url).rstrip("/")

    dispatched_items = []
    
    for s in students:
        # Check student has evaluated work
        if not s.trabajo or not s.trabajo.evaluacion:
            continue

        # Check if an active test already exists
        existing_test = db.query(models.FlashTest).filter(
            models.FlashTest.estudiante_id == s.id,
            models.FlashTest.estado.in_(["pendiente", "en_progreso"])
        ).first()

        now = datetime.now(timezone.utc)
        if existing_test and ensure_utc(existing_test.vigencia) > now:
            token = existing_test.token
            flash_test = existing_test
        else:
            token = str(uuid.uuid4())
            flash_test = models.FlashTest(
                estudiante_id=s.id,
                token=token,
                vigencia=now + timedelta(hours=48),
                tiempo_limite_segundos=tiempo_segundos,
                estado="pendiente"
            )
            db.add(flash_test)
            db.commit()
            db.refresh(flash_test)

        test_link = f"{base_url}/test/{token}"
        email_sent = await send_flash_test_email(
            student_name=s.nombre,
            student_email=s.correo,
            course_name=course.nombre,
            test_link=test_link
        )

        dispatched_items.append(
            schemas.FlashTestDispatchItem(
                estudiante_id=s.id,
                token=token,
                correo=s.correo,
                enlace_test=test_link,
                correo_enviado=email_sent
            )
        )

    log_audit(
        db=db,
        accion="DESPACHO_FLASH_TESTS",
        tabla="flash_tests",
        registro_id=course.id,
        usuario_id=current_user.id,
        datos_nuevos={"total_despachados": len(dispatched_items)}
    )

    return schemas.FlashTestDispatchResponse(
        total_despachados=len(dispatched_items),
        items=dispatched_items
    )

@router.get("/api/flash-test/{token}/info", response_model=schemas.FlashTestPublicInfo)
def get_flash_test_info(token: str, db: Session = Depends(get_db)):
    """
    Public student endpoint (Zero-login via Token, RN-001).
    Validates token and returns questions without revealing correct answer.
    """
    test = db.query(models.FlashTest).filter(models.FlashTest.token == token).first()
    if not test:
        raise HTTPException(status_code=404, detail="Enlace de verificación inválido o inexistente")

    now = datetime.now(timezone.utc)
    if test.estado == "completado":
        raise HTTPException(status_code=400, detail="Este Flash Test ya ha sido completado y cerrado.")

    if ensure_utc(test.vigencia) < now:
        test.estado = "expirado"
        db.commit()
        raise HTTPException(status_code=400, detail="Este enlace ha expirado (vigencia 48h superada).")

    student = test.estudiante
    course = student.asignatura
    evaluacion = student.trabajo.evaluacion if student.trabajo else None
    
    if not evaluacion:
        raise HTTPException(status_code=400, detail="No hay evaluación asociada a este test.")

    # Get selected questions
    selected_questions = [q for q in evaluacion.preguntas if q.seleccionada]
    if not selected_questions:
        selected_questions = evaluacion.preguntas[:5]

    safe_questions = []
    for q in selected_questions:
        safe_alts = [{"id": a["id"], "texto": a["texto"]} for a in q.alternativas]
        safe_questions.append({
            "id": q.id,
            "texto": q.texto,
            "seccion_origen": q.seccion_origen,
            "alternativas": safe_alts
        })

    session = ws_manager.get_or_create_session(token, test.tiempo_limite_segundos)
    remaining = session.remaining_seconds if session.is_active else test.tiempo_limite_segundos

    return schemas.FlashTestPublicInfo(
        token=token,
        estudiante_nombre=student.nombre,
        asignatura_nombre=course.nombre,
        tiempo_limite_segundos=test.tiempo_limite_segundos,
        tiempo_restante_segundos=remaining,
        estado=test.estado,
        preguntas=safe_questions
    )

def evaluate_and_close_test(
    test: models.FlashTest,
    respuestas: Dict[str, str],
    tiempo_transcurrido: int,
    db: Session
) -> float:
    """
    Computes score and coherence based on answered questions (RN-002).
    Updates student's evaluation with real Flash Test results.
    """
    evaluacion = test.estudiante.trabajo.evaluacion
    selected_questions = [q for q in evaluacion.preguntas if q.seleccionada]
    if not selected_questions:
        selected_questions = evaluacion.preguntas[:5]

    total_preguntas = len(selected_questions)
    correctas = 0
    falladas = []

    for q in selected_questions:
        q_id_str = str(q.id)
        chosen = respuestas.get(q_id_str)
        # Find correct alternative
        correct_alt = next((a["id"] for a in q.alternativas if a.get("es_correcta")), "A")
        if chosen == correct_alt:
            correctas += 1
        else:
            falladas.append(f"{q.texto[:45]}...")

    score = round((correctas / max(total_preguntas, 1)) * 100.0, 1)
    
    test.respuestas = respuestas
    test.puntaje = score
    test.tiempo_transcurrido = tiempo_transcurrido
    test.estado = "completado"
    test.fecha_completado = datetime.now(timezone.utc)

    # Update Anexo A evaluacion_respuestas in Evaluacion.desglose
    if evaluacion.desglose:
        updated_desglose = dict(evaluacion.desglose)
        course_params = test.estudiante.asignatura.parametros or {}
        umbral_coherencia = float(course_params.get("umbral_coherencia", 60.0))
        umbral_ia = float(course_params.get("umbral_ia", 40.0))
        
        requiere_defensa = (score < umbral_coherencia) or (evaluacion.pct_ia >= umbral_ia)

        updated_desglose["evaluacion_respuestas"] = {
            "nivel_rigor_aplicado": course_params.get("nivel_rigor", "medium"),
            "porcentaje_coherencia": f"{int(score)}%",
            "respuestas_correctas": f"{correctas}/{total_preguntas}",
            "preguntas_falladas": falladas,
            "observacion_ia": (
                "Bajo desempeño en verificación flash. Se detectan inconsistencias entre el texto entregado y las respuestas del alumno."
                if score < umbral_coherencia
                else "Respuestas flash consistentes con la autoría y comprensión de los conceptos del informe."
            ),
            "requiere_defensa_oral": requiere_defensa
        }
        evaluacion.desglose = updated_desglose

    db.commit()
    return score

@router.post("/api/flash-test/{token}/submit")
async def submit_flash_test(
    token: str,
    payload: schemas.SubmitAnswerRequest,
    db: Session = Depends(get_db)
):
    """
    Submit Flash Test via HTTP (or automatic on timer expiry, RN-002)
    """
    test = db.query(models.FlashTest).filter(models.FlashTest.token == token).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test no encontrado")
    if test.estado == "completado":
        return {"status": "already_completed", "puntaje": test.puntaje}

    score = evaluate_and_close_test(test, payload.respuestas, payload.tiempo_transcurrido, db)

    # Broadcast to student WebSocket and teacher dashboard
    await ws_manager.broadcast_to_session(token, {
        "type": "TEST_COMPLETED",
        "score": score,
        "message": "Flash Test finalizado con éxito"
    })
    await ws_manager.notify_teacher_dashboard(test.estudiante.asignatura_id, {
        "type": "STUDENT_TEST_FINISHED",
        "estudiante_id": test.estudiante_id,
        "score": score
    })

    return {
        "status": "success",
        "puntaje": score,
        "mensaje": "Respuestas registradas exitosamente"
    }

@router.websocket("/ws/flash-test/{token}")
async def websocket_flash_test(websocket: WebSocket, token: str, db: Session = Depends(get_db)):
    """
    Real-time WebSocket endpoint for Flash Test (RF-011, RNF-001, RN-002, RNF-008)
    - Sub-50ms latency response
    - 60s live countdown
    - Resilient reconnection (preserves state <= 120s)
    - Automatic partial scoring on expiration
    """
    test = db.query(models.FlashTest).filter(models.FlashTest.token == token).first()
    if not test or test.estado == "completado":
        await websocket.accept()
        await websocket.send_json({"type": "ERROR", "message": "Test no válido o ya completado"})
        await websocket.close()
        return

    session = await ws_manager.connect_student(websocket, token, test.tiempo_limite_segundos)

    try:
        # Send initial state
        await websocket.send_json({
            "type": "INIT_STATE",
            "is_active": session.is_active,
            "remaining_seconds": session.remaining_seconds if session.is_active else test.tiempo_limite_segundos,
            "answers": session.answers
        })

        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "START_TIMER":
                if not session.is_active:
                    session.is_active = True
                    session.start_time = datetime.now(timezone.utc).timestamp()
                    test.estado = "en_progreso"
                    test.fecha_inicio = datetime.now(timezone.utc)
                    db.commit()

                await ws_manager.broadcast_to_session(token, {
                    "type": "TIMER_TICK",
                    "remaining_seconds": session.remaining_seconds
                })

            elif msg_type == "ANSWER_CHANGE":
                # Real-time state preservation (RNF-008)
                q_id = str(data.get("question_id"))
                ans = data.get("answer")
                session.answers[q_id] = ans
                await websocket.send_json({"type": "ACK", "question_id": q_id})

            elif msg_type == "PING":
                # Latency measurement (RNF-001 <= 50ms)
                await websocket.send_json({"type": "PONG", "ts": data.get("ts")})

            elif msg_type == "SUBMIT" or msg_type == "TIME_EXPIRED":
                # Finish test and score partial or full (RN-002)
                answers = data.get("answers", session.answers)
                elapsed = session.elapsed_seconds
                score = evaluate_and_close_test(test, answers, elapsed, db)
                session.is_completed = True

                await ws_manager.broadcast_to_session(token, {
                    "type": "TEST_COMPLETED",
                    "score": score
                })
                await ws_manager.notify_teacher_dashboard(test.estudiante.asignatura_id, {
                    "type": "STUDENT_TEST_FINISHED",
                    "estudiante_id": test.estudiante_id,
                    "score": score
                })
                break

    except WebSocketDisconnect:
        ws_manager.disconnect_student(websocket, token)
    except Exception as e:
        ws_manager.disconnect_student(websocket, token)
