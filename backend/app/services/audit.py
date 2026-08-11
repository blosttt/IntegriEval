from sqlalchemy.orm import Session
from app.models.models import AuditLog
import datetime
from typing import Optional, Any

def log_event(
    db: Session,
    user_id: Optional[int],
    action: str,
    entity: str,
    entity_id: Optional[str],
    details: Optional[Any] = None
):
    """
    Log an event to the audit_logs table.
    Ensures rollback in case database commit fails, without crashing the main application flow.
    """
    log = AuditLog(
        user_id=user_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        details=details,
        timestamp=datetime.datetime.utcnow()
    )
    db.add(log)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        # Fallback console log if DB fails
        print(f"Audit log failed to write to DB: {e}. Action was: {action} on {entity} (ID: {entity_id})")
