from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app import models, schemas
from backend.app.auth import get_current_user, check_course_access
from backend.app.audit import log_audit

router = APIRouter(prefix="/api/asignaturas", tags=["Asignaturas"])

@router.get("", response_model=List[schemas.AsignaturaOut])
def get_user_asignaturas(
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all courses belonging to the authenticated teacher (RF-001)"""
    if current_user.rol == "admin":
        courses = db.query(models.Asignatura).all()
    else:
        courses = db.query(models.Asignatura).filter(models.Asignatura.docente_id == current_user.id).all()

    result = []
    for c in courses:
        total_std = db.query(models.Estudiante).filter(models.Estudiante.asignatura_id == c.id).count()
        result.append(
            schemas.AsignaturaOut(
                id=c.id,
                nombre=c.nombre,
                periodo=c.periodo,
                ano=c.ano,
                docente_id=c.docente_id,
                parametros=c.parametros or {},
                fecha_creacion=c.fecha_creacion,
                total_estudiantes=total_std
            )
        )
    return result

@router.post("", response_model=schemas.AsignaturaOut)
def create_asignatura(
    data: schemas.AsignaturaCreate,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new course (RF-001)"""
    default_params = {
        "prompt_custom": "",
        "nivel_rigor": "medium",
        "pool_size": 15,
        "num_preguntas_test": 5,
        "umbral_ia": 40.0,
        "umbral_coherencia": 60.0,
        "tiempo_test_segundos": 60
    }
    if data.parametros:
        default_params.update(data.parametros.model_dump())

    new_course = models.Asignatura(
        nombre=data.nombre,
        periodo=data.periodo,
        ano=data.ano,
        docente_id=current_user.id,
        parametros=default_params
    )
    db.add(new_course)
    db.commit()
    db.refresh(new_course)

    log_audit(
        db=db,
        accion="CREAR_ASIGNATURA",
        tabla="asignaturas",
        registro_id=new_course.id,
        usuario_id=current_user.id,
        datos_nuevos={"nombre": new_course.nombre, "periodo": new_course.periodo, "ano": new_course.ano}
    )

    return schemas.AsignaturaOut(
        id=new_course.id,
        nombre=new_course.nombre,
        periodo=new_course.periodo,
        ano=new_course.ano,
        docente_id=new_course.docente_id,
        parametros=new_course.parametros,
        fecha_creacion=new_course.fecha_creacion,
        total_estudiantes=0
    )

@router.get("/{asignatura_id}", response_model=schemas.AsignaturaOut)
def get_asignatura(
    asignatura_id: int,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get single course details with RBAC check (RNF-006)"""
    course = check_course_access(asignatura_id, current_user, db)
    total_std = db.query(models.Estudiante).filter(models.Estudiante.asignatura_id == course.id).count()
    return schemas.AsignaturaOut(
        id=course.id,
        nombre=course.nombre,
        periodo=course.periodo,
        ano=course.ano,
        docente_id=course.docente_id,
        parametros=course.parametros or {},
        fecha_creacion=course.fecha_creacion,
        total_estudiantes=total_std
    )

@router.put("/{asignatura_id}", response_model=schemas.AsignaturaOut)
def update_asignatura(
    asignatura_id: int,
    data: schemas.AsignaturaUpdate,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update course and evaluation parameters (RF-003, RN-003)"""
    course = check_course_access(asignatura_id, current_user, db)
    datos_previos = {
        "nombre": course.nombre,
        "periodo": course.periodo,
        "ano": course.ano,
        "parametros": course.parametros
    }

    if data.nombre is not None:
        course.nombre = data.nombre
    if data.periodo is not None:
        course.periodo = data.periodo
    if data.ano is not None:
        course.ano = data.ano
    if data.parametros is not None:
        current_p = dict(course.parametros or {})
        current_p.update(data.parametros.model_dump())
        course.parametros = current_p

    db.commit()
    db.refresh(course)

    log_audit(
        db=db,
        accion="ACTUALIZAR_PARAMETROS_ASIGNATURA",
        tabla="asignaturas",
        registro_id=course.id,
        usuario_id=current_user.id,
        datos_previos=datos_previos,
        datos_nuevos={"nombre": course.nombre, "parametros": course.parametros}
    )

    total_std = db.query(models.Estudiante).filter(models.Estudiante.asignatura_id == course.id).count()
    return schemas.AsignaturaOut(
        id=course.id,
        nombre=course.nombre,
        periodo=course.periodo,
        ano=course.ano,
        docente_id=course.docente_id,
        parametros=course.parametros or {},
        fecha_creacion=course.fecha_creacion,
        total_estudiantes=total_std
    )
