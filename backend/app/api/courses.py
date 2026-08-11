from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user, require_teacher, require_staff
from app.models.models import Course, User, enrollments, Institution
from app.schemas.schemas import CourseCreate, CourseResponse, StudentEnroll, UserResponse
from app.services.audit import log_event

router = APIRouter(prefix="/courses", tags=["courses"])

@router.post("/", response_model=CourseResponse)
def create_course(
    course_in: CourseCreate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """
    Creates a new course. Only teachers can create courses.
    The course will be associated with the teacher who creates it.
    """
    # If the teacher is not linked to an institution, use the one from the payload
    # Otherwise, force the teacher's institution for data safety
    institution_id = current_user.institution_id
    if not institution_id:
        institution_id = course_in.institution_id
        # Verify institution exists
        inst = db.query(Institution).filter(Institution.id == institution_id).first()
        if not inst:
            raise HTTPException(status_code=404, detail="La institución especificada no existe")
            
    course = Course(
        name=course_in.name,
        period=course_in.period,
        teacher_id=current_user.id,
        institution_id=institution_id
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    
    # Audit log
    log_event(
        db,
        user_id=current_user.id,
        action="create_course",
        entity="course",
        entity_id=str(course.id),
        details={"name": course.name, "period": course.period}
    )
    
    return course

@router.get("/", response_model=List[CourseResponse])
def get_courses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lists courses based on user role:
    - Students see courses they are enrolled in.
    - Teachers see courses they teach.
    - Admins see all courses in their institution.
    """
    if current_user.role == "student":
        # Courses student is enrolled in
        courses = current_user.enrolled_courses
    elif current_user.role == "teacher":
        courses = db.query(Course).filter(Course.teacher_id == current_user.id).all()
    else: # admin
        if current_user.institution_id:
            courses = db.query(Course).filter(Course.institution_id == current_user.institution_id).all()
        else:
            courses = db.query(Course).all()
            
    # Map teacher name to output
    response_courses = []
    for c in courses:
        rc = CourseResponse.from_orm(c)
        rc.teacher_name = c.teacher.name
        response_courses.append(rc)
        
    return response_courses

@router.get("/{course_id}", response_model=CourseResponse)
def get_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
        
    # Check permissions (student must be enrolled, teacher must own it, admin must be in same inst)
    if current_user.role == "student" and course not in current_user.enrolled_courses:
        raise HTTPException(status_code=403, detail="No estás inscrito en este curso")
    elif current_user.role == "teacher" and course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="No eres el docente de este curso")
        
    rc = CourseResponse.from_orm(course)
    rc.teacher_name = course.teacher.name
    return rc

@router.post("/{course_id}/enroll", status_code=status.HTTP_201_CREATED)
def enroll_student(
    course_id: int,
    enroll_in: StudentEnroll,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """
    Enrolls a student in a course by their email. Only teachers of the course can enroll.
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
        
    if course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permisos sobre este curso")
        
    student = db.query(User).filter(User.email == enroll_in.student_email, User.role == "student").first()
    if not student:
        raise HTTPException(
            status_code=404,
            detail=f"Estudiante con correo '{enroll_in.student_email}' no encontrado. Debe registrarse primero."
        )
        
    # Check if already enrolled
    if student in course.students:
        raise HTTPException(status_code=400, detail="El estudiante ya está inscrito en este curso")
        
    course.students.append(student)
    db.commit()
    
    # Audit log
    log_event(
        db,
        user_id=current_user.id,
        action="enroll_student",
        entity="course",
        entity_id=str(course.id),
        details={"student_id": student.id, "student_email": student.email}
    )
    
    return {"message": f"Estudiante {student.name} inscrito exitosamente en {course.name}"}

@router.get("/{course_id}/students", response_model=List[UserResponse])
def get_course_students(
    course_id: int,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db)
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
        
    if current_user.role == "teacher" and course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permisos sobre este curso")
        
    return course.students
