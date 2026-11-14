from random import SystemRandom
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from backend.app import models, schemas
from backend.app.activities import assert_activity_open, lock_question_plan, parameters
from backend.app.auth import check_course_access, get_current_user
from backend.app.database import get_db

router = APIRouter(prefix="/api/asignaturas/{course_id}/pool-general", tags=["Pool general"])


def scoped_questions(db, course_id, activity_id):
    return db.query(models.GeneralQuestion).filter_by(asignatura_id=course_id, actividad_key=activity_id or 0)


def authorize(course_id, activity_id, user, db, write=False):
    course = check_course_access(course_id, user, db, write=write)
    if write:
        lock_question_plan(course_id, db)
        assert_activity_open(course_id, activity_id, db)
    return parameters(course, activity_id, db)


def content(data):
    return data.model_dump(exclude={"seleccionada"})


@router.get("")
def list_questions(course_id: int, actividad_id: int | None = None, user=Depends(get_current_user), db: Session = Depends(get_db)):
    authorize(course_id, actividad_id, user, db)
    return [{"id": q.id, **q.contenido} for q in scoped_questions(db, course_id, actividad_id).order_by(models.GeneralQuestion.id)]


@router.post("", status_code=201)
def add_question(course_id: int, data: schemas.PreguntaCreate, actividad_id: int | None = None, user=Depends(get_current_user), db: Session = Depends(get_db)):
    authorize(course_id, actividad_id, user, db, write=True)
    question = models.GeneralQuestion(asignatura_id=course_id, actividad_key=actividad_id or 0, contenido=content(data))
    db.add(question)
    db.commit()
    return {"id": question.id, **question.contenido}


@router.put("/{question_id:int}")
def edit_question(course_id: int, question_id: int, data: schemas.PreguntaCreate, actividad_id: int | None = None, user=Depends(get_current_user), db: Session = Depends(get_db)):
    authorize(course_id, actividad_id, user, db, write=True)
    question = scoped_questions(db, course_id, actividad_id).filter_by(id=question_id).first()
    if question is None:
        raise HTTPException(404, "Pregunta general no encontrada")
    question.contenido = content(data)
    db.commit()
    return {"id": question.id, **question.contenido}


@router.delete("/{question_id:int}", status_code=204)
def delete_question(course_id: int, question_id: int, actividad_id: int | None = None, user=Depends(get_current_user), db: Session = Depends(get_db)):
    authorize(course_id, actividad_id, user, db, write=True)
    question = scoped_questions(db, course_id, actividad_id).filter_by(id=question_id).first()
    if question is None:
        raise HTTPException(404, "Pregunta general no encontrada")
    db.delete(question)
    db.commit()


def student_records(db, course_id, activity_id):
    students = db.query(models.Estudiante).filter_by(asignatura_id=course_id)
    student_ids = students.with_entities(models.Estudiante.id)
    works = (db.query(models.Trabajo).filter(models.Trabajo.estudiante_id.in_(student_ids), models.Trabajo.actividad_id == activity_id)
             .options(selectinload(models.Trabajo.evaluacion).selectinload(models.Evaluacion.preguntas)).order_by(models.Trabajo.id))
    tests = (db.query(models.FlashTest).filter(models.FlashTest.estudiante_id.in_(student_ids), models.FlashTest.actividad_id == activity_id)
             .order_by(models.FlashTest.id.desc()))
    return students.order_by(models.Estudiante.nombre, models.Estudiante.id), works, tests


def question_key(question):
    return " ".join(question["texto"].casefold().split())


def draw_questions(general, individual, count, source, rng, required=()):
    general = list(general) if source != "individual" else []
    individual = list(individual) if source != "general" else []
    rng.shuffle(general)
    rng.shuffle(individual)
    chosen = []
    seen = set()

    def take(candidates):
        for is_general, question in candidates:
            key = question_key(question)
            if key in seen:
                continue
            seen.add(key)
            chosen.append((is_general, question))
            if len(chosen) == count:
                return

    if required:
        candidates = [(True, q) for q in general] + [(False, q) for q in individual]
        rng.shuffle(candidates)
        for criterion in required:
            matches = [(shared, q) for shared, q in candidates if q.get("seccion_origen") == criterion]
            before = len(chosen)
            candidate = next(((shared, q) for shared, q in matches if question_key(q) not in seen), None)
            if candidate:
                take([candidate])
            if len(chosen) == before:
                return []
    if not required and source == "mixto" and count > 1 and general and individual:
        general_index = next((i for i, q in enumerate(general) if question_key(q) != question_key(individual[-1])), None)
        if general_index is not None:
            take([(True, general.pop(general_index)), (False, individual.pop())])
        else:
            individual_index = next((i for i, q in enumerate(individual) if question_key(q) != question_key(general[-1])), None)
            if individual_index is not None:
                take([(True, general.pop()), (False, individual.pop(individual_index))])
    if len(chosen) < count:
        remaining = [(True, q) for q in general] + [(False, q) for q in individual]
        rng.shuffle(remaining)
        take(remaining)
    return chosen


@router.post("/sortear")
def randomize(course_id: int, fuente: Literal["mixto", "general", "individual"] = "mixto",
              actividad_id: int | None = None, user=Depends(get_current_user), db: Session = Depends(get_db)):
    params = authorize(course_id, actividad_id, user, db, write=True)
    count = int(params.get("num_preguntas_test", 5))
    if count < 1:
        raise HTTPException(422, "Configura una cantidad de preguntas mayor que cero")
    general = [q.contenido for q in scoped_questions(db, course_id, actividad_id)]
    if fuente == "general" and not general:
        raise HTTPException(422, "Agrega preguntas al pool general antes de sortear")
    students, works, tests = student_records(db, course_id, actividad_id)
    issued = {test.estudiante_id for test in tests}
    inactive = {student_id for (student_id,) in db.query(models.StudentStatus.estudiante_id).filter_by(active=False)}
    work_by_student = {work.estudiante_id: work for work in works}
    rng = SystemRandom()
    assigned, skipped = 0, []
    for student in students:
        if student.id in issued or student.id in inactive:
            continue
        work = work_by_student.get(student.id)
        if not work or work.estado != "analizado" or not work.evaluacion:
            skipped.append({"estudiante": student.nombre, "motivo": "Informe sin análisis"})
            continue
        evaluation = work.evaluacion
        personal = [q for q in evaluation.preguntas if not q.pool_general]
        rubric = (evaluation.desglose or {}).get("rubrica_aplicada", {})
        required = [row["nombre"] for row in rubric.get("criterios", [])]
        individual = [{"id": q.id, "texto": q.texto, "seccion_origen": q.seccion_origen} for q in personal]
        chosen = draw_questions(general, individual, count, fuente, rng, required) if len(required) <= count else []
        if len(chosen) != count:
            skipped.append({"estudiante": student.nombre, "motivo": ("Faltan preguntas distintas o cobertura de la rubrica" if required else f"Solo hay {len(chosen)} preguntas distintas de las {count} requeridas")})
            continue
        selected_ids = {q["id"] for shared, q in chosen if not shared}
        for question in evaluation.preguntas:
            if question.pool_general:
                db.delete(question)
            else:
                question.seleccionada = question.id in selected_ids
        for shared, question in chosen:
            if shared:
                db.add(models.Pregunta(evaluacion_id=evaluation.id, seleccionada=True, pool_general=True, **question))
        assigned += 1
    if assigned:
        db.add(models.AuditLog(usuario_id=user.id, accion="SORTEAR_POOL_GENERAL", tabla="asignaturas", registro_id=course_id,
                              datos_nuevos={"actividad_id": actividad_id, "fuente": fuente, "asignados": assigned}))
    db.commit()
    return {"asignados": assigned, "omitidos": skipped, "ya_despachados": len(issued)}


@router.get("/asignaciones")
def assignments(course_id: int, actividad_id: int | None = None, user=Depends(get_current_user), db: Session = Depends(get_db)):
    authorize(course_id, actividad_id, user, db)
    students, works, tests = student_records(db, course_id, actividad_id)
    work_by_student = {work.estudiante_id: work for work in works}
    tests = tests.all()
    states = {state.test_id: state for state in db.query(models.FlashTestState)
              .filter(models.FlashTestState.test_id.in_([test.id for test in tests]))}
    attempts = {}
    for test in tests:
        state = states.get(test.id)
        attempts.setdefault(test.estudiante_id, []).append({
            "id": test.id, "estado": test.estado,
            "preguntas": [{"texto": q["texto"], "tipo": q.get("tipo", "alternativas"), "pool_general": q.get("pool_general", False)}
                          for q in state.preguntas] if state else None,
        })
    result = []
    for student in students:
        work = work_by_student.get(student.id)
        sent = attempts.get(student.id, [])
        draft = [{"texto": q.texto, "tipo": q.tipo, "pool_general": q.pool_general}
                 for q in work.evaluacion.preguntas if q.seleccionada] if work and work.evaluacion and not sent else []
        if sent or draft:
            result.append({"estudiante_id": student.id, "estudiante": student.nombre, "intentos": sent, "seleccion": draft})
    return result
