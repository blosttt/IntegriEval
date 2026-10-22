"""Evaluation scopes. NULL preserves the original course evaluation and its history."""
from fastapi import HTTPException
from backend.app import models


def parameters(course, activity_id, db):
    if activity_id is None:
        return course.parametros or {}
    activity = db.get(models.Actividad, activity_id)
    if not activity or activity.asignatura_id != course.id:
        raise HTTPException(404, "Evaluación no encontrada en esta asignatura")
    return activity.parametros


def work_for(student_id, activity_id, db):
    return db.query(models.Trabajo).filter_by(estudiante_id=student_id, actividad_id=activity_id).first()


def test_evaluation(test, db):
    work = work_for(test.estudiante_id, test.actividad_id, db)
    return work.evaluacion if work else None


def assert_activity_open(course_id, activity_id, db):
    status = db.get(models.ActivityStatus, (course_id, activity_id or 0))
    if status and status.estado != "abierta":
        raise HTTPException(409, "La evaluación está cerrada o archivada. Reábrela antes de modificarla.")
