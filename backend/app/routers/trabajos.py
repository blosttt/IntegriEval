import os
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, BackgroundTasks
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app import models, schemas
from backend.app.config import settings
from backend.app.auth import get_current_user, check_course_access
from backend.app.services.pdf_service import extract_pdf_to_markdown, match_student_filename
from backend.app.services.llm_service import evaluate_submission_llm, generate_question_pool_llm
from backend.app.audit import log_audit

router = APIRouter(tags=["Trabajos y Evaluación"])

async def process_and_evaluate_trabajo(trabajo_id: int, asignatura_id: int, db: Session, user_id: int):
    """
    Background or direct task:
    1. Extracts PDF into structured Markdown (RF-006)
    2. Runs LLM / Mock Engine to evaluate (RF-007)
    3. Generates Question Pool (RF-008, 10-30 questions)
    """
    trabajo = db.query(models.Trabajo).filter(models.Trabajo.id == trabajo_id).first()
    if not trabajo:
        return

    course = db.query(models.Asignatura).filter(models.Asignatura.id == asignatura_id).first()
    course_params = course.parametros or {}
    
    # 1. Semantic PDF extraction
    try:
        if trabajo.pdf_path and os.path.exists(trabajo.pdf_path):
            md_text = extract_pdf_to_markdown(trabajo.pdf_path)
            trabajo.markdown = md_text
            trabajo.estado = "analizado"
            db.commit()
    except Exception as e:
        trabajo.estado = "error"
        db.commit()
        return

    # Gather contextual materials (Syllabus, Rubric)
    materials = db.query(models.Material).filter(models.Material.asignatura_id == asignatura_id).all()
    syllabus_text = "\n\n".join(m.markdown for m in materials if m.tipo in ["syllabus", "guia"])
    rubric_text = "\n\n".join(m.markdown for m in materials if m.tipo == "rubrica")

    # 2. Run LLM / Mock evaluation (RF-007)
    anexo_a_data, nota_preliminar, pct_ia = await evaluate_submission_llm(
        markdown_content=trabajo.markdown or "",
        syllabus_content=syllabus_text,
        rubric_content=rubric_text,
        nivel_rigor=course_params.get("nivel_rigor", "medium"),
        umbral_ia=float(course_params.get("umbral_ia", 40.0)),
        umbral_coherencia=float(course_params.get("umbral_coherencia", 60.0)),
        prompt_custom=course_params.get("prompt_custom", "")
    )

    # Delete existing evaluation if re-evaluating
    if trabajo.evaluacion:
        db.delete(trabajo.evaluacion)
        db.commit()

    evaluacion = models.Evaluacion(
        trabajo_id=trabajo.id,
        nota=nota_preliminar,
        feedback=anexo_a_data.get("feedback", {}),
        pct_ia=pct_ia,
        desglose=anexo_a_data
    )
    db.add(evaluacion)
    db.commit()
    db.refresh(evaluacion)

    # 3. Generate Question Pool (RF-008, 10-30 questions)
    pool_size = int(course_params.get("pool_size", 15))
    num_selected = int(course_params.get("num_preguntas_test", 5))
    questions_data = await generate_question_pool_llm(
        markdown_content=trabajo.markdown or "",
        syllabus_content=syllabus_text,
        pool_size=pool_size
    )

    for idx, q_dict in enumerate(questions_data):
        is_sel = idx < num_selected
        pregunta = models.Pregunta(
            evaluacion_id=evaluacion.id,
            texto=q_dict["texto"],
            alternativas=q_dict["alternativas"],
            seleccionada=is_sel,
            justificacion_respuesta=q_dict.get("justificacion_respuesta"),
            seccion_origen=q_dict.get("seccion_origen")
        )
        db.add(pregunta)

    db.commit()

    log_audit(
        db=db,
        accion="EVALUACION_GENERADA",
        tabla="evaluaciones",
        registro_id=evaluacion.id,
        usuario_id=user_id,
        datos_nuevos={
            "estudiante_id": trabajo.estudiante_id,
            "nota_preliminar": nota_preliminar,
            "pct_ia": pct_ia,
            "total_preguntas": len(questions_data)
        }
    )

@router.post("/api/asignaturas/{asignatura_id}/trabajos/upload")
async def upload_trabajo_single(
    asignatura_id: int,
    estudiante_id: int = Form(...),
    file: UploadFile = File(...),
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a single PDF for a specific student and trigger extraction & evaluation (RF-005, RF-006, RF-007)
    """
    check_course_access(asignatura_id, current_user, db)

    student = db.query(models.Estudiante).filter(
        models.Estudiante.id == estudiante_id,
        models.Estudiante.asignatura_id == asignatura_id
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado en esta asignatura")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo del trabajo debe estar en formato PDF")

    course_work_dir = settings.WORKS_DIR / f"course_{asignatura_id}"
    os.makedirs(course_work_dir, exist_ok=True)
    saved_path = course_work_dir / f"std_{estudiante_id}_{file.filename}"

    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Check if student already has a trabajo
    trabajo = db.query(models.Trabajo).filter(models.Trabajo.estudiante_id == estudiante_id).first()
    if not trabajo:
        trabajo = models.Trabajo(
            estudiante_id=estudiante_id,
            pdf_path=str(saved_path),
            estado="cargado"
        )
        db.add(trabajo)
    else:
        trabajo.pdf_path = str(saved_path)
        trabajo.estado = "cargado"

    db.commit()
    db.refresh(trabajo)

    # Run processing and evaluation synchronously or directly
    await process_and_evaluate_trabajo(trabajo.id, asignatura_id, db, current_user.id)

    return {
        "status": "success",
        "message": f"Informe procesado y evaluado para {student.nombre}",
        "trabajo_id": trabajo.id
    }

@router.post("/api/asignaturas/{asignatura_id}/trabajos/batch")
async def upload_trabajos_batch(
    asignatura_id: int,
    files: List[UploadFile] = File(...),
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Massive upload of student PDFs with automatic association by filename (RF-005)
    """
    check_course_access(asignatura_id, current_user, db)

    students = db.query(models.Estudiante).filter(models.Estudiante.asignatura_id == asignatura_id).all()
    student_lookup = [
        {"id": s.id, "nombre": s.nombre, "correo": s.correo, "rut": s.rut}
        for s in students
    ]

    matched_count = 0
    unmatched = []
    course_work_dir = settings.WORKS_DIR / f"course_{asignatura_id}"
    os.makedirs(course_work_dir, exist_ok=True)

    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            unmatched.append({"file": file.filename, "reason": "No es archivo PDF"})
            continue

        matched_id = match_student_filename(file.filename, student_lookup)
        if not matched_id:
            unmatched.append({"file": file.filename, "reason": "No se pudo asociar a ningún estudiante por nombre/correo"})
            continue

        saved_path = course_work_dir / f"std_{matched_id}_{file.filename}"
        with open(saved_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        trabajo = db.query(models.Trabajo).filter(models.Trabajo.estudiante_id == matched_id).first()
        if not trabajo:
            trabajo = models.Trabajo(
                estudiante_id=matched_id,
                pdf_path=str(saved_path),
                estado="cargado"
            )
            db.add(trabajo)
        else:
            trabajo.pdf_path = str(saved_path)
            trabajo.estado = "cargado"

        db.commit()
        db.refresh(trabajo)

        await process_and_evaluate_trabajo(trabajo.id, asignatura_id, db, current_user.id)
        matched_count += 1

    return {
        "status": "success",
        "total_archivos": len(files),
        "asociados_y_evaluados": matched_count,
        "no_asociados": unmatched
    }

@router.get("/api/asignaturas/{asignatura_id}/estudiantes/{estudiante_id}/evaluacion")
def get_student_evaluation(
    asignatura_id: int,
    estudiante_id: int,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve full evaluation details (Anexo A) for a student (RF-007)"""
    check_course_access(asignatura_id, current_user, db)

    trabajo = db.query(models.Trabajo).filter(models.Trabajo.estudiante_id == estudiante_id).first()
    if not trabajo or not trabajo.evaluacion:
        raise HTTPException(status_code=404, detail="No existe evaluación disponible para este estudiante")

    return {
        "evaluacion_id": trabajo.evaluacion.id,
        "nota": trabajo.evaluacion.nota,
        "pct_ia": trabajo.evaluacion.pct_ia,
        "feedback": trabajo.evaluacion.feedback,
        "desglose": trabajo.evaluacion.desglose,
        "fecha_creacion": trabajo.evaluacion.fecha_creacion
    }
