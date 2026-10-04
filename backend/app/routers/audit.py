from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app import models, schemas
from backend.app.auth import get_current_user

router = APIRouter(prefix="/api/audit", tags=["Auditoría Inmutable"])

@router.get("", response_model=List[schemas.AuditLogOut])
def get_audit_logs(
    limit: int = 100,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve immutable audit log trail (RD-AuditLog, RN-004).
    Ensures complete legal, academic and ethical compliance under Ley N° 21.719 (RNF-013).
    """
    query = db.query(models.AuditLog).order_by(models.AuditLog.timestamp.desc())
    if current_user.rol != "admin":
        query = query.filter(models.AuditLog.usuario_id == current_user.id)

    logs = query.limit(limit).all()

    result = []
    for l in logs:
        result.append(
            schemas.AuditLogOut(
                id=l.id,
                usuario_id=l.usuario_id,
                usuario_nombre=l.usuario.nombre if l.usuario else "Sistema / Estudiante",
                accion=l.accion,
                tabla=l.tabla,
                registro_id=l.registro_id,
                timestamp=l.timestamp,
                datos_previos=l.datos_previos,
                datos_nuevos=l.datos_nuevos
            )
        )
    return result
