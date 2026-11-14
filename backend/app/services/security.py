import hashlib
import hmac
import time
from fastapi import HTTPException, Request
from sqlalchemy import case
from sqlalchemy.dialects.sqlite import insert
from backend.app import models
from backend.app.config import settings

DEMO_EMAILS = {"admin@universidad.cl", "docente@universidad.cl", "ayudante@universidad.cl"}


def demo_disabled(email):
    return not settings.SEED_DEMO_DATA and email.lower() in DEMO_EMAILS


def throttle(db, request: Request, action: str, *, account="", limit=10, seconds=60):
    """Persist an atomic counter. The client address comes from the trusted ASGI peer."""
    peer = request.client.host if request.client else "unknown"
    material = f"{action}|{peer}|{account.lower()}".encode()
    digest = hmac.new(settings.SECRET_KEY.encode(), material, hashlib.sha256).hexdigest()
    now = int(time.time())
    window = now // seconds * seconds
    stmt = insert(models.AuthThrottle).values(key_hash=digest, window_start=window, attempts=1)
    stmt = stmt.on_conflict_do_update(index_elements=[models.AuthThrottle.key_hash], set_={
        "attempts": case((models.AuthThrottle.window_start == window, models.AuthThrottle.attempts + 1), else_=1),
        "window_start": window,
    }).returning(models.AuthThrottle.attempts)
    count = db.execute(stmt).scalar_one()
    db.query(models.AuthThrottle).filter(models.AuthThrottle.window_start < now - 86400).delete()
    db.commit()
    if count > limit:
        raise HTTPException(429, "Demasiados intentos. Espera antes de volver a intentar.", headers={"Retry-After": str(window + seconds - now)})
