"""Plan and apply pre-reviewed follow-ups without waiting for a model during the test."""
from fastapi import HTTPException
from pydantic import BaseModel, Field

from backend.app import models


class Branch(BaseModel):
    base: int
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
        base, help_question = (questions.get(rule[key]) for key in ("base", "error"))
        if not base or not help_question or base.id not in order or base.tipo != "alternativas":
            raise HTTPException(422, "La pregunta base debe estar seleccionada y ser de alternativas.")
        index = order.index(base.id)
        if index + 1 >= len(order) or occupied.intersection({index, index + 1}):
            raise HTTPException(422, "Cada pregunta base necesita un espacio siguiente sin otra regla.")
        slot = questions[order[index + 1]]
        if (help_question.seleccionada
                or help_question.texto.strip().casefold() in {base.texto.strip().casefold(), slot.texto.strip().casefold()}
                or help_question.seccion_origen != slot.seccion_origen or help_question.tipo != slot.tipo
                or help_question.seccion_origen != base.seccion_origen):
            raise HTTPException(422, "Usa una repregunta distinta y sin seleccionar, del criterio de la pregunta base y del mismo tipo y criterio que la siguiente.")
        occupied.update({index, index + 1})
        result[str(index)] = {"error": snapshot(help_question)}
    return result


def advance_branch(test, state, db, answer):
    adaptive = db.get(models.AdaptiveSession, test.id)
    if not adaptive or str(state.indice) not in adaptive.reglas:
        return
    branches = adaptive.reglas[str(state.indice)]
    current = state.preguntas[state.indice]
    correct = any(option["id"] == answer and option["es_correcta"] for option in current["alternativas"])
    if correct:
        return
    reason = "sin_respuesta" if answer is None else "error"
    next_index = state.indice + 1
    followup = branches["error"]
    state.preguntas = [
        *state.preguntas[:next_index],
        {**followup, "rama": reason, "depende_de": state.indice + 1},
        *state.preguntas[next_index + 1:],
    ]
