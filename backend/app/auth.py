import bcrypt
import jwt
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app import models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def hash_password(password: str) -> str:
    """Hash password using bcrypt with factor >= 12 (RNF-005)"""
    salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash"""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate JWT token (RNF-004)"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.Usuario:
    """Retrieve and authenticate current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales de acceso",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)
    except Exception:
        raise credentials_exception

    user = db.query(models.Usuario).filter(models.Usuario.id == user_id).first()
    if user is None:
        raise credentials_exception
    account = db.get(models.AccountStatus, user.id)
    if account and not account.active:
        raise HTTPException(403, "La cuenta está desactivada")
    return user

def check_course_access(asignatura_id: int, user: models.Usuario, db: Session, write: bool = False) -> models.Asignatura:
    """RBAC check: verify teacher owns or has access to the asignatura (RNF-006)"""
    course = db.query(models.Asignatura).filter(models.Asignatura.id == asignatura_id).first()
    if not course or (course.parametros or {}).get("_archived"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asignatura no encontrada")
    
    assistant = user.rol == "ayudante" and db.query(models.CourseAssistant).filter_by(asignatura_id=course.id, usuario_id=user.id).first() is not None
    teacher = user.rol == "docente" and db.get(models.CourseTeacher, (course.id, user.id)) is not None
    if user.rol != "admin" and course.docente_id != user.id and not assistant and not teacher:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: no tiene permisos sobre esta asignatura"
        )
    return course


def require_admin(user: models.Usuario = Depends(get_current_user)):
    if user.rol != "admin":
        raise HTTPException(403, "Esta operación está reservada al administrador")
    return user


def check_roster_access(asignatura_id: int, user: models.Usuario, db: Session):
    course = check_course_access(asignatura_id, user, db, write=True)
    if user.rol == "ayudante":
        raise HTTPException(403, "El ayudante puede consultar la nómina, pero no agregar, editar, importar ni retirar alumnos")
    return course
