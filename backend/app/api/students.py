"""
Student management API.
Students do NOT have accounts — they are managed by teachers/admins.
"""
import csv
import io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import require_teacher, require_staff
from app.models.models import Student, Course, User
from app.schemas.schemas import StudentCreate, StudentResponse, StudentImportResult
from app.services.audit import log_event

router = APIRouter(prefix="/courses", tags=["students"])


def _get_course_for_teacher(course_id: int, current_user: User, db: Session) -> Course:
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    if current_user.role == "teacher" and course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="No eres el docente de este curso")
    return course


@router.get("/{course_id}/students", response_model=List[StudentResponse])
def list_students(
    course_id: int,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """List all students in a course."""
    _get_course_for_teacher(course_id, current_user, db)
    return db.query(Student).filter(Student.course_id == course_id).order_by(Student.name).all()


@router.post("/{course_id}/students", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(
    course_id: int,
    student_in: StudentCreate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """Add a single student to a course."""
    _get_course_for_teacher(course_id, current_user, db)

    # Check if email already exists in this course
    existing = db.query(Student).filter(
        Student.course_id == course_id,
        Student.email == student_in.email
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe un estudiante con el email '{student_in.email}' en este curso"
        )

    student = Student(
        name=student_in.name,
        email=student_in.email,
        course_id=course_id,
    )
    db.add(student)
    db.commit()
    db.refresh(student)

    log_event(db, user_id=current_user.id, action="create_student",
              entity="student", entity_id=str(student.id),
              details={"name": student.name, "email": student.email})
    return student


@router.post("/{course_id}/students/import", response_model=StudentImportResult)
async def import_students_csv(
    course_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """
    Import students from a CSV file.
    Expected format: two columns — 'nombre' and 'correo' (with or without header).
    Duplicate emails within the course are skipped.
    """
    _get_course_for_teacher(course_id, current_user, db)

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos .csv")

    content = await file.read()
    text = content.decode("utf-8-sig")  # handle BOM from Excel exports

    reader = csv.reader(io.StringIO(text))
    rows = list(reader)

    created = 0
    skipped = 0
    errors = []

    # Auto-detect if first row is a header
    start_idx = 0
    if rows and rows[0] and rows[0][0].strip().lower() in ("nombre", "name", "names", "estudiante"):
        start_idx = 1

    for i, row in enumerate(rows[start_idx:], start=start_idx + 1):
        if len(row) < 2:
            errors.append(f"Fila {i}: formato incorrecto (se esperan 2 columnas: nombre, correo)")
            continue

        name = row[0].strip()
        email = row[1].strip().lower()

        if not name or not email or "@" not in email:
            errors.append(f"Fila {i}: datos inválidos — nombre='{name}', correo='{email}'")
            continue

        existing = db.query(Student).filter(
            Student.course_id == course_id,
            Student.email == email
        ).first()
        if existing:
            skipped += 1
            continue

        student = Student(name=name, email=email, course_id=course_id)
        db.add(student)
        created += 1

    db.commit()

    log_event(db, user_id=current_user.id, action="import_students_csv",
              entity="course", entity_id=str(course_id),
              details={"created": created, "skipped": skipped, "errors": len(errors)})

    return StudentImportResult(created=created, skipped=skipped, errors=errors)


@router.delete("/{course_id}/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(
    course_id: int,
    student_id: int,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """Remove a student from a course. Also deletes their reports and flash sessions (cascade)."""
    _get_course_for_teacher(course_id, current_user, db)

    student = db.query(Student).filter(
        Student.id == student_id,
        Student.course_id == course_id
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado en este curso")

    db.delete(student)
    db.commit()

    log_event(db, user_id=current_user.id, action="delete_student",
              entity="student", entity_id=str(student_id), details={})
