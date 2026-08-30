from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Any, Dict
from datetime import datetime

# ─────────────────────────────────────────────
# Token / Auth
# ─────────────────────────────────────────────
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    name: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None

# ─────────────────────────────────────────────
# User (teacher / admin — has account)
# ─────────────────────────────────────────────
class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: str  # "teacher" | "admin"
    institution_id: Optional[int] = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# ─────────────────────────────────────────────
# Student (no account — managed by teacher)
# ─────────────────────────────────────────────
class StudentBase(BaseModel):
    name: str
    email: EmailStr

class StudentCreate(StudentBase):
    pass

class StudentResponse(StudentBase):
    id: int
    course_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class StudentImportRow(BaseModel):
    """Single row from CSV import: name + email."""
    name: str
    email: EmailStr

class StudentImportResult(BaseModel):
    created: int
    skipped: int
    errors: List[str] = []

# ─────────────────────────────────────────────
# Institution
# ─────────────────────────────────────────────
class InstitutionBase(BaseModel):
    name: str
    type: str  # "university" | "school"

class InstitutionCreate(InstitutionBase):
    pass

class InstitutionResponse(InstitutionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# ─────────────────────────────────────────────
# Course
# ─────────────────────────────────────────────
class CourseBase(BaseModel):
    name: str
    period: str
    institution_id: int

class CourseCreate(CourseBase):
    teacher_id: Optional[int] = None

class CourseResponse(CourseBase):
    id: int
    teacher_id: int
    created_at: datetime
    teacher_name: Optional[str] = None
    student_count: Optional[int] = None

    class Config:
        from_attributes = True

# ─────────────────────────────────────────────
# Evaluation
# ─────────────────────────────────────────────
class EvaluationBase(BaseModel):
    title: str
    prompt_rubric: Optional[str] = None          # AI analysis rubric / instructions
    question_rigor: str = "medium"               # "strict" | "medium" | "lax"
    pool_size: int = 20                           # Total questions AI generates
    flash_questions_count: int = 10              # Questions shown to student
    time_per_question: int = 30                  # Seconds per question
    low_threshold: float = 0.50                  # Flash score below → office
    high_threshold: float = 0.95                 # Flash score above → office
    random_review_pct: float = 0.10              # Random % → office
    flash_link_ttl_hours: int = 48               # Hours until link expires
    require_approval: bool = True                # Teacher must approve before sending

class EvaluationCreate(EvaluationBase):
    pass

class EvaluationUpdate(BaseModel):
    title: Optional[str] = None
    prompt_rubric: Optional[str] = None
    question_rigor: Optional[str] = None
    pool_size: Optional[int] = None
    flash_questions_count: Optional[int] = None
    time_per_question: Optional[int] = None
    low_threshold: Optional[float] = None
    high_threshold: Optional[float] = None
    random_review_pct: Optional[float] = None
    flash_link_ttl_hours: Optional[int] = None
    require_approval: Optional[bool] = None

class EvaluationResponse(EvaluationBase):
    id: int
    course_id: int
    created_at: datetime
    report_count: Optional[int] = None          # Number of reports uploaded

    class Config:
        from_attributes = True

# ─────────────────────────────────────────────
# Course Material
# ─────────────────────────────────────────────
class CourseMaterialResponse(BaseModel):
    id: int
    evaluation_id: int
    title: str
    file_path: str
    uploaded_at: datetime

    class Config:
        from_attributes = True

# ─────────────────────────────────────────────
# Report
# ─────────────────────────────────────────────
class ReportResponse(BaseModel):
    id: int
    evaluation_id: int
    student_id: int
    student_name: Optional[str] = None
    student_email: Optional[str] = None
    file_path: str
    uploaded_at: datetime

    # Analysis
    analysis_status: str
    ai_score_percentage: Optional[float] = None
    ai_detected_percentage: Optional[float] = None
    analysis_feedback: Optional[str] = None
    analysis_breakdown: Optional[Dict[str, float]] = None

    # Overrides
    teacher_score_override: Optional[float] = None
    final_score_percentage: Optional[float] = None

    # Flash test
    flash_email_sent: bool
    flash_completed: bool
    flash_token_expires_at: Optional[datetime] = None

    # Review
    review_required: bool
    review_reason: Optional[str] = None

    # Question bank status
    bank_generated: Optional[bool] = None
    bank_approved: Optional[bool] = None

    class Config:
        from_attributes = True

class ReportScoreUpdate(BaseModel):
    teacher_score_override: float = Field(..., ge=0.0, le=1.0)

# ─────────────────────────────────────────────
# Question
# ─────────────────────────────────────────────
class QuestionBase(BaseModel):
    text: str
    type: str  # "multiple_choice" | "true_false"
    options: Optional[List[str]] = None
    limit_seconds: int = 30

class QuestionCreate(QuestionBase):
    correct_answer: str

class QuestionUpdate(BaseModel):
    text: Optional[str] = None
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    limit_seconds: Optional[int] = None

class QuestionResponse(QuestionBase):
    id: int
    question_bank_id: int
    correct_answer: str
    is_custom: bool

    class Config:
        from_attributes = True

# ─────────────────────────────────────────────
# Question Bank
# ─────────────────────────────────────────────
class QuestionBankResponse(BaseModel):
    id: int
    report_id: int
    evaluation_id: int
    student_id: int
    is_generated: bool
    is_approved: bool
    selected_question_ids: Optional[List[int]] = None
    questions: List[QuestionResponse] = []

    class Config:
        from_attributes = True

class QuestionSelectPayload(BaseModel):
    """Payload to manually select which question IDs to include in flash test."""
    question_ids: List[int]

# ─────────────────────────────────────────────
# Flash Test Session
# ─────────────────────────────────────────────
class FlashTestSessionResponse(BaseModel):
    id: int
    report_id: int
    evaluation_id: int
    student_id: int
    status: str
    score: Optional[float] = None
    percentage_score: Optional[float] = None
    classification: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class FlashTokenValidateResponse(BaseModel):
    session_id: int
    student_name: str
    evaluation_title: str
    total_questions: int
    time_per_question: int

# ─────────────────────────────────────────────
# Answer
# ─────────────────────────────────────────────
class AnswerSubmit(BaseModel):
    question_id: int
    student_answer: Optional[str] = None
    response_time_ms: int

# ─────────────────────────────────────────────
# Appointment
# ─────────────────────────────────────────────
class AppointmentResponse(BaseModel):
    id: int
    evaluation_id: int
    student_id: int
    teacher_id: int
    type: str
    scheduled_time: datetime
    status: str
    notes: Optional[str] = None
    adjusted_score: Optional[float] = None
    student_name: Optional[str] = None
    student_email: Optional[str] = None
    teacher_name: Optional[str] = None
    evaluation_title: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AppointmentFeedback(BaseModel):
    status: str  # "completed" | "cancelled"
    notes: Optional[str] = None
    adjusted_score: Optional[float] = Field(None, ge=0.0, le=1.0)

# ─────────────────────────────────────────────
# Teacher Availability
# ─────────────────────────────────────────────
class TeacherAvailabilityBase(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6)
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")

class TeacherAvailabilityCreate(TeacherAvailabilityBase):
    pass

class TeacherAvailabilityResponse(TeacherAvailabilityBase):
    id: int
    teacher_id: int

    class Config:
        from_attributes = True

# ─────────────────────────────────────────────
# Audit Log
# ─────────────────────────────────────────────
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
