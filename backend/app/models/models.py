import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, JSON, Table
from sqlalchemy.orm import relationship
from app.core.database import Base

# Association table for student enrollment in courses
enrollments = Table(
    "enrollments",
    Base.metadata,
    Column("student_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("course_id", Integer, ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True),
    Column("enrolled_at", DateTime, default=datetime.datetime.utcnow)
)

class Institution(Base):
    __tablename__ = "institutions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    type = Column(String, nullable=False) # e.g., "university" or "school"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    users = relationship("User", back_populates="institution", cascade="all, delete-orphan")
    courses = relationship("Course", back_populates="institution", cascade="all, delete-orphan")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False) # "student", "teacher", "admin"
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    institution = relationship("Institution", back_populates="users")
    
    # As teacher
    taught_courses = relationship("Course", back_populates="teacher", foreign_keys="Course.teacher_id")
    teacher_appointments = relationship("Appointment", back_populates="teacher", foreign_keys="Appointment.teacher_id")
    availabilities = relationship("TeacherAvailability", back_populates="teacher", cascade="all, delete-orphan")

    # As student
    enrolled_courses = relationship("Course", secondary=enrollments, back_populates="students")
    reports = relationship("Report", back_populates="student", cascade="all, delete-orphan")
    question_banks = relationship("QuestionBank", back_populates="student", cascade="all, delete-orphan", foreign_keys="QuestionBank.student_id")
    evaluation_sessions = relationship("EvaluationSession", back_populates="student", cascade="all, delete-orphan")
    student_appointments = relationship("Appointment", back_populates="student", foreign_keys="Appointment.student_id")
    audit_logs = relationship("AuditLog", back_populates="user")

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    period = Column(String, nullable=False) # e.g., "2026-1", "Primer Semestre"
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    teacher = relationship("User", back_populates="taught_courses", foreign_keys=[teacher_id])
    institution = relationship("Institution", back_populates="courses")
    students = relationship("User", secondary=enrollments, back_populates="enrolled_courses")
    evaluations = relationship("Evaluation", back_populates="course", cascade="all, delete-orphan")

class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    prompt_teacher = Column(String, nullable=True) # rubrics or general prompt
    due_date = Column(DateTime, nullable=False) # report upload deadline
    start_window = Column(DateTime, nullable=False) # when flash test opens
    end_window = Column(DateTime, nullable=False) # when flash test closes
    time_per_question = Column(Integer, default=30) # time in seconds
    num_questions = Column(Integer, default=5)
    pass_threshold = Column(Float, default=0.6) # percentage (e.g. 60%) to pass
    excellence_threshold = Column(Float, default=0.95) # score >= this triggers excellence flow
    require_approval = Column(Boolean, default=True) # require teacher approval for question bank
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    course = relationship("Course", back_populates="evaluations")
    reports = relationship("Report", back_populates="evaluation", cascade="all, delete-orphan")
    question_banks = relationship("QuestionBank", back_populates="evaluation", cascade="all, delete-orphan")
    sessions = relationship("EvaluationSession", back_populates="evaluation", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="evaluation", cascade="all, delete-orphan")

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    evaluation_id = Column(Integer, ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String, nullable=False)
    extracted_text = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)

    evaluation = relationship("Evaluation", back_populates="reports")
    student = relationship("User", back_populates="reports")

class QuestionBank(Base):
    __tablename__ = "question_banks"

    id = Column(Integer, primary_key=True, index=True)
    evaluation_id = Column(Integer, ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    is_generated = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=False)
    approved_by_teacher_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    evaluation = relationship("Evaluation", back_populates="question_banks")
    student = relationship("User", back_populates="question_banks", foreign_keys=[student_id])
    questions = relationship("Question", back_populates="bank", cascade="all, delete-orphan")

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    question_bank_id = Column(Integer, ForeignKey("question_banks.id", ondelete="CASCADE"), nullable=False)
    text = Column(String, nullable=False)
    type = Column(String, nullable=False) # "multiple_choice", "true_false", "short_answer"
    options = Column(JSON, nullable=True) # List of strings for multiple choice
    correct_answer = Column(String, nullable=False) # correct alternative index (e.g. "0") or text
    limit_seconds = Column(Integer, default=30)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    bank = relationship("QuestionBank", back_populates="questions")

class EvaluationSession(Base):
    __tablename__ = "evaluation_sessions"

    id = Column(Integer, primary_key=True, index=True)
    evaluation_id = Column(Integer, ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    status = Column(String, default="started") # "started", "completed", "abandoned"
    score = Column(Float, nullable=True) # raw score
    percentage_score = Column(Float, nullable=True) # percentage 0.0 - 1.0
    classification = Column(String, nullable=True) # "low", "medium", "high"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    evaluation = relationship("Evaluation", back_populates="sessions")
    student = relationship("User", back_populates="evaluation_sessions")
    answers = relationship("Answer", back_populates="session", cascade="all, delete-orphan")

class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("evaluation_sessions.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    student_answer = Column(String, nullable=True) # answer text or option index; Null if skipped/timed out
    is_correct = Column(Boolean, default=False)
    response_time_ms = Column(Integer, nullable=True) # time taken in ms
    answered_at = Column(DateTime, default=datetime.datetime.utcnow)

    session = relationship("EvaluationSession", back_populates="answers")
    question = relationship("Question")

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    evaluation_id = Column(Integer, ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(String, nullable=False) # "defense" (oral defense for low score) or "random_verification" (high score / random peer)
    scheduled_time = Column(DateTime, nullable=False)
    status = Column(String, default="pending") # "pending", "completed", "cancelled", "rescheduled"
    notes = Column(String, nullable=True) # adjustment notes by teacher
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    evaluation = relationship("Evaluation", back_populates="appointments")
    student = relationship("User", back_populates="student_appointments", foreign_keys=[student_id])
    teacher = relationship("User", back_populates="teacher_appointments", foreign_keys=[teacher_id])

class TeacherAvailability(Base):
    __tablename__ = "teacher_availabilities"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    day_of_week = Column(Integer, nullable=False) # 0 = Monday, 6 = Sunday
    start_time = Column(String, nullable=False) # "HH:MM" format
    end_time = Column(String, nullable=False) # "HH:MM" format
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    teacher = relationship("User", back_populates="availabilities")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String, nullable=False) # e.g. "upload_report", "start_eval", "answer_question"
    entity = Column(String, nullable=False) # e.g. "report", "evaluation_session"
    entity_id = Column(String, nullable=True) # ID of the entity affected
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    details = Column(JSON, nullable=True) # JSON with details (IP, browser, etc.)

    user = relationship("User", back_populates="audit_logs")
