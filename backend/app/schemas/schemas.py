from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Any
from datetime import datetime

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    name: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None

# --- User Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: str # "student", "teacher", "admin"
    institution_id: Optional[int] = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- Institution Schemas ---
class InstitutionBase(BaseModel):
    name: str
    type: str # "university", "school"

class InstitutionCreate(InstitutionBase):
    pass

class InstitutionResponse(InstitutionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- Course Schemas ---
class CourseBase(BaseModel):
    name: str
    period: str
    institution_id: int

class CourseCreate(CourseBase):
    teacher_id: Optional[int] = None # Filled from current user if they are a teacher

class CourseResponse(CourseBase):
    id: int
    teacher_id: int
    created_at: datetime
    teacher_name: Optional[str] = None

    class Config:
        from_attributes = True

class StudentEnroll(BaseModel):
    student_email: EmailStr

# --- Evaluation Schemas ---
class EvaluationBase(BaseModel):
    title: str
    prompt_teacher: Optional[str] = None
    due_date: datetime
    start_window: datetime
    end_window: datetime
    time_per_question: int = 30
    num_questions: int = 5
    pass_threshold: float = 0.6
    excellence_threshold: float = 0.95
    require_approval: bool = True

class EvaluationCreate(EvaluationBase):
    pass

class EvaluationResponse(EvaluationBase):
    id: int
    course_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- Report Schemas ---
class ReportResponse(BaseModel):
    id: int
    evaluation_id: int
    student_id: int
    file_path: str
    uploaded_at: datetime

    class Config:
        from_attributes = True

# --- Question Schemas ---
class QuestionBase(BaseModel):
    text: str
    type: str # "multiple_choice", "true_false", "short_answer"
    options: Optional[List[str]] = None
    limit_seconds: int = 30

class QuestionCreate(QuestionBase):
    correct_answer: str

class QuestionResponse(QuestionBase):
    id: int
    question_bank_id: int

    class Config:
        from_attributes = True

# --- Question Bank Schemas ---
class QuestionBankResponse(BaseModel):
    id: int
    evaluation_id: int
    student_id: int
    is_generated: bool
    is_approved: bool
    approved_by_teacher_id: Optional[int] = None
    questions: List[QuestionResponse] = []

    class Config:
        from_attributes = True

class QuestionEdit(BaseModel):
    id: int
    text: str
    options: Optional[List[str]] = None
    correct_answer: str
    limit_seconds: int

class QuestionBankReview(BaseModel):
    is_approved: bool
    questions: List[QuestionEdit]

# --- Evaluation Session Schemas ---
class EvaluationSessionStart(BaseModel):
    evaluation_id: int

class EvaluationSessionResponse(BaseModel):
    id: int
    evaluation_id: int
    student_id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str
    score: Optional[float] = None
    percentage_score: Optional[float] = None
    classification: Optional[str] = None

    class Config:
        from_attributes = True

class AnswerSubmit(BaseModel):
    question_id: int
    student_answer: Optional[str] = None # can be index or text, null if skipped
    response_time_ms: int

# --- Appointment Schemas ---
class AppointmentBase(BaseModel):
    evaluation_id: int
    student_id: int
    teacher_id: int
    type: str # "defense", "random_verification"
    scheduled_time: datetime

class AppointmentCreate(BaseModel):
    evaluation_id: int
    student_id: int
    scheduled_time: datetime
    type: str

class AppointmentResponse(AppointmentBase):
    id: int
    status: str
    notes: Optional[str] = None
    student_name: Optional[str] = None
    teacher_name: Optional[str] = None
    evaluation_title: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AppointmentFeedback(BaseModel):
    status: str # "completed", "cancelled"
    notes: Optional[str] = None
    adjusted_score: Optional[float] = None # Optional score adjustment by teacher

# --- Teacher Availability Schemas ---
class TeacherAvailabilityBase(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6) # 0 = Monday, 6 = Sunday
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$") # "HH:MM"
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$") # "HH:MM"

class TeacherAvailabilityCreate(TeacherAvailabilityBase):
    pass

class TeacherAvailabilityResponse(TeacherAvailabilityBase):
    id: int
    teacher_id: int

    class Config:
        from_attributes = True

# --- Audit Log Schemas ---
class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    action: str
    entity: str
    entity_id: Optional[str] = None
    timestamp: datetime
    details: Optional[Any] = None

    class Config:
        from_attributes = True
