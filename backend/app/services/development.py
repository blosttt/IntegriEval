from backend.app import models
from backend.app.activities import test_evaluation, parameters


def score_details(test, state, db):
    answers = test.respuestas or {}
    reviews = {review.pregunta_id: review for review in db.query(models.DevelopmentReview).filter_by(test_id=test.id)}
    points, correct, closed, pending, development, failed = 0.0, 0, 0, [], 0, []
    for question in state.preguntas:
        answer = answers.get(str(question['id']))
        if question.get('tipo', 'alternativas') == 'desarrollo':
            development += 1
            if not (answer or '').strip():
                failed.append(question['texto'][:80])
            elif question['id'] not in reviews:
                pending.append(question['id'])
            else:
                points += reviews[question['id']].puntaje
                if reviews[question['id']].puntaje < 100:
                    failed.append(question['texto'][:80])
        else:
            closed += 1
            expected = next((item['id'] for item in question['alternativas'] if item.get('es_correcta')), None)
            if expected is not None and answer == expected:
                points += 100
                correct += 1
            else:
                failed.append(question['texto'][:80])
    return {'puntaje': None if pending else round(points / max(1, len(state.preguntas)), 1),
            'respuestas_correctas': correct, 'preguntas_alternativas': closed,
            'preguntas_desarrollo': development, 'desarrollo_pendientes': len(pending),
            'revision_pendiente': bool(pending), 'falladas': failed}


def refresh_score(test, state, db):
    details = score_details(test, state, db)
    test.puntaje = details['puntaje']
    evaluation = test_evaluation(test, db)
    newer = db.query(models.FlashTest.id).filter(
        models.FlashTest.estudiante_id == test.estudiante_id,
        models.FlashTest.actividad_id == test.actividad_id,
        models.FlashTest.id > test.id,
    ).first()
    if evaluation and evaluation.desglose and not newer:
        params = parameters(test.estudiante.asignatura, test.actividad_id, db)
        pending = details['revision_pendiente']
        low = not pending and test.puntaje < float(params.get('umbral_coherencia', 60))
        evaluation.desglose = {**evaluation.desglose, 'evaluacion_respuestas': {
            'nivel_rigor_aplicado': params.get('nivel_rigor', 'medium'),
            'porcentaje_coherencia': 'Pendiente revisión docente' if pending else f'{test.puntaje:g}%',
            'respuestas_correctas': f"{details['respuestas_correctas']}/{details['preguntas_alternativas']}",
            'preguntas_falladas': details['falladas'],
            'observacion_ia': 'Respuestas de desarrollo pendientes de revisión docente.' if pending else
                ('Resultado Flash bajo el umbral; requiere revisión docente.' if low else 'Verificación Flash completada.'),
            'requiere_defensa_oral': low or evaluation.pct_ia >= float(params.get('umbral_ia', 40)),
            'desarrollo_pendientes': details['desarrollo_pendientes'],
        }}
    return details


def pending_review(test, db):
    if not test or test.estado != 'completado':
        return False
    state = db.get(models.FlashTestState, test.id)
    return bool(state and score_details(test, state, db)['revision_pendiente'])
