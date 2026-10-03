from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app import models, schemas
from backend.app.auth import hash_password, verify_password, create_access_token, get_current_user
from backend.app.audit import log_audit

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])

@router.post("/register", response_model=schemas.TokenResponse)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if user email already exists
    existing = db.query(models.Usuario).filter(models.Usuario.correo == user_data.correo).first()
    if existing:
        raise HTTPException(status_code=400, detail="El correo electrónico ya se encuentra registrado.")

    hashed_pw = hash_password(user_data.contrasena)
    new_user = models.Usuario(
        nombre=user_data.nombre,
        correo=user_data.correo,
        contrasena=hashed_pw,
        rol=user_data.rol
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    log_audit(
        db=db,
        accion="REGISTRO_DOCENTE",
        tabla="usuarios",
        registro_id=new_user.id,
        usuario_id=new_user.id,
        datos_nuevos={"nombre": new_user.nombre, "correo": new_user.correo, "rol": new_user.rol}
    )

    token = create_access_token({"sub": str(new_user.id), "rol": new_user.rol, "email": new_user.correo})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": new_user
    }

@router.post("/login", response_model=schemas.TokenResponse)
def login(login_data: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.Usuario).filter(models.Usuario.correo == login_data.correo).first()
    if not user or not verify_password(login_data.contrasena, user.contrasena):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas (correo o contraseña)"
        )

    token = create_access_token({"sub": str(user.id), "rol": user.rol, "email": user.correo})
    
    log_audit(
        db=db,
        accion="LOGIN",
        tabla="usuarios",
        registro_id=user.id,
        usuario_id=user.id
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=schemas.UserOut)
def get_me(current_user: models.Usuario = Depends(get_current_user)):
    return current_user
