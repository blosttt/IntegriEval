import csv
import io
import re
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app import models, schemas
from backend.app.auth import get_current_user, check_course_access
from backend.app.audit import log_audit

router = APIRouter(tags=["Estudiantes"])

@router.get("/api/asignaturas/{asignatura_id}/estudiantes", response_model=List[schemas.EstudianteOut])
def list_estudiantes(
    asignatura_id: int,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all students registered in a course (RF-002)"""
    check_course_access(asignatura_id, current_user, db)
    students = db.query(models.Estudiante).filter(models.Estudiante.asignatura_id == asignatura_id).all()
    
    result = []
    for s in students:
        has_work = s.trabajo is not None
        flash_test = db.query(models.FlashTest).filter(models.FlashTest.estudiante_id == s.id).order_by(models.FlashTest.id.desc()).first()
        result.append(
            schemas.EstudianteOut(
                id=s.id,
                nombre=s.nombre,
                correo=s.correo,
                rut=s.rut,
                asignatura_id=s.asignatura_id,
                fecha_creacion=s.fecha_creacion,
                tiene_trabajo=has_work,
                tiene_test=(flash_test is not None),
                estado_test=(flash_test.estado if flash_test else None),
                nota_final=(flash_test.nota_final_confirmada if flash_test else None)
            )
        )
    return result

@router.post("/api/asignaturas/{asignatura_id}/estudiantes/csv", response_model=schemas.CSVIngestionResult)
async def upload_csv_estudiantes(
    asignatura_id: int,
    file: UploadFile = File(...),
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ingest CSV of students with validation and duplicate detection (RF-002).
    Supported columns: nombre, correo / email, rut (opcional).
    Delimiters handled: comma (,) or semicolon (;).
    """
    course = check_course_access(asignatura_id, current_user, db)

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="El archivo subido debe ser un archivo de texto .csv")

    content_bytes = await file.read()
    try:
        content_text = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        content_text = content_bytes.decode("latin-1")

    # Detect delimiter
    sample = content_text[:1024]
    delimiter = ";" if ";" in sample and sample.count(";") > sample.count(",") else ","

    reader = csv.DictReader(io.StringIO(content_text), delimiter=delimiter)
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="El archivo CSV está vacío o sin encabezados válidos.")

    # Normalize header mapping
    header_map = {}
    for col in reader.fieldnames:
        col_clean = col.strip().lower()
        if "correo" in col_clean or "email" in col_clean or "mail" in col_clean:
            header_map["correo"] = col
        elif "nombre" in col_clean or "name" in col_clean or "alumno" in col_clean or "estudiante" in col_clean:
            header_map["nombre"] = col
        elif "rut" in col_clean or "id" in col_clean or "matricula" in col_clean or "rol" in col_clean:
            header_map["rut"] = col

    if "correo" not in header_map or "nombre" not in header_map:
        raise HTTPException(
            status_code=400,
            detail=f"El CSV debe contener al menos las columnas 'nombre' y 'correo'. Encontradas: {list(reader.fieldnames)}"
        )

    # Existing emails in this subject
    existing_emails = set(
        e[0].lower() for e in db.query(models.Estudiante.correo)
        .filter(models.Estudiante.asignatura_id == asignatura_id).all()
    )

    total_procesados = 0
    cargados_exitosamente = 0
    duplicados_omitidos = 0
    errores = []
    nuevos_estudiantes = []

    seen_in_batch = set()

    for idx, row in enumerate(reader, start=2):
        total_procesados += 1
        raw_name = row.get(header_map["nombre"], "").strip()
        raw_email = row.get(header_map["correo"], "").strip().lower()
        raw_rut = row.get(header_map.get("rut", ""), "").strip() if "rut" in header_map else None

        if not raw_name or not raw_email:
            errores.append(f"Fila {idx}: Faltan campos requeridos (nombre o correo).")
            continue

        # Basic email regex validation
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", raw_email):
            errores.append(f"Fila {idx}: Correo inválido '{raw_email}'.")
            continue

        if raw_email in existing_emails or raw_email in seen_in_batch:
            duplicados_omitidos += 1
            continue

        seen_in_batch.add(raw_email)
        student = models.Estudiante(
            nombre=raw_name,
            correo=raw_email,
            rut=raw_rut,
            asignatura_id=asignatura_id
        )
        db.add(student)
        nuevos_estudiantes.append(student)
        cargados_exitosamente += 1

    db.commit()

    # Refresh newly added
    for s in nuevos_estudiantes:
        db.refresh(s)

    log_audit(
        db=db,
        accion="CARGA_CSV_ESTUDIANTES",
        tabla="estudiantes",
        registro_id=course.id,
        usuario_id=current_user.id,
        datos_nuevos={
            "asignatura_id": asignatura_id,
            "procesados": total_procesados,
            "cargados": cargados_exitosamente,
            "duplicados": duplicados_omitidos
        }
    )

    out_students = [
        schemas.EstudianteOut(
            id=s.id,
            nombre=s.nombre,
            correo=s.correo,
            rut=s.rut,
            asignatura_id=s.asignatura_id,
            fecha_creacion=s.fecha_creacion,
            tiene_trabajo=False,
            tiene_test=False,
            estado_test=None,
            nota_final=None
        )
        for s in nuevos_estudiantes
    ]

    return schemas.CSVIngestionResult(
        total_procesados=total_procesados,
        cargados_exitosamente=cargados_exitosamente,
        duplicados_omitidos=duplicados_omitidos,
        errores=errores,
        estudiantes=out_students
    )
