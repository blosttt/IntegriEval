"""
Course materials API.
Professors upload PDFs/DOCX as knowledge base for AI analysis and question generation.
"""
import os
import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import require_teacher
from app.models.models import CourseMaterial, Evaluation, Course, User
from app.schemas.schemas import CourseMaterialResponse
from app.services.extractor import extract_to_markdown
from app.services.audit import log_event

router = APIRouter(prefix="/evaluations", tags=["materials"])

MATERIALS_DIR = "./uploads/materials"
os.makedirs(MATERIALS_DIR, exist_ok=True)


def _get_evaluation_for_teacher(eval_id: int, current_user: User, db: Session) -> Evaluation:
    evaluation = db.query(Evaluation).filter(Evaluation.id == eval_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")
    if current_user.role == "teacher" and evaluation.course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="No eres el docente de esta evaluación")
    return evaluation


@router.get("/{eval_id}/materials", response_model=List[CourseMaterialResponse])
def list_materials(
    eval_id: int,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """List all course materials for an evaluation."""
    _get_evaluation_for_teacher(eval_id, current_user, db)
    return db.query(CourseMaterial).filter(CourseMaterial.evaluation_id == eval_id).all()


@router.post("/{eval_id}/materials", response_model=CourseMaterialResponse, status_code=status.HTTP_201_CREATED)
async def upload_material(
    eval_id: int,
    title: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """
    Upload a PDF or DOCX as course material.
    The file is converted to Markdown and stored as context for AI analysis.
    Max size: 20MB.
    """
    _get_evaluation_for_teacher(eval_id, current_user, db)

    filename = file.filename or "material"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".pdf", ".docx", ".doc"]:
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF o Word (.docx)")

    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > 20.0:
        raise HTTPException(
            status_code=400,
            detail=f"El archivo excede el límite de 20MB (tamaño: {size_mb:.1f}MB)"
        )

    # Save file
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_name = f"eval_{eval_id}_{timestamp}{ext}"
    dest_path = os.path.join(MATERIALS_DIR, safe_name)

    with open(dest_path, "wb") as f:
        f.write(contents)

    # Extract to Markdown for AI context
    try:
        markdown_content = extract_to_markdown(dest_path)
    except Exception as e:
        markdown_content = ""
        print(f"[materials] Warning: could not extract markdown from material: {e}")

    material = CourseMaterial(
        evaluation_id=eval_id,
        title=title,
        file_path=dest_path,
        markdown_content=markdown_content,
    )
    db.add(material)
    db.commit()
    db.refresh(material)

    log_event(db, user_id=current_user.id, action="upload_material",
              entity="course_material", entity_id=str(material.id),
              details={"title": title, "filename": filename, "size_mb": round(size_mb, 2)})

    return material


@router.delete("/{eval_id}/materials/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_material(
    eval_id: int,
    material_id: int,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """Delete a course material."""
    _get_evaluation_for_teacher(eval_id, current_user, db)

    material = db.query(CourseMaterial).filter(
        CourseMaterial.id == material_id,
        CourseMaterial.evaluation_id == eval_id,
    ).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material no encontrado")

    if os.path.exists(material.file_path):
        try:
            os.remove(material.file_path)
        except Exception:
            pass

    db.delete(material)
    db.commit()

    log_event(db, user_id=current_user.id, action="delete_material",
              entity="course_material", entity_id=str(material_id), details={})
