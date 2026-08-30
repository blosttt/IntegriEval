from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user, require_teacher, require_staff
from app.models.models import Course, User, Institution, Student
from app.schemas.schemas import CourseCreate, CourseResponse
from app.services.audit import log_event

router = APIRouter(prefix="/courses", tags=["courses"])


@router.post("/", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(
    course_in: CourseCreate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """Creates a new course. Only teachers and admins can create courses."""
    institution_id = current_user.institution_id or course_in.institution_id
    if not institution_id:
        raise HTTPException(status_code=400, detail="Se requiere una institución")

    inst = db.query(Institution).filter(Institution.id == institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="La institución especificada no existe")

    course = Course(
        name=course_in.name,
        period=course_in.period,
        teacher_id=current_user.id,
        institution_id=institution_id,
    )
    db.add(course)
    db.commit()
    db.refresh(course)

    log_event(db, user_id=current_user.id, action="create_course",
              entity="course", entity_id=str(course.id),
              details={"name": course.name, "period": course.period})

    return _enrich(course, db)


@router.get("/", response_model=List[CourseResponse])
def get_courses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lists courses based on role: teacher sees own courses, admin sees all."""
    if current_user.role == "teacher":
        courses = db.query(Course).filter(Course.teacher_id == current_user.id).all()
    else:  # admin
        if current_user.institution_id:
            courses = db.query(Course).filter(
                Course.institution_id == current_user.institution_id
            ).all()
        else:
            courses = db.query(Course).all()

    return [_enrich(c, db) for c in courses]


@router.get("/{course_id}", response_model=CourseResponse)
def get_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    if current_user.role == "teacher" and course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="No eres el docente de este curso")

    return _enrich(course, db)


def _enrich(course: Course, db: Session) -> CourseResponse:
    resp = CourseResponse.model_validate(course)
    resp.teacher_name = course.teacher.name if course.teacher else None
    resp.student_count = db.query(Student).filter(Student.course_id == course.id).count()
    return resp
