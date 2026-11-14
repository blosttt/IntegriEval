import asyncio
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from backend.app.auth import require_admin
from backend.app.config import settings
from backend.app.database import get_db
from backend.app.audit import log_audit

router = APIRouter(prefix='/api/admin', tags=['Preparación y respaldos'])


@router.get('/preparacion')
def readiness(user=Depends(require_admin), db: Session = Depends(get_db)):
    from tools.readiness import inspect_readiness
    result = inspect_readiness(settings)
    from backend.app.routers.smtp_admin import public_config
    smtp = public_config(db)
    for check in result['checks']:
        if check['id'] == 'smtp':
            check['ok'] = check['ok'] and smtp['verified']
    return result


@router.post('/respaldos')
async def backup(request: Request, user=Depends(require_admin), db: Session = Depends(get_db)):
    from backend.app.services.security import throttle
    throttle(db, request, 'backup', account=str(user.id), limit=1)
    # Avoid repeated expensive snapshots from double clicks or parallel tabs.
    from datetime import datetime, timezone
    archives = list(Path(settings.BACKUP_DIR).glob('integrieval-*.backup.zip'))
    if archives and datetime.now(timezone.utc).timestamp() - max(item.stat().st_mtime for item in archives) < 60:
        raise HTTPException(429, 'Ya existe un respaldo reciente. Espera un minuto antes de crear otro.')
    from backend.app.services.backups import snapshot
    try:
        result = await asyncio.to_thread(snapshot, settings)
    except Exception:
        raise HTTPException(503, 'No se pudo completar el respaldo. Revisa los registros y el espacio disponible.')
    log_audit(db, 'CREAR_RESPALDO', 'configuracion', None, user.id, datos_nuevos=result)
    return result
