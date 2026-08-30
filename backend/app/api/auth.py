from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.core.database import get_db, settings
from app.core.security import hash_password, verify_password, create_access_token, get_current_user
from app.models.models import User, Institution
from app.schemas.schemas import UserCreate, UserResponse, Token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """Register a teacher or admin account. Students do NOT have accounts."""
    if user_in.role not in ("teacher", "admin"):
        raise HTTPException(
            status_code=400,
            detail="Solo se pueden registrar cuentas de tipo 'teacher' o 'admin'. "
                   "Los estudiantes son gestionados por el profesor sin cuenta propia."
        )

    db_user = db.query(User).filter(User.email == user_in.email).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="El correo electrónico ya se encuentra registrado"
        )

    if user_in.institution_id:
        inst = db.query(Institution).filter(Institution.id == user_in.institution_id).first()
        if not inst:
            raise HTTPException(status_code=404, detail="La institución especificada no existe")

    hashed = hash_password(user_in.password)
    user = User(
        email=user_in.email,
        password_hash=hashed,
        name=user_in.name,
        role=user_in.role,
        institution_id=user_in.institution_id
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo electrónico o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "name": user.name
    }

@router.post("/sso/google-mock", response_model=Token)
def google_sso_mock(sso_data: dict, db: Session = Depends(get_db)):
    """
    Simulates Google Single Sign-On (SSO) login.
    If the email exists, returns a token. Otherwise, automatically creates a new profile.
    Reads optional 'role' (default 'student') from body.
    """
    email = sso_data.get("email")
    name = sso_data.get("name")
    role = sso_data.get("role", "student")
    
    if not email:
        raise HTTPException(status_code=400, detail="El correo de Google es obligatorio")
        
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Create a new profile with the requested role
        hashed = hash_password("sso-dummy-password-12345")
        user = User(
            email=email,
            password_hash=hashed,
            name=name or email.split("@")[0],
            role=role
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        
    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "name": user.name
    }

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
