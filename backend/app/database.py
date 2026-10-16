from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def protect_audit_logs():
    """Prevent audit updates and deletes at the SQLite storage layer."""
    if engine.dialect.name == "sqlite":
        from sqlalchemy import text
        with engine.begin() as connection:
            for action in ("UPDATE", "DELETE"):
                connection.execute(text(f"CREATE TRIGGER IF NOT EXISTS audit_no_{action.lower()} BEFORE {action} ON audit_logs BEGIN SELECT RAISE(ABORT, 'audit_logs are append-only'); END"))
