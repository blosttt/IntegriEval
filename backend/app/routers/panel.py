from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app import models, schemas
from backend.app.auth import get_current_user, check_course_access
from backend.app.services.websocket_mgr import ws_manager
from backend.app.audit import log_audit

router = APIRouter(tags=["Panel Docente y Cierre"])

@router.get("/api/asignaturas/{asignatura_id}/panel", response_model=schemas.PanelResultadosOut)
def get_teacher_panel(
    asignatura_id: int,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Teacher Results Dashboard (RF-012):
    Calculates summary metrics, highlights students exceeding AI threshold or low Flash coherence,
    and supports informed oral defense decision making.
    """
    course = check_course_access(asignatura_id, current_user, db)
    params = course.parametros or {}
    umbral_ia = float(params.get("umbral_ia", 40.0))
    umbral_coherencia = float(params.get("umbral_coherencia", 60.0))

    students = db.query(models.Estudiante).filter(models.Estudiante.asignatura_id == asignatura_id).all()

    total_alumnos = len(students)
    analizados = 0
    alerta_ia = 0
    requieren_defensa = 0
    tests_completados = 0
    notas_cerradas = 0

    filas = []
    for s in students:
        trabajo = s.trabajo
        evaluacion = trabajo.evaluacion if trabajo else None
        flash_test = db.query(models.FlashTest).filter(models.FlashTest.estudiante_id == s.id).order_by(models.FlashTest.id.desc()).first()
        cita = db.query(models.Cita).filter(models.Cita.estudiante_id == s.id).order_by(models.Cita.id.desc()).first()

        trabajo_estado = trabajo.estado if trabajo else "sin_entrega"
        nota_preliminar = evaluacion.nota if evaluacion else None
        pct_ia = evaluacion.pct_ia if evaluacion else None

        confianza_ia = None
        coherencia_str = None
        req_def = False
        pct_logro = None

        if evaluacion:
            analizados += 1
            if pct_ia is not None and pct_ia >= umbral_ia:
                alerta_ia += 1

            desglose = evaluacion.desglose or {}
            confianza_ia = desglose.get("deteccion_ia", {}).get("nivel_confianza", "medio")
            coherencia_str = desglose.get("evaluacion_respuestas", {}).get("porcentaje_coherencia")
            req_def = desglose.get("evaluacion_respuestas", {}).get("requiere_defensa_oral", False)

            raw_logro = desglose.get("porcentaje_logro")
            if raw_logro:
                try:
                    pct_logro = float(str(raw_logro).replace("%", "").strip())
                except Exception:
                    pct_logro = None
            if pct_logro is None and evaluacion.nota is not None:
                if evaluacion.nota >= 4.0:
                    pct_logro = round(60.0 + (evaluacion.nota - 4.0) * (40.0 / 3.0), 1)
                else:
                    pct_logro = round(max(0.0, (evaluacion.nota - 1.0) * (60.0 / 3.0)), 1)

        puntaje_flash = flash_test.puntaje if flash_test else None
        if flash_test and flash_test.estado == "completado":
            tests_completados += 1
            if puntaje_flash is not None and puntaje_flash < umbral_coherencia:
                req_def = True

        if req_def:
            requieren_defensa += 1

        is_cerrada = flash_test.nota_cerrada if flash_test else False
        if is_cerrada:
            notas_cerradas += 1

        pct_logro_final = None
        if flash_test and flash_test.nota_final_confirmada is not None:
            val = flash_test.nota_final_confirmada
            if val > 7.0:
                pct_logro_final = round(val, 1)
            else:
                if val >= 4.0:
                    pct_logro_final = round(60.0 + (val - 4.0) * (40.0 / 3.0), 1)
                else:
                    pct_logro_final = round(max(0.0, (val - 1.0) * (60.0 / 3.0)), 1)
        elif is_cerrada:
            pct_logro_final = pct_logro

        disp_logro = None
        active_logro = pct_logro_final if (is_cerrada and pct_logro_final is not None) else pct_logro
        if active_logro is not None:
            disp_logro = f"{int(active_logro) if active_logro.is_integer() else active_logro}%"

        filas.append(
            schemas.PanelEstudianteFila(
                estudiante_id=s.id,
                estudiante_nombre=s.nombre,
                estudiante_correo=s.correo,
                trabajo_estado=trabajo_estado,
                pct_logro=pct_logro,
                pct_logro_final=pct_logro_final,
                porcentaje_logro=disp_logro,
                nota_preliminar=nota_preliminar,
                pct_ia=pct_ia,
                confianza_ia=confianza_ia,
                coherencia_flash=coherencia_str,
                puntaje_flash=puntaje_flash,
                requiere_defensa=req_def,
                cita_id=cita.id if cita else None,
                cita_fecha=cita.fecha.strftime("%Y-%m-%d %H:%M") if cita else None,
                cita_bloque=cita.bloque if cita else None,
                cita_estado=cita.estado if cita else None,
                nota_final=flash_test.nota_final_confirmada if flash_test else nota_preliminar,
                justificacion_nota=flash_test.justificacion_nota if flash_test else "Criterio del docente",
                nota_cerrada=is_cerrada,
                flash_test_token=flash_test.token if flash_test else None
            )
        )

    return schemas.PanelResultadosOut(
        asignatura_id=course.id,
        asignatura_nombre=course.nombre,
        total_alumnos=total_alumnos,
        analizados=analizados,
        alerta_ia=alerta_ia,
        requieren_defensa=requieren_defensa,
        tests_completados=tests_completados,
        notas_cerradas=notas_cerradas,
        estudiantes=filas
    )

@router.post("/api/asignaturas/{asignatura_id}/citas", response_model=schemas.CitaOut)
def schedule_oral_defense(
    asignatura_id: int,
    data: schemas.CitaCreate,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Schedule an oral defense appointment for an alerted student (RF-013)
    """
    course = check_course_access(asignatura_id, current_user, db)
    student = db.query(models.Estudiante).filter(
        models.Estudiante.id == data.estudiante_id,
        models.Estudiante.asignatura_id == asignatura_id
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado en esta asignatura")

    cita = models.Cita(
        estudiante_id=student.id,
        docente_id=current_user.id,
        fecha=data.fecha,
        bloque=data.bloque,
        acuerdos=data.acuerdos,
        estado="programada",
        creada_por=current_user.nombre
    )
    db.add(cita)
    db.commit()
    db.refresh(cita)

    log_audit(
        db=db,
        accion="AGENDAR_DEFENSA_ORAL",
        tabla="citas",
        registro_id=cita.id,
        usuario_id=current_user.id,
        datos_nuevos={
            "estudiante_id": student.id,
            "estudiante_nombre": student.nombre,
            "fecha": str(cita.fecha),
            "bloque": cita.bloque
        }
    )

    return schemas.CitaOut(
        id=cita.id,
        estudiante_id=cita.estudiante_id,
        estudiante_nombre=student.nombre,
        docente_id=cita.docente_id,
        fecha=cita.fecha,
        bloque=cita.bloque,
        estado=cita.estado,
        acuerdos=cita.acuerdos,
        creada_por=cita.creada_por
    )

@router.post("/api/asignaturas/{asignatura_id}/cerrar-nota")
def close_grade(
    asignatura_id: int,
    data: schemas.CierreNotaRequest,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cierre de calificaciones con nota editable y justificación obligatoria (RF-013, RN-004, RNF-003 <= 200ms).
    Persists immutable audit log.
    """
    course = check_course_access(asignatura_id, current_user, db)
    student = db.query(models.Estudiante).filter(
        models.Estudiante.id == data.estudiante_id,
        models.Estudiante.asignatura_id == asignatura_id
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    # Fetch latest FlashTest or create a closing record
    test = db.query(models.FlashTest).filter(models.FlashTest.estudiante_id == student.id).order_by(models.FlashTest.id.desc()).first()
    if not test:
        test = models.FlashTest(
            estudiante_id=student.id,
            estado="completado"
        )
        db.add(test)

    nota_previa = test.nota_final_confirmada or (student.trabajo.evaluacion.nota if student.trabajo and student.trabajo.evaluacion else None)

    # RN-004: Campo justificación obligatorio (defecto 'Criterio del docente')
    justificacion = data.justificacion.strip() if data.justificacion and data.justificacion.strip() else "Criterio del docente"

    test.nota_final_confirmada = data.nota_final
    test.justificacion_nota = justificacion
    test.nota_cerrada = True
    test.fecha_cierre = datetime.now(timezone.utc)

    db.commit()

    # Immutable AuditLog (RN-004, RD-AuditLog)
    log_audit(
        db=db,
        accion="CIERRE_MODIFICACION_NOTA",
        tabla="flash_tests",
        registro_id=test.id,
        usuario_id=current_user.id,
        datos_previos={"nota_previa": nota_previa},
        datos_nuevos={
            "estudiante_id": student.id,
            "estudiante_nombre": student.nombre,
            "nota_final": data.nota_final,
            "justificacion": justificacion
        }
    )

    return {
        "status": "success",
        "mensaje": f"Porcentaje de logro final ({data.nota_final}%) confirmado para {student.nombre}",
        "nota_final": data.nota_final,
        "justificacion": justificacion
    }

@router.websocket("/ws/panel/{asignatura_id}")
async def websocket_teacher_panel(websocket: WebSocket, asignatura_id: int):
    """Teacher live dashboard observer WebSocket (RF-012, RNF-001)"""
    await ws_manager.connect_teacher(websocket, asignatura_id)
    try:
        while True:
            # Keep alive and respond to client pings
            data = await websocket.receive_json()
            if data.get("type") == "PING":
                await websocket.send_json({"type": "PONG", "ts": data.get("ts")})
    except WebSocketDisconnect:
        ws_manager.disconnect_teacher(websocket, asignatura_id)
    except Exception:
        ws_manager.disconnect_teacher(websocket, asignatura_id)
