from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.app import models, schemas
from backend.app.auth import get_current_user, check_course_access
from backend.app.database import get_db
from backend.app.activities import parameters, assert_activity_open
from backend.app.audit import log_audit

router = APIRouter(tags=["Evaluaciones de asignatura"])

class ActivityData(BaseModel):
    titulo: str = Field(min_length=1, max_length=150)
    parametros: schemas.ParametrosConfig

@router.get('/api/asignaturas/{course_id}/actividades')
def list_activities(course_id: int, user=Depends(get_current_user), db: Session=Depends(get_db)):
    course = check_course_access(course_id, user, db)
    result = [{"id":0,"asignatura_id":course.id,"titulo":(course.parametros or {}).get("titulo_evaluacion", "Evaluación de informes"),"parametros":course.parametros}] + [{"id":a.id,"asignatura_id":course.id,"titulo":a.titulo,"parametros":a.parametros} for a in db.query(models.Actividad).filter_by(asignatura_id=course.id).order_by(models.Actividad.id).all()]

    for item in result:
        state=db.get(models.ActivityStatus,(course.id,item['id']))
        item['estado']=state.estado if state else 'abierta'
    return result

@router.post('/api/asignaturas/{course_id}/actividades')
def create_activity(course_id: int, data: ActivityData, user=Depends(get_current_user), db: Session=Depends(get_db)):
    check_course_access(course_id,user,db,write=True)
    activity=models.Actividad(asignatura_id=course_id,titulo=data.titulo,parametros=data.parametros.model_dump())
    db.add(activity); db.commit(); db.refresh(activity)
    log_audit(db,"CREAR_EVALUACION","actividades",activity.id,user.id,datos_nuevos={"titulo":activity.titulo})
    return {"id":activity.id,"asignatura_id":course_id,"titulo":activity.titulo,"parametros":activity.parametros}

@router.put('/api/asignaturas/{course_id}/actividades/{activity_id}')
def update_activity(course_id: int, activity_id: int, data: ActivityData, user=Depends(get_current_user), db: Session=Depends(get_db)):
    course=check_course_access(course_id,user,db,write=True)
    parameters(course, activity_id or None, db)
    assert_activity_open(course_id, activity_id or None, db)
    if activity_id:
        activity=db.get(models.Actividad,activity_id)
        activity.titulo=data.titulo; activity.parametros=data.parametros.model_dump()
    else:
        course.parametros={**data.parametros.model_dump(),"titulo_evaluacion":data.titulo}
    db.commit()
    log_audit(db,"EDITAR_EVALUACION","asignaturas",course_id,user.id,datos_nuevos={"actividad_id":activity_id,"titulo":data.titulo})
    return {"id":activity_id,"asignatura_id":course_id,"titulo":data.titulo,"parametros":data.parametros.model_dump()}
