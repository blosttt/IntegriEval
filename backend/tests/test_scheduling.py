import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import datetime

from app.core.database import Base
import app.models.models as m
from app.services.scheduling import process_session_result

TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_context():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    
    # Seed Institution, Teacher, Course, and Students
    inst = m.Institution(name="UCT Test", type="university")
    session.add(inst)
    session.commit()
    
    teacher = m.User(email="profe@uct.cl", password_hash="hash", name="Profe", role="teacher", institution_id=inst.id)
    student1 = m.User(email="alumno1@uct.cl", password_hash="hash", name="Alumno 1", role="student", institution_id=inst.id)
    student2 = m.User(email="alumno2@uct.cl", password_hash="hash", name="Alumno 2", role="student", institution_id=inst.id)
    session.add_all([teacher, student1, student2])
    session.commit()
    
    course = m.Course(name="Ingeniería de Software", period="2026-1", teacher_id=teacher.id, institution_id=inst.id)
    session.add(course)
    session.commit()
    
    course.students.extend([student1, student2])
    session.commit()
    
    # Create Evaluation with thresholds
    evaluation = m.Evaluation(
        course_id=course.id,
        title="Certamen 1",
        due_date=datetime.datetime.utcnow() + datetime.timedelta(days=1),
        start_window=datetime.datetime.utcnow(),
        end_window=datetime.datetime.utcnow() + datetime.timedelta(days=2),
        time_per_question=30,
        num_questions=1,
        pass_threshold=0.6,
        excellence_threshold=0.9,
        require_approval=True
    )
    session.add(evaluation)
    session.commit()
    
    yield session, evaluation, student1, student2, teacher
    
    session.close()
    Base.metadata.drop_all(bind=engine)

def test_scheduling_on_failing_score(db_context):
    """
    Verifies that scoring below the pass threshold automatically schedules
    a defense session for the student.
    """
    session, evaluation, student1, student2, teacher = db_context
    
    # 1. Create student report
    report = m.Report(
        evaluation_id=evaluation.id,
        student_id=student1.id,
        file_path="mock_path.pdf",
        extracted_text="Metodologías de desarrollo ágil en la Universidad Católica de Temuco."
    )
    session.add(report)
    session.commit()
    
    # 2. Setup Question Bank with 1 question
    bank = m.QuestionBank(
        evaluation_id=evaluation.id,
        student_id=student1.id,
        is_generated=True,
        is_approved=True
    )
    session.add(bank)
    session.commit()
    
    question = m.Question(
        question_bank_id=bank.id,
        text="¿Se menciona Scrum en el informe?",
        type="true_false",
        correct_answer="0", # "Verdadero"
        limit_seconds=30
    )
    session.add(question)
    session.commit()
    
    # 3. Start Session and record incorrect answer (0/1 = 0% score < 60% threshold)
    eval_session = m.EvaluationSession(
        evaluation_id=evaluation.id,
        student_id=student1.id,
        status="started"
    )
    session.add(eval_session)
    session.commit()
    
    answer = m.Answer(
        session_id=eval_session.id,
        question_id=question.id,
        student_answer="1", # "Falso" -> Incorrect
        is_correct=False,
        response_time_ms=5000
    )
    session.add(answer)
    session.commit()
    
    # 4. Trigger grading process
    process_session_result(session, eval_session.id)
    
    # Assert session is closed and classified as low
    assert eval_session.status == "completed"
    assert eval_session.classification == "low"
    assert eval_session.score == 0.0
    
    # Assert a defense appointment is created for Alumno 1
    appointment = session.query(m.Appointment).filter(
        m.Appointment.evaluation_id == evaluation.id,
        m.Appointment.student_id == student1.id
    ).first()
    
    assert appointment is not None
    assert appointment.type == "defense"
    assert appointment.teacher_id == teacher.id
    assert appointment.status == "pending"
