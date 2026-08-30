import datetime
import uuid
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, JSON, Text, Table
from sqlalchemy.orm import relationship
from app.core.database import Base

# Association table for teacher enrollment in courses (kept for admin use)
enrollments = Table(
    "enrollments",
    Base.metadata,
    Column("student_id", Integer, ForeignKey("students.id", ondelete="CASCADE"), primary_key=True),
    Column("course_id", Integer, ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True),
    Column("enrolled_at", DateTime, default=datetime.datetime.utcnow)
)


class Institution(Base):
    __tablename__ = "institutions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    type = Column(String, nullable=False)  # "university" | "school"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    users = relationship("User", back_populates="institution", cascade="all, delete-orphan")
    courses = relationship("Course", back_populates="institution", cascade="all, delete-orphan")


class User(Base):
    """Platform users with accounts: teacher, admin."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # "teacher" | "admin"
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    institution = relationship("Institution", back_populates="users")
    taught_courses = relationship("Course", back_populates="teacher", foreign_keys="Course.teacher_id")
    teacher_appointments = relationship("Appointment", back_populates="teacher", foreign_keys="Appointment.teacher_id")
    availabilities = relationship("TeacherAvailability", back_populates="teacher", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")


class Student(Base):
    """Lightweight student record — no account/password. Identified by email for flash test link."""
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    course = relationship("Course", back_populates="students")
    reports = relationship("Report", back_populates="student", cascade="all, delete-orphan")
    flash_sessions = relationship("FlashTestSession", back_populates="student", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="student", foreign_keys="Appointment.student_id")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    period = Column(String, nullable=False)  # e.g., "2026-1"
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    teacher = relationship("User", back_populates="taught_courses", foreign_keys=[teacher_id])
    institution = relationship("Institution", back_populates="courses")
    students = relationship("Student", back_populates="course", cascade="all, delete-orphan")
    evaluations = relationship("Evaluation", back_populates="course", cascade="all, delete-orphan")


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)

    # Rubric / analysis prompt defined by teacher
    prompt_rubric = Column(Text, nullable=True)  # What the AI should evaluate

    # Question generation parameters
    question_rigor = Column(String, default="medium")  # "strict" | "medium" | "lax"
    pool_size = Column(Integer, default=20)             # Total questions generated in pool
    flash_questions_count = Column(Integer, default=10) # Questions student actually sees
    time_per_question = Column(Integer, default=30)     # Seconds per question

    # Routing thresholds (based on flash test result)
    low_threshold = Column(Float, default=0.50)          # Flash score < this → office call
    high_threshold = Column(Float, default=0.95)         # Flash score >= this → office call
    random_review_pct = Column(Float, default=0.10)      # Random % called to office

    # Flash test link config
    flash_link_ttl_hours = Column(Integer, default=48)   # Hours before link expires

    require_approval = Column(Boolean, default=True)     # Teacher must approve question set before sending
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    course = relationship("Course", back_populates="evaluations")
    reports = relationship("Report", back_populates="evaluation", cascade="all, delete-orphan")
    materials = relationship("CourseMaterial", back_populates="evaluation", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="evaluation", cascade="all, delete-orphan")


class CourseMaterial(Base):
    """PDFs/DOCX uploaded by teacher as knowledge base for AI analysis and question generation."""
    __tablename__ = "course_materials"

    id = Column(Integer, primary_key=True, index=True)
    evaluation_id = Column(Integer, ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    markdown_content = Column(Text, nullable=True)  # Extracted content used as AI context
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)

    evaluation = relationship("Evaluation", back_populates="materials")


class Report(Base):
    """A student's submitted work, uploaded in bulk by the teacher."""
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    evaluation_id = Column(Integer, ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Markdown conversion
    markdown_content = Column(Text, nullable=True)

    # AI Analysis results
    analysis_status = Column(String, default="pending")  # "pending"|"processing"|"done"|"error"
    ai_score_percentage = Column(Float, nullable=True)      # Preliminary score by AI (0.0–1.0)
    ai_detected_percentage = Column(Float, nullable=True)   # AI-generated content likelihood (0.0–1.0)
    analysis_feedback = Column(Text, nullable=True)         # Textual justification
    analysis_breakdown = Column(JSON, nullable=True)        # e.g. {"methodology": 0.8, "results": 0.75}

    # Teacher adjustments
    teacher_score_override = Column(Float, nullable=True)   # Manual override of AI score

    # Final score (may be adjusted after office appointment)
    final_score_percentage = Column(Float, nullable=True)

    # Flash test tracking
    flash_token = Column(String, unique=True, nullable=True, index=True)  # UUID for email link
    flash_token_expires_at = Column(DateTime, nullable=True)
    flash_email_sent = Column(Boolean, default=False)
    flash_completed = Column(Boolean, default=False)

    # Review / office call
    review_required = Column(Boolean, default=False)
    review_reason = Column(String, nullable=True)  # "low_flash"|"high_flash"|"random"|"ai_suspicion"

    evaluation = relationship("Evaluation", back_populates="reports")
    student = relationship("Student", back_populates="reports")
    question_bank = relationship("QuestionBank", back_populates="report", uselist=False, cascade="all, delete-orphan")
    flash_session = relationship("FlashTestSession", back_populates="report", uselist=False, cascade="all, delete-orphan")


class QuestionBank(Base):
    """Pool of AI-generated questions for a specific student's report.
    Teacher can review, edit, add, remove and select which ones to send."""
    __tablename__ = "question_banks"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, unique=True)
    evaluation_id = Column(Integer, ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)

    is_generated = Column(Boolean, default=False)      # AI has finished generating
    is_approved = Column(Boolean, default=False)       # Teacher approved & sent email
    approved_by_teacher_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    # IDs of selected questions (subset of pool to send to student)
    selected_question_ids = Column(JSON, nullable=True)  # List[int]

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    report = relationship("Report", back_populates="question_bank")
    questions = relationship("Question", back_populates="bank", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    question_bank_id = Column(Integer, ForeignKey("question_banks.id", ondelete="CASCADE"), nullable=False)
    text = Column(String, nullable=False)
    type = Column(String, nullable=False)  # "multiple_choice" | "true_false"
    options = Column(JSON, nullable=True)  # List of option strings
    correct_answer = Column(String, nullable=False)  # index as string: "0","1","2","3" or "0"/"1" for T/F
    limit_seconds = Column(Integer, default=30)
    is_custom = Column(Boolean, default=False)  # True if created by teacher, not AI
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    bank = relationship("QuestionBank", back_populates="questions")


class FlashTestSession(Base):
    """Tracks the student's flash test attempt, initiated via email token."""
    __tablename__ = "flash_test_sessions"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, unique=True)
    evaluation_id = Column(Integer, ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)

    status = Column(String, default="pending")  # "pending"|"started"|"completed"|"expired"
    score = Column(Float, nullable=True)
    percentage_score = Column(Float, nullable=True)
    classification = Column(String, nullable=True)  # "low"|"medium"|"high"

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    report = relationship("Report", back_populates="flash_session")
    student = relationship("Student", back_populates="flash_sessions")
    answers = relationship("Answer", back_populates="session", cascade="all, delete-orphan")


class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("flash_test_sessions.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    student_answer = Column(String, nullable=True)  # Null if skipped/timed out
    is_correct = Column(Boolean, default=False)
    response_time_ms = Column(Integer, nullable=True)
    answered_at = Column(DateTime, default=datetime.datetime.utcnow)

    session = relationship("FlashTestSession", back_populates="answers")
    question = relationship("Question")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    evaluation_id = Column(Integer, ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(String, nullable=False)   # "defense" | "high_score_verification" | "random_verification"
    scheduled_time = Column(DateTime, nullable=False)
    status = Column(String, default="pending")  # "pending"|"completed"|"cancelled"|"rescheduled"
    notes = Column(String, nullable=True)

    # Score adjustment after appointment
    adjusted_score = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    evaluation = relationship("Evaluation", back_populates="appointments")
    student = relationship("Student", back_populates="appointments", foreign_keys=[student_id])
    teacher = relationship("User", back_populates="teacher_appointments", foreign_keys=[teacher_id])


class TeacherAvailability(Base):
    __tablename__ = "teacher_availabilities"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = Column(String, nullable=False)    # "HH:MM"
    end_time = Column(String, nullable=False)      # "HH:MM"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    teacher = relationship("User", back_populates="availabilities")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String, nullable=False)
    entity = Column(String, nullable=False)
    entity_id = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    details = Column(JSON, nullable=True)

    user = relationship("User", back_populates="audit_logs")
