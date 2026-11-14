import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Request, status, Body
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool
from backend.app.database import get_db
from backend.app import models, schemas
from backend.app.config import settings
from backend.app.auth import get_current_user, check_course_access
from backend.app.services.email_service import send_flash_test_email
from backend.app.services.websocket_mgr import ws_manager
from backend.app.audit import log_audit

from backend.app.activities import parameters, work_for, test_evaluation, assert_activity_open, lock_question_plan

from backend.app.services.adaptive import advance_branch, compile_plan, snapshot

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
    estudiante_ids: Optional[List[int]] = Body(default=None),
    actividad_id: Optional[int] = None,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Despacho masivo o individual de tokens UUIDv4 con vigencia 48h vía Gmail SMTP (RF-010, RN-001).
    """
    course = check_course_access(asignatura_id, current_user, db, write=True)
    students = db.query(models.Estudiante).filter(models.Estudiante.asignatura_id == asignatura_id, ~models.Estudiante.id.in_(db.query(models.StudentStatus.estudiante_id).filter_by(active=False))).all()
    if estudiante_ids is not None:
        valid_ids = {s.id for s in students}
        if not estudiante_ids or not set(estudiante_ids) <= valid_ids:
            raise HTTPException(422, "Seleccione estudiantes de esta asignatura")
        students = [s for s in students if s.id in estudiante_ids]
    
    assert_activity_open(asignatura_id, actividad_id, db)
    course_params = parameters(course, actividad_id, db)
    tiempo_segundos = int(course_params.get("tiempo_test_segundos", 60))

    dispatched_items = []
    
    for s in students:
        plan = await run_in_threadpool(prepare_dispatch, asignatura_id, actividad_id, s.id, tiempo_segundos, estudiante_ids is not None, db)
        if plan is None:
            continue
        flash_test = plan
        token = flash_test.token
        test_link = f"{settings.PUBLIC_APP_URL.rstrip(chr(47))}/flash/{token}"
        email_sent = await send_flash_test_email(
            student_name=s.nombre,
            student_email=s.correo,
            course_name=course.nombre,
            test_link=test_link,
            seconds_per_question=flash_test.tiempo_limite_segundos
        )

        db.add(models.MailDelivery(asignatura_id=asignatura_id, estudiante_id=s.id, purpose='flash', reference_id=flash_test.id, recipient=s.correo, subject=f'IntegryEval · Flash Test · {course.nombre}', body=f'Hola {s.nombre}, abre tu Flash Test: {test_link}\nVigencia: {flash_test.vigencia}.', status='sent' if email_sent else ('disabled' if not settings.SMTP_ENABLED else 'failed'), attempts=1, error=None if email_sent else 'Correo no enviado; revisa la configuración SMTP', sent_at=datetime.now(timezone.utc) if email_sent else None))
        db.commit()
        dispatched_items.append(
            schemas.FlashTestDispatchItem(
                estudiante_id=s.id,
                actividad_id=actividad_id,
                token=token,
                correo=s.correo,
                enlace_test=test_link,
                correo_enviado=email_sent,
                error=None if email_sent else ("SMTP desactivado: utilice el enlace local" if not settings.SMTP_ENABLED else "No se pudo enviar el correo; utilice el enlace")
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
    return schemas.FlashTestDispatchResponse(total_despachados=len(dispatched_items), items=dispatched_items)


def prepare_dispatch(course_id, activity_id, student_id, seconds, explicit, db):
    try:
        lock_question_plan(course_id, db)
        assert_activity_open(course_id, activity_id, db)
        flash = prepare_student_test(activity_id, student_id, seconds, explicit, db)
        db.commit()
        return flash
    except Exception:
        db.rollback()
        raise


def prepare_student_test(activity_id, student_id, seconds, explicit, db):
    # Check student has evaluated work
    work = work_for(student_id, activity_id, db)
    if not work or not work.evaluacion:
        return None

    provenance = work.evaluacion.desglose or {}
    if work.estado != "analizado":
        if explicit:
            raise HTTPException(409, "El análisis no está completo. Reintenta el procesamiento antes de despachar el Flash Test.")
        return None
    if settings.LLM_PROVIDER != "mock" and (
        provenance.get("fallback_ia") or provenance.get("motor_analisis") == "mock"
        or provenance.get("motor_preguntas") == "mock"
    ):
        if explicit:
            raise HTTPException(409, "La evaluación contiene resultados simulados. Reanaliza el informe con la IA real antes de despachar el Flash Test.")
        return None

    if not any(q.seleccionada for q in work.evaluacion.preguntas):
        return None
    if db.query(models.FlashTest).filter_by(estudiante_id=student_id, actividad_id=activity_id, estado="completado").first():
        return None
    # Check if an active test already exists
    existing_test = db.query(models.FlashTest).filter(
        models.FlashTest.estudiante_id == student_id,
        models.FlashTest.actividad_id == activity_id,
        models.FlashTest.estado.in_(["pendiente", "en_progreso"])
    ).first()

    now = datetime.now(timezone.utc)
    reused = existing_test and ensure_utc(existing_test.vigencia) > now
    if reused:
        flash_test = existing_test
    else:
        token = str(uuid.uuid4())
        flash_test = models.FlashTest(
            estudiante_id=student_id,
            actividad_id=activity_id,
            token=token,
            vigencia=now + timedelta(hours=48),
            tiempo_limite_segundos=seconds,
            estado="pendiente"
        )
        db.add(flash_test)
        db.flush()

    state = get_state(flash_test, db)
    rubric = provenance.get("rubrica_aplicada")
    activity_params = parameters(work.estudiante.asignatura, activity_id, db)
    if activity_params.get("requiere_rubrica") and not rubric and not reused:
        raise HTTPException(422, "Analiza el informe con la rubrica antes de despachar.")
    if rubric and not reused:
        required = {row["nombre"] for row in rubric["criterios"]}
        selected = {q.get("seccion_origen") for q in state.preguntas}
        if not required <= selected:
            raise HTTPException(422, "Selecciona al menos una pregunta por cada criterio de la rubrica.")
        expected = int(activity_params.get("num_preguntas_test", 5))
        if len(state.preguntas) != expected:
            raise HTTPException(422, f"Selecciona exactamente {expected} preguntas.")
    return flash_test


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
    if test.estado == "completado":
        return test.puntaje
    state = get_state(test, db)
    test.respuestas = respuestas
    test.tiempo_transcurrido = tiempo_transcurrido
    test.estado = "completado"
    test.fecha_completado = datetime.now(timezone.utc)
    from backend.app.services.development import refresh_score
    refresh_score(test, state, db)
    db.commit()
    return test.puntaje



def get_state(test, db):
    state = db.get(models.FlashTestState, test.id)
    if state is None:
        evaluation = test_evaluation(test, db)
        if not evaluation:
            raise HTTPException(409, "No hay evaluación asociada")
        selected = [q for q in evaluation.preguntas if q.seleccionada]
        if not selected:
            raise HTTPException(409, "Seleccione preguntas antes del despacho")
        state = models.FlashTestState(test_id=test.id, preguntas=[snapshot(q) for q in selected], indice=0)
        db.add(state)
        plan = db.get(models.AdaptivePlan, evaluation.id)
        if plan and plan.reglas:
            db.add(models.AdaptiveSession(test_id=test.id, reglas=compile_plan(evaluation, plan.reglas)))
        db.flush()
    return state


def advance_time(test, state, db):
    now = datetime.now(timezone.utc)
    if test.estado in {"completado", "expirado"}:
        return
    if ensure_utc(test.vigencia) <= now:
        test.estado = "expirado"
        return
    if not state.inicio_pregunta:
        return
    while state.indice < len(state.preguntas) and (now - ensure_utc(state.inicio_pregunta)).total_seconds() >= test.tiempo_limite_segundos:
        advance_branch(test, state, db, None)
        state.indice += 1
        state.inicio_pregunta = ensure_utc(state.inicio_pregunta) + timedelta(seconds=test.tiempo_limite_segundos)
    if state.indice == len(state.preguntas):
        elapsed = int((now - ensure_utc(test.fecha_inicio)).total_seconds())
        evaluate_and_close_test(test, test.respuestas or {}, elapsed, db)


def load_test(token, db, allow_completed=False, keep_lock=False):
    from sqlalchemy import update
    try:
        db.execute(update(models.FlashTest).where(models.FlashTest.token == token).values(estado=models.FlashTest.estado))
        db.expire_all()
        test = db.query(models.FlashTest).filter_by(token=token).first()
        if not test:
            raise HTTPException(404, "Test no encontrado")
        student_status = db.get(models.StudentStatus, test.estudiante_id)
        if (student_status and not student_status.active) or (test.estudiante.asignatura.parametros or {}).get('_archived'):
            raise HTTPException(410, "El enlace de esta evaluación ya no está activo")
        state = get_state(test, db)
        advance_time(test, state, db)
        if test.estado == "expirado":
            db.commit()
            raise HTTPException(410, "El enlace ha expirado")
        if test.estado == "completado" and not allow_completed:
            raise HTTPException(409, "Este test ya ha sido completado")
        if not keep_lock:
            db.commit()
        return test, state
    except Exception:
        db.rollback()
        raise


from contextlib import contextmanager


@contextmanager
def locked_test(token, db):
    try:
        yield load_test(token, db, allow_completed=True, keep_lock=True)
        db.commit()
    except Exception:
        db.rollback()
        raise


def public_state(test, state):
    remaining = test.tiempo_limite_segundos
    if state.inicio_pregunta:
        remaining = max(0, remaining - int((datetime.now(timezone.utc) - ensure_utc(state.inicio_pregunta)).total_seconds()))
    visible = state.preguntas
    if state.adaptive is not None and test.estado != "completado":
        visible = visible[:state.indice + 1] if test.estado == "en_progreso" else []
    return {
        "adaptativo": state.adaptive is not None,
        "token": test.token, "estudiante_nombre": test.estudiante.nombre,
        "asignatura_nombre": test.estudiante.asignatura.nombre,
        "asignatura_periodo": test.estudiante.asignatura.periodo,
        "tiempo_limite_segundos": test.tiempo_limite_segundos,
        "tiempo_restante_segundos": remaining, "tiempo_segundos": test.tiempo_limite_segundos,
        "num_preguntas": len(state.preguntas), "pregunta_actual": state.indice,
        "estado": test.estado, "respuestas": test.respuestas or {},
        "puntaje": test.puntaje,
        "preguntas": [{"id": q['id'], "texto": q['texto'], "tipo": q.get('tipo', 'alternativas'),
            "seccion_origen": q.get('seccion_origen'),
            "alternativas": [{"id": a["id"], "texto": a["texto"]} for a in q["alternativas"]]} for q in visible]
    }


async def notify_result(test):
    await ws_manager.notify_teacher_dashboard(test.estudiante.asignatura_id, {
        "type": "STUDENT_TEST_FINISHED", "estudiante_id": test.estudiante_id, "score": test.puntaje
    })
    await ws_manager.broadcast_to_session(test.token, {"type": "TEST_COMPLETED", "score": test.puntaje})


@router.get("/api/flash-test/{token}/info")
def get_flash_test_info(token: str, db: Session = Depends(get_db)):
    test, state = load_test(token, db, allow_completed=True)
    return public_state(test, state)


@router.post("/api/flash-test/{token}/start")
def start_flash_test(token: str, db: Session = Depends(get_db)):
    with locked_test(token, db) as (test, state):
        if test.estado == "pendiente":
            test.estado = "en_progreso"
            test.fecha_inicio = datetime.now(timezone.utc)
            state.inicio_pregunta = test.fecha_inicio
        return public_state(test, state)


from pydantic import BaseModel, Field
class AnswerRequest(BaseModel):
    question_id: int
    answer: Optional[str] = Field(default=None, max_length=5000)


def _record_answer(token, payload, db):
    with locked_test(token, db) as (test, state):
        completed = False
        if test.estado == "completado":
            return public_state(test, state), test, completed
        if test.estado != "en_progreso":
            raise HTTPException(409, "Inicie el test antes de responder")
        question = state.preguntas[state.indice]
        if payload.question_id != question["id"]:
            if str(payload.question_id) in (test.respuestas or {}):
                return public_state(test, state), test, completed
            raise HTTPException(409, "La pregunta ya no está activa")
        if question.get('tipo', 'alternativas') == 'desarrollo':
            if not (payload.answer or '').strip():
                raise HTTPException(422, 'Escribe tu respuesta antes de enviarla')
        elif payload.answer is not None and payload.answer not in {item["id"] for item in question["alternativas"]}:
            raise HTTPException(422, "Alternativa inválida")
        test.respuestas = {**(test.respuestas or {}), str(question["id"]): payload.answer}
        advance_branch(test, state, db, payload.answer)
        state.indice += 1
        state.inicio_pregunta = datetime.now(timezone.utc)
        if state.indice == len(state.preguntas):
            evaluate_and_close_test(test, test.respuestas, int((datetime.now(timezone.utc) - ensure_utc(test.fecha_inicio)).total_seconds()), db)
            completed = True
        return public_state(test, state), test, completed


async def record_answer(token, payload, db):
    response, test, completed = await run_in_threadpool(_record_answer, token, payload, db)
    if completed:
        await notify_result(test)
    return response


@router.post("/api/flash-test/{token}/answer")
async def answer_flash_test(token: str, payload: AnswerRequest, db: Session = Depends(get_db)):
    return await record_answer(token, payload, db)


@router.post('/api/flash-test/{token}/draft')
def save_development_draft(token: str, payload: AnswerRequest, db: Session = Depends(get_db)):
    with locked_test(token, db) as (test, state):
        if test.estado != 'en_progreso':
            raise HTTPException(409, 'La pregunta ya no está activa')
        question = state.preguntas[state.indice]
        if question['id'] != payload.question_id or question.get('tipo') != 'desarrollo':
            raise HTTPException(409, 'Solo se guarda el texto de la pregunta de desarrollo activa')
        test.respuestas = {**(test.respuestas or {}), str(question['id']): payload.answer or ''}
        return public_state(test, state)


def _submit_flash_test(token, payload, db):
    if payload.token != token:
        raise HTTPException(422, "El token no coincide con el enlace")
    with locked_test(token, db) as (test, state):
        completed = False
        if test.estado != "completado":
            if test.estado != "en_progreso":
                raise HTTPException(409, "El test no ha sido iniciado")
            evaluate_and_close_test(test, test.respuestas or {}, int((datetime.now(timezone.utc) - ensure_utc(test.fecha_inicio)).total_seconds()), db)
            completed = True
        from backend.app.services.development import score_details
        details = score_details(test, state, db)
        return ({"status": "success", "porcentaje_logro": test.puntaje, "puntaje": test.puntaje, "tiempo_transcurrido": test.tiempo_transcurrido,
                **{key: value for key, value in details.items() if key not in {'falladas', 'puntaje'}}}, test, completed)


@router.post("/api/flash-test/{token}/submit")
async def submit_flash_test(token: str, payload: schemas.SubmitAnswerRequest, db: Session = Depends(get_db)):
    response, test, completed = await run_in_threadpool(_submit_flash_test, token, payload, db)
    if completed:
        await notify_result(test)
    return response


@router.websocket("/ws/flash-test/{token}")
async def websocket_flash_test(websocket: WebSocket, token: str, db: Session = Depends(get_db)):
    import asyncio
    try:
        test, state = load_test(token, db, allow_completed=True)
    except HTTPException:
        await websocket.close(code=1008)
        return
    await ws_manager.connect_student(websocket, token, test.tiempo_limite_segundos)
    try:
        while True:
            db.expire_all()
            test, state = load_test(token, db, allow_completed=True)
            await websocket.send_json({"type": "STATE", **public_state(test, state)})
            if test.estado == "completado":
                await notify_result(test)
                break
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=1)
            except asyncio.TimeoutError:
                continue
            kind = data.get("type")
            if kind == "PING":
                await websocket.send_json({"type": "PONG", "ts": data.get("ts")})
            elif kind == "START_TIMER":
                start_flash_test(token, db)
            elif kind == "ANSWER_CHANGE":
                await record_answer(token, AnswerRequest(question_id=data.get("question_id"), answer=data.get("answer")), db)
    except (WebSocketDisconnect, HTTPException):
        pass
    finally:
        ws_manager.disconnect_student(websocket, token)


async def sweep_active_tests(session_factory):
    """Persist timeouts even when the student's browser is disconnected."""
    import asyncio
    import logging
    while True:
        await asyncio.sleep(1)
        with session_factory() as db:
            tests = db.query(models.FlashTest).filter_by(estado="en_progreso").all()
            for test in tests:
                try:
                    from sqlalchemy import update
                    db.execute(update(models.FlashTest).where(models.FlashTest.id == test.id).values(estado=models.FlashTest.estado))
                    db.expire_all()
                    if test.estado != 'en_progreso':
                        db.commit()
                        continue
                    state = get_state(test, db)
                    before = test.estado
                    advance_time(test, state, db)
                    db.commit()
                    if test.estado == "completado" and before != "completado":
                        await notify_result(test)
                except Exception:
                    db.rollback()
                    logging.getLogger(__name__).exception("No se pudo actualizar el cronómetro del test %s", test.id)
