import os
import shutil
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app import models, schemas
from backend.app.config import settings
from backend.app.auth import get_current_user, check_course_access
from backend.app.services.pdf_service import extract_pdf_to_markdown
from backend.app.audit import log_audit

router = APIRouter(tags=["Materiales"])

@router.get("/api/asignaturas/{asignatura_id}/materiales", response_model=List[schemas.MaterialOut])
def list_materiales(
    asignatura_id: int,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all contextual materials uploaded for a course (RF-004)"""
    check_course_access(asignatura_id, current_user, db)
    return db.query(models.Material).filter(models.Material.asignatura_id == asignatura_id).all()

@router.post("/api/asignaturas/{asignatura_id}/materiales", response_model=schemas.MaterialOut)
async def upload_material(
    asignatura_id: int,
    nombre: str = Form(...),
    tipo: str = Form("syllabus"),  # syllabus, rubrica, guia, otro
    file: UploadFile = File(...),
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload course support material (Syllabus, Rubric, Guide) and convert to Markdown for LLM prompt injection (RF-004)
    """
    check_course_access(asignatura_id, current_user, db)

    file_ext = os.path.splitext(file.filename)[1].lower()
    allowed_exts = [".pdf", ".md", ".txt", ".markdown"]
    if file_ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Formato no soportado ({file_ext}). Utilice .pdf, .md o .txt"
        )

    # Save file to disk
    course_mat_dir = settings.MATERIALS_DIR / f"course_{asignatura_id}"
    os.makedirs(course_mat_dir, exist_ok=True)
    saved_path = course_mat_dir / f"{tipo}_{file.filename}"

    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Extract to markdown
    if file_ext == ".pdf":
        try:
            markdown_content = extract_pdf_to_markdown(str(saved_path))
        except Exception as e:
            markdown_content = f"# {nombre}\n\nError extrayendo PDF estructurado: {e}"
    else:
        with open(saved_path, "r", encoding="utf-8", errors="replace") as f:
            markdown_content = f.read()

    material = models.Material(
        asignatura_id=asignatura_id,
        nombre=nombre,
        tipo=tipo,
        file_path=str(saved_path),
        markdown=markdown_content
    )
    db.add(material)
    db.commit()
    db.refresh(material)

    log_audit(
        db=db,
        accion="SUBIR_MATERIAL",
        tabla="materiales",
        registro_id=material.id,
        usuario_id=current_user.id,
        datos_nuevos={"nombre": material.nombre, "tipo": material.tipo}
    )

    return material
