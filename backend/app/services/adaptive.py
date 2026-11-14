"""Plan and apply pre-reviewed follow-ups without waiting for a model during the test."""
from fastapi import HTTPException
from pydantic import BaseModel, Field

from backend.app import models


class Branch(BaseModel):
    base: int
    acierto: int
    error: int


class Plan(BaseModel):
    reglas: list[Branch] = Field(max_length=7)


def snapshot(q):
    return {"id": q.id, "texto": q.texto, "alternativas": q.alternativas, "tipo": q.tipo,
            "pool_general": q.pool_general, "respuesta_referencia": q.respuesta_referencia,
            "criterios_evaluacion": q.criterios_evaluacion, "seccion_origen": q.seccion_origen}


def compile_plan(evaluation, rules):
    questions = {q.id: q for q in evaluation.preguntas}
    order = [q.id for q in evaluation.preguntas if q.seleccionada]
    occupied = set()
    result = {}
    for rule in rules:
        base, correct, incorrect = (questions.get(rule[key]) for key in ("base", "acierto", "error"))
        if not all((base, correct, incorrect)) or base.id not in order or base.tipo != "alternativas":
            raise HTTPException(422, "La pregunta base debe estar seleccionada y ser de alternativas.")
        index = order.index(base.id)
        if index + 1 >= len(order) or occupied.intersection({index, index + 1}):
            raise HTTPException(422, "Cada pregunta base necesita un espacio siguiente sin otra regla.")
        slot = questions[order[index + 1]]
        if (correct.id == incorrect.id or correct.seleccionada or incorrect.seleccionada
                or len({slot.texto.strip().casefold(), correct.texto.strip().casefold(), incorrect.texto.strip().casefold()}) != 3
                or any(q.seccion_origen != slot.seccion_origen or q.tipo != slot.tipo for q in (correct, incorrect))):
            raise HTTPException(422, "Usa dos repreguntas distintas sin seleccionar, del mismo tipo y criterio que el espacio siguiente.")
        occupied.update({index, index + 1})
        result[str(index)] = {"acierto": snapshot(correct), "error": snapshot(incorrect)}
    return result


def advance_branch(test, state, db, answer):
    adaptive = db.get(models.AdaptiveSession, test.id)
    if not adaptive or str(state.indice) not in adaptive.reglas:
        return
    branches = adaptive.reglas[str(state.indice)]
    current = state.preguntas[state.indice]
    correct = any(option["id"] == answer and option["es_correcta"] for option in current["alternativas"])
    reason = "sin_respuesta" if not answer else "acierto" if correct else "error"
    next_index = state.indice + 1
    followup = branches.get(reason, state.preguntas[next_index])
    state.preguntas = [
        *state.preguntas[:next_index],
        {**followup, "rama": reason, "depende_de": state.indice + 1},
        *state.preguntas[next_index + 1:],
    ]
