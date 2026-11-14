from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app import models
from backend.app.activities import assert_activity_open, lock_question_plan, parameters, test_evaluation
from backend.app.auth import check_course_access, get_current_user
from backend.app.config import settings
from backend.app.database import get_db
from backend.app.services.assessment import Findings, Setup, generate_report, transcript, weighted_score

router = APIRouter(tags=["Evaluacion por rubrica"])


@router.get("/api/asignaturas/{course_id}/preparacion-evaluacion")
def get_setup(course_id: int, actividad_id: int | None = None, user=Depends(get_current_user), db: Session = Depends(get_db)):
    parameters(check_course_access(course_id, user, db), actividad_id, db)
    setup = db.get(models.AssessmentSetup, (course_id, actividad_id or 0))
    return {"version": setup.version, **setup.contenido} if setup else None


@router.put("/api/asignaturas/{course_id}/preparacion-evaluacion")
def save_setup(course_id: int, data: Setup, actividad_id: int | None = None,
               user=Depends(get_current_user), db: Session = Depends(get_db)):
    course = check_course_access(course_id, user, db, write=True)
    lock_question_plan(course_id, db)
    params = parameters(course, actividad_id, db)
    assert_activity_open(course_id, actividad_id, db)
    for row in data.criterios:
        row.nombre = row.nombre.strip()
        row.descripcion = row.descripcion.strip()
    data.temas = data.temas.strip()
    if (not data.temas or any(not row.nombre or not row.descripcion for row in data.criterios)
            or sum(row.peso for row in data.criterios) != 100
            or len({row.nombre.casefold() for row in data.criterios}) != len(data.criterios)):
        raise HTTPException(422, "Indica temas y criterios distintos, con descripciones y pesos que sumen 100.")
    if len(data.criterios) > int(params.get("num_preguntas_test", 5)):
        raise HTTPException(422, "Configura al menos una pregunta por cada criterio de la rubrica.")
    ids = data.materiales_clase + data.materiales_semestre + ([data.rubrica_id] if data.rubrica_id else [])
    materials = {m.id: m for m in db.query(models.Material).filter_by(asignatura_id=course_id).filter(models.Material.id.in_(ids))}
    if len(ids) != len(materials) or (data.rubrica_id and materials[data.rubrica_id].tipo != "rubrica"):
        raise HTTPException(422, "Selecciona materiales distintos de este curso y un documento de tipo rubrica.")
    if any(materials[i].tipo == "rubrica" for i in data.materiales_clase + data.materiales_semestre):
        raise HTTPException(422, "Asigna las rubricas en su campo correspondiente.")
    setup = db.get(models.AssessmentSetup, (course_id, actividad_id or 0))
    if setup is None:
        setup = models.AssessmentSetup(asignatura_id=course_id, actividad_key=actividad_id or 0, version=0)
        db.add(setup)
    if setup.contenido != data.model_dump():
        setup.version += 1
        setup.contenido = data.model_dump()
    db.commit()
    return {"version": setup.version, **setup.contenido}


def review_context(test_id, user, db):
    test = db.get(models.FlashTest, test_id)
    if test is None:
        raise HTTPException(404, "Flash Test no encontrado.")
    check_course_access(test.estudiante.asignatura_id, user, db)
    state = db.get(models.FlashTestState, test_id)
    evaluation = test_evaluation(test, db)
    config = (evaluation.desglose or {}).get("rubrica_aplicada") if evaluation else None
    if test.estado != "completado" or not state:
        raise HTTPException(409, "El Flash Test debe estar completado y tener preguntas registradas.")
    return test, evaluation, config, transcript(test, state)


@router.get("/api/flash-tests/{test_id}/reporte-rubrica")
def get_report(test_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    test, evaluation, config, rows = review_context(test_id, user, db)
    review = db.get(models.AssessmentReview, test_id)
    teacher = review.docente if review else None
    run = db.get(models.CalibrationRun, test_id) if teacher else None
    return {"desempeno": {"informe": (evaluation.desglose or {}).get("porcentaje_logro") if evaluation else None,
                           "flash": test.puntaje}, "rubrica": config, "registro": rows, "informe": evaluation.trabajo.markdown if evaluation else None,
            "docente": teacher, "ia": review.ia if teacher else None,
            "ia_generada": bool(review and review.ia), "calibracion": run.resultado if run else None, "contraste": review.contraste if teacher else None}


@router.post("/api/flash-tests/{test_id}/reporte-rubrica/ia")
async def create_report(test_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    test, evaluation, config, rows = review_context(test_id, user, db)
    if not config:
        raise HTTPException(409, "Este informe no fue analizado con una rubrica configurada.")
    if settings.LLM_PROVIDER == "mock":
        raise HTTPException(409, "Activa Ollama para generar un reporte de IA.")
    existing = db.get(models.AssessmentReview, test_id)
    if existing and existing.ia:
        return {"generado": True}
    try:
        result = await generate_report(evaluation.trabajo, config["criterios"], rows)
    except Exception as exc:
        raise HTTPException(503, "Ollama no pudo completar el reporte. Revisa la conexion y reintenta.") from exc
    lock_question_plan(test.estudiante.asignatura_id, db)
    review = db.get(models.AssessmentReview, test_id)
    if review is None:
        review = models.AssessmentReview(test_id=test_id)
        db.add(review)
    if not review.ia:
        review.ia = {**result, "motor": settings.LLM_PROVIDER, "modelo": settings.LLM_MODEL}
    db.commit()
    return {"generado": True}


@router.put("/api/flash-tests/{test_id}/reporte-rubrica/docente")
def save_teacher_report(test_id: int, data: Findings, user=Depends(get_current_user), db: Session = Depends(get_db)):
    test, evaluation, config, rows = review_context(test_id, user, db)
    if not config:
        raise HTTPException(409, "Este informe no tiene rubrica registrada.")
    rubric = config["criterios"]
    names = {item["nombre"] for item in rubric}
    findings = data.model_dump()["criterios"]
    if len(findings) != len(names) or {item["criterio"] for item in findings} != names:
        raise HTTPException(422, "Evalua todos los criterios una vez.")
    for item in findings:
        quote = item["evidencia"].strip()
        question = next((row for row in rows if row["orden"] == item["pregunta"]), None)
        source = (evaluation.trabajo.markdown or "") if item["fuente"] == "informe" else question["respuesta"] if question and item["fuente"] == "respuesta" else ""
        if item["fuente"] == "sin_evidencia":
            item.update(puntaje=None, evidencia="", pregunta=None)
        elif not quote or quote not in source or item["puntaje"] is None:
            raise HTTPException(422, f'Cita un fragmento literal y asigna puntaje para {item["criterio"]}.')
    lock_question_plan(test.estudiante.asignatura_id, db)
    review = db.get(models.AssessmentReview, test_id)
    if review is None:
        review = models.AssessmentReview(test_id=test_id)
        db.add(review)
    if review.docente:
        raise HTTPException(409, "La revision independiente ya fue registrada.")
    review.docente = {"criterios": findings, "usuario_id": user.id, **weighted_score(findings, rubric)}
    db.commit()
    return {"guardado": True}


class Verdict(BaseModel):
    acuerdo: bool
    comentario: str = Field(min_length=1, max_length=3000)


@router.put("/api/flash-tests/{test_id}/reporte-rubrica/contraste")
def save_verdict(test_id: int, data: Verdict, user=Depends(get_current_user), db: Session = Depends(get_db)):
    test, _, _, _ = review_context(test_id, user, db)
    lock_question_plan(test.estudiante.asignatura_id, db)
    review = db.get(models.AssessmentReview, test_id)
    if not review or not review.docente or not review.ia:
        raise HTTPException(409, "Registra ambas evaluaciones antes de guardar el contraste.")
    if not data.comentario.strip():
        raise HTTPException(422, "Explica el motivo del veredicto.")
    review.contraste = {**data.model_dump(), "usuario_id": user.id}
    db.commit()
    return review.contraste
from io import BytesIO

from fastapi import Response
from backend.app.routers.preguntas import assert_editable
from backend.app.services.adaptive import Plan, compile_plan
from backend.app.services.assessment import Criterion


def allowed_evaluation(evaluation_id, user, db):
    evaluation = db.get(models.Evaluacion, evaluation_id)
    if not evaluation:
        raise HTTPException(404, "Informe no encontrado")
    check_course_access(evaluation.trabajo.estudiante.asignatura_id, user, db)
    return evaluation


@router.get("/api/evaluaciones/{evaluation_id}/repreguntas")
def get_plan(evaluation_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    allowed_evaluation(evaluation_id, user, db)
    plan = db.get(models.AdaptivePlan, evaluation_id)
    return plan.reglas if plan else []


class PlanWithSelection(Plan):
    seleccion: list[int] | None = Field(default=None, max_length=30)


@router.put("/api/evaluaciones/{evaluation_id}/repreguntas")
def save_plan(evaluation_id: int, data: PlanWithSelection, user=Depends(get_current_user), db: Session = Depends(get_db)):
    evaluation = allowed_evaluation(evaluation_id, user, db)
    assert_editable(evaluation, db)
    if data.seleccion is not None:
        selected = set(data.seleccion)
        if not selected or len(selected) != len(data.seleccion) or not selected <= {q.id for q in evaluation.preguntas}:
            raise HTTPException(422, "La selección contiene preguntas inválidas.")
        for question in evaluation.preguntas:
            question.seleccionada = question.id in selected
    rules = [item.model_dump() for item in data.reglas]
    compile_plan(evaluation, rules)
    plan = db.get(models.AdaptivePlan, evaluation_id)
    if plan:
        plan.reglas = rules
    else:
        db.add(models.AdaptivePlan(evaluacion_id=evaluation_id, reglas=rules))
    db.commit()
    return rules


class Template(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    criterios: list[Criterion] = Field(min_length=1, max_length=10)


@router.get("/api/asignaturas/{course_id}/plantillas-rubrica")
def list_templates(course_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    check_course_access(course_id, user, db)
    return [{"nombre": row.nombre, "criterios": row.criterios} for row in
            db.query(models.RubricTemplate).filter_by(asignatura_id=course_id).order_by(models.RubricTemplate.nombre)]


@router.post("/api/asignaturas/{course_id}/plantillas-rubrica", status_code=201)
def add_template(course_id: int, data: Template, user=Depends(get_current_user), db: Session = Depends(get_db)):
    check_course_access(course_id, user, db, write=True)
    lock_question_plan(course_id, db)
    name = data.nombre.strip()
    rows = [row.model_dump() for row in data.criterios]
    for row in rows:
        row["nombre"] = row["nombre"].strip()
        row["descripcion"] = row["descripcion"].strip()
    if (not name or any(not row["nombre"] or not row["descripcion"] for row in rows)
            or sum(row["peso"] for row in rows) != 100
            or len({row["nombre"].casefold() for row in rows}) != len(rows)):
        raise HTTPException(422, "La plantilla requiere criterios distintos, descripciones y pesos que sumen 100.")
    if db.query(models.RubricTemplate).filter_by(asignatura_id=course_id, nombre=name).first():
        raise HTTPException(409, "Ya existe una plantilla con ese nombre.")
    db.add(models.RubricTemplate(asignatura_id=course_id, nombre=name, criterios=rows))
    db.commit()
    return {"nombre": name, "criterios": rows}


@router.get("/api/flash-tests/{test_id}/reporte-rubrica/pdf")
def download_report(test_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    from html import escape
    import pymupdf

    test, evaluation, config, rows = review_context(test_id, user, db)
    review = db.get(models.AssessmentReview, test_id)
    def paragraph(value):
        return f"<p>{escape(str(value)).replace(chr(10), '<br>')}</p>"
    html = "<h1>IntegryEval - Informe individual</h1>" + paragraph(test.estudiante.nombre)
    if evaluation:
        html += paragraph(f'Informe del proyecto: {(evaluation.desglose or {}).get("porcentaje_logro", "Sin puntaje")}')
    html += paragraph(f"Flash Test: {test.puntaje if test.puntaje is not None else 'pendiente de revisión'}")
    if config:
        html += paragraph(f'Rúbrica, versión {config["version"]} · {config["temas"]}')
        for criterion in config["criterios"]:
            html += paragraph(f'{criterion["nombre"]} ({criterion["peso"]}%): {criterion["descripcion"]}')
    html += "<h2>Preguntas y respuestas</h2>"
    for row in rows:
        html += paragraph(f'{row["orden"]}. {row["pregunta"]}')
        html += paragraph(row["respuesta"] or "Sin respuesta")
        if row["rama"]:
            html += paragraph(f'Pregunta {row["depende_de"]} → {row["rama"].replace("_", " ")}')
    if review and review.docente:
        for title, result in (("Evaluación docente", review.docente), ("Evaluación de IA", review.ia)):
            if not result:
                continue
            html += f"<h2>{title}</h2>" + paragraph(f'Puntaje: {result["puntaje"]} · Cobertura: {result["cobertura"]}%')
            for row in result["criterios"]:
                html += paragraph(f'{row["criterio"]} · {row["puntaje"] if row["puntaje"] is not None else "Sin evidencia"} · {row["observacion"]}')
                for key in ("evidencia", "entrevista"):
                    if row[key]:
                        html += paragraph(row[key])
        if review.contraste:
            html += "<h2>Contraste docente</h2>" + paragraph("De acuerdo" if review.contraste["acuerdo"] else "En desacuerdo")
            html += paragraph(review.contraste["comentario"])
    buffer = BytesIO()
    writer = pymupdf.DocumentWriter(buffer)
    story = pymupdf.Story(html=html, user_css="body{font-family:sans-serif;font-size:10pt} p{margin:0 0 7pt}")
    page = pymupdf.paper_rect("a4")
    more = True
    while more:
        device = writer.begin_page(page)
        more, _ = story.place(page + (44, 44, -44, -44))
        story.draw(device)
        writer.end_page()
    writer.close()
    return Response(buffer.getvalue(), media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="integryeval-informe-{test_id}.pdf"'})


@router.post("/api/flash-tests/{test_id}/reporte-rubrica/calibrar")
async def calibrate(test_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    test, evaluation, config, rows = review_context(test_id, user, db)
    review = db.get(models.AssessmentReview, test_id)
    if not config or not review or not review.ia or not review.docente or not review.contraste:
        raise HTTPException(409, "Completa ambas evaluaciones y el contraste antes de recalibrar.")
    if settings.LLM_PROVIDER == "mock":
        raise HTTPException(409, "Activa Ollama para recalibrar.")
    try:
        result = await generate_report(evaluation.trabajo, config["criterios"], rows, guidance={
            "revision_docente": review.docente["criterios"], "contraste": review.contraste["comentario"],
        })
    except Exception as exc:
        raise HTTPException(503, "Ollama no pudo recalibrar el reporte.") from exc
    reference = {row["criterio"]: row["puntaje"] for row in review.docente["criterios"]}
    def compare(report):
        paired = [(row["puntaje"], reference[row["criterio"]]) for row in report["criterios"]
                  if row["puntaje"] is not None and reference[row["criterio"]] is not None]
        return {"criterios_comparables": len(paired),
                "error_medio": round(sum(abs(a - b) for a, b in paired) / len(paired), 1) if paired else None}
    payload = {**result, "antes": compare(review.ia), "despues": compare(result)}
    lock_question_plan(test.estudiante.asignatura_id, db)
    run = db.get(models.CalibrationRun, test_id)
    if run:
        run.resultado = payload
    else:
        db.add(models.CalibrationRun(test_id=test_id, resultado=payload))
    db.commit()
    return payload
