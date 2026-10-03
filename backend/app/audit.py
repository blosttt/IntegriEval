from typing import Optional, Any, Dict
from sqlalchemy.orm import Session
from backend.app import models

def log_audit(
    db: Session,
    accion: str,
    tabla: str,
    registro_id: Optional[int] = None,
    usuario_id: Optional[int] = None,
    datos_previos: Optional[Dict[str, Any]] = None,
    datos_nuevos: Optional[Dict[str, Any]] = None
) -> models.AuditLog:
    """
    Persist immutable audit log entry (RN-004, RNF-004, RD-AuditLog).
    Any critical change (grade edits, oral citations, settings modifications) must be recorded.
    """
    entry = models.AuditLog(
        usuario_id=usuario_id,
        accion=accion,
        tabla=tabla,
        registro_id=registro_id,
        datos_previos=datos_previos,
        datos_nuevos=datos_nuevos
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
