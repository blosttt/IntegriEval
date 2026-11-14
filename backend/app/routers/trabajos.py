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
from backend.app.services.llm_service import evaluate_submission_llm, generate_question_pool_llm, LLMUnavailable
from backend.app.audit import log_audit
from backend.app.services.assessment import configured_context, rubric_text as format_rubric

from backend.app.activities import parameters, work_for, assert_activity_open

router = APIRouter(tags=["Trabajos y Evaluación"])

async def process_and_evaluate_trabajo(trabajo_id: int, asignatura_id: int, db: Session, user_id: int):
    try:
        await _process_and_evaluate_trabajo(trabajo_id, asignatura_id, db, user_id)
    except LLMUnavailable as exc:
        db.rollback()
        trabajo = db.get(models.Trabajo, trabajo_id)
        if trabajo:
            trabajo.estado = "error"
            db.commit()
        raise HTTPException(503, str(exc)) from exc


async def _process_and_evaluate_trabajo(trabajo_id: int, asignatura_id: int, db: Session, user_id: int):
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
    assert_activity_open(asignatura_id, trabajo.actividad_id, db)
    course_params = parameters(course, trabajo.actividad_id, db)
    trabajo.estado = "cargado"
    db.commit()
    
    # 1. Semantic PDF extraction
    try:
        if trabajo.pdf_path and os.path.exists(trabajo.pdf_path):
            md_text = extract_pdf_to_markdown(trabajo.pdf_path)
            trabajo.markdown = md_text
            trabajo.estado = "cargado"
            db.commit()
    except Exception as e:
        trabajo.estado = "error"
        db.commit()
        raise HTTPException(422, str(e) if isinstance(e,ValueError) and 'OCR' in str(e) else "No se pudo extraer el PDF")

    if not (trabajo.markdown or "").strip():
        trabajo.estado = "error"
        db.commit()
        raise HTTPException(422, "El PDF no contiene texto extraíble")

    # Gather contextual materials (Syllabus, Rubric)
    materials = db.query(models.Material).filter(models.Material.asignatura_id == asignatura_id).all()
    syllabus_text = "\n\n".join(m.markdown for m in materials if m.tipo in ["syllabus", "guia"])
    rubric_text = "\n\n".join(m.markdown for m in materials if m.tipo == "rubrica")

    setup = configured_context(db, asignatura_id, trabajo.actividad_id)
    if course_params.get("requiere_rubrica") and not setup:
        trabajo.estado = "error"
        db.commit()
        raise HTTPException(422, "Guarda la rubrica de la evaluacion antes de analizar informes.")
    if setup:
        rubric_text_input = format_rubric(setup)
        rubric_text_full = rubric_text_input + "\n" + setup["rubrica_documento"]
        syllabus_text = f'Temas: {setup["temas"]}\nMaterial de clase:\n{setup["clase"]}\nMaterial del semestre:\n{setup["semestre"]}'
    else:
        rubric_text_full = rubric_text
    # 2. Run LLM / Mock evaluation (RF-007)
    anexo_a_data, nota_preliminar, pct_ia = await evaluate_submission_llm(
        markdown_content=trabajo.markdown or "",
        syllabus_content=syllabus_text,
        rubric_content=rubric_text_full,
        nivel_rigor=course_params.get("nivel_rigor", "medium"),
        umbral_ia=float(course_params.get("umbral_ia", 40.0)),
        umbral_coherencia=float(course_params.get("umbral_coherencia", 60.0)),
        prompt_custom=course_params.get("prompt_custom", "")
    )

    anexo_a_data["evaluacion_respuestas"] = {
        "nivel_rigor_aplicado": course_params.get("nivel_rigor", "medium"),
        "porcentaje_coherencia": "Pendiente", "respuestas_correctas": "0/0",
        "preguntas_falladas": [], "observacion_ia": "Verificación Flash aún no realizada",
        "requiere_defensa_oral": pct_ia >= float(course_params.get("umbral_ia", 40))
    }

    # Generate both outputs before replacing any previously reviewed evaluation.
    pool_size = int(course_params.get("pool_size", 15))
    num_selected = int(course_params.get("num_preguntas_test", 5))
    if setup:
        if len(setup["criterios"]) > num_selected:
            raise LLMUnavailable("Ajusta el numero de preguntas para cubrir todos los criterios.")
        anexo_a_data["rubrica_aplicada"] = {
            "version": setup["version"], "criterios": setup["criterios"], "temas": setup["temas"],
        }
        questions_data = await generate_rubric_pool(trabajo.markdown, syllabus_text, setup, num_selected, pool_size)
    else:
        questions_data = await generate_question_pool_llm(
            markdown_content=trabajo.markdown or "",
            syllabus_content=syllabus_text,
            pool_size=pool_size
        )

    # Replace evaluation and questions in one transaction, only after AI succeeds.
    if trabajo.evaluacion:
        db.delete(trabajo.evaluacion)
        db.flush()

    evaluacion = models.Evaluacion(
        trabajo_id=trabajo.id,
        nota=nota_preliminar,
        feedback=anexo_a_data.get("feedback", {}),
        pct_ia=pct_ia,
        desglose=anexo_a_data
    )
    db.add(evaluacion)
    db.flush()

    evaluacion.desglose = {**evaluacion.desglose, 'motor_preguntas': 'mock' if any(q.get('_motor') == 'mock' for q in questions_data) else settings.LLM_PROVIDER}
    for idx, q_dict in enumerate(questions_data):
        is_sel = q_dict.get("seleccionada", idx < num_selected)
        pregunta = models.Pregunta(
            evaluacion_id=evaluacion.id,
            texto=q_dict["texto"],
            alternativas=q_dict["alternativas"],
            seleccionada=is_sel,
            justificacion_respuesta=q_dict.get("justificacion_respuesta"),
            seccion_origen=q_dict.get("seccion_origen")
        )
        db.add(pregunta)

    trabajo.estado = "analizado"
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

async def generate_rubric_pool(markdown, context, setup, count, configured_size):
    from backend.app.config import settings
    criteria = setup["criterios"]
    quota, extra = divmod(max(configured_size, 3 * count), len(criteria))
    result = []
    selected, seen = [], set()
    for index, criterion in enumerate(criteria):
        target = quota + (index < extra)
        instruction = (
            f'Criterio obligatorio: {criterion["nombre"]}. {criterion["descripcion"]}. '
            'Incluye preguntas para explicar y justificar, y al menos una para aplicar el concepto '
            'a un caso nuevo parecido, con cambios concretos respecto del informe.'
        )
        for offset in range(0, target, 8):
            batch = min(8, target - offset)
            questions = await generate_question_pool_llm(markdown, context, batch, focus=instruction, exclude=sorted(seen))
            for batch_index, item in enumerate(questions, start=1):
                if settings.LLM_PROVIDER == "mock":
                    item["texto"] = f'{criterion["nombre"]} ({offset + batch_index}): {item["texto"]}'
                key = " ".join(item["texto"].casefold().split())
                if key in seen:
                    raise LLMUnavailable("El pool generado contiene preguntas repetidas. Reintenta el analisis.")
                seen.add(key)
                item["seccion_origen"] = criterion["nombre"]
                item["seleccionada"] = False
            if offset == 0:
                selected.append(questions[0])
            result.extend(questions)
    selected.extend([q for q in result if q not in selected][:count - len(selected)])
    for item in selected:
        item["seleccionada"] = True
    return result


@router.post("/api/asignaturas/{asignatura_id}/trabajos/upload")
async def upload_trabajo_single(
    asignatura_id: int,
    estudiante_id: int = Form(...),
    actividad_id: Optional[int] = Form(None),
    file: UploadFile = File(...),
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a single PDF for a specific student and trigger extraction & evaluation (RF-005, RF-006, RF-007)
    """
    check_course_access(asignatura_id, current_user, db, write=True)

    parameters(db.get(models.Asignatura, asignatura_id), actividad_id, db)
    assert_activity_open(asignatura_id, actividad_id, db)
    student = db.query(models.Estudiante).filter(
        models.Estudiante.id == estudiante_id,
        models.Estudiante.asignatura_id == asignatura_id
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado en esta asignatura")

    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo del trabajo debe estar en formato PDF")

    course_work_dir = settings.WORKS_DIR / f"course_{asignatura_id}"
    os.makedirs(course_work_dir, exist_ok=True)
    saved_path = course_work_dir / f"std_{estudiante_id}_{__import__('uuid').uuid4().hex}.pdf"

    assert_work_editable(estudiante_id, db, actividad_id)
    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    assert_work_editable(estudiante_id, db, actividad_id)
    # Check if student already has a trabajo
    trabajo = work_for(estudiante_id, actividad_id, db)
    if not trabajo:
        trabajo = models.Trabajo(
            estudiante_id=estudiante_id,
            actividad_id=actividad_id,
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
    actividad_id: Optional[int] = Form(None),
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Massive upload of student PDFs with automatic association by filename (RF-005)
    """
    check_course_access(asignatura_id, current_user, db, write=True)

    parameters(db.get(models.Asignatura, asignatura_id), actividad_id, db)
    assert_activity_open(asignatura_id, actividad_id, db)
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
        if not (file.filename or "").lower().endswith(".pdf"):
            unmatched.append({"file": file.filename, "reason": "No es archivo PDF"})
            continue

        matched_id = match_student_filename(file.filename, student_lookup)
        if not matched_id:
            unmatched.append({"file": file.filename, "reason": "No se pudo asociar a ningún estudiante por nombre/correo"})
            continue

        if db.query(models.FlashTest).filter_by(estudiante_id=matched_id, actividad_id=actividad_id).first():
            unmatched.append({"file": file.filename, "reason": "El estudiante ya tiene un test despachado"})
            continue
        saved_path = course_work_dir / f"std_{matched_id}_{__import__('uuid').uuid4().hex}.pdf"
        with open(saved_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        trabajo = work_for(matched_id, actividad_id, db)
        if not trabajo:
            trabajo = models.Trabajo(
                estudiante_id=matched_id,
                actividad_id=actividad_id,
                pdf_path=str(saved_path),
                estado="cargado"
            )
            db.add(trabajo)
        else:
            trabajo.pdf_path = str(saved_path)
            trabajo.estado = "cargado"

        db.commit()
        db.refresh(trabajo)

        try:
            await process_and_evaluate_trabajo(trabajo.id, asignatura_id, db, current_user.id)
            matched_count += 1
        except HTTPException as exc:
            unmatched.append({"file": file.filename, "reason": str(exc.detail)})

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
    actividad_id: Optional[int] = None,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve full evaluation details (Anexo A) for a student (RF-007)"""
    check_course_access(asignatura_id, current_user, db)

    student = db.query(models.Estudiante).filter_by(id=estudiante_id, asignatura_id=asignatura_id).first()
    if not student:
        raise HTTPException(404, "Estudiante no encontrado en esta asignatura")
    trabajo = work_for(student.id, actividad_id, db)
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


def assert_work_editable(student_id, db, actividad_id=None):
    if db.query(models.FlashTest).filter_by(estudiante_id=student_id, actividad_id=actividad_id).first():
        raise HTTPException(409, "No se puede reemplazar un informe con test despachado")
