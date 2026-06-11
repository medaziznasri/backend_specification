import os
from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core import models
from app.schemas import base as schemas
from app.core import security as pwd_logic
from app.core.database import get_db

router = APIRouter(tags=["Authentication"])

# Cross-site cookies (Vercel frontend ↔ Render backend on different domains)
# require SameSite=None + Secure=True. Set these env vars in production:
#   COOKIE_SECURE=true   COOKIE_SAMESITE=none
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() in ("true", "1", "yes")
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax")

@router.post("/register", response_model=schemas.UserOut)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):

    user_exists = db.query(models.User).filter(models.User.email == user_in.email).first()
    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Cet email est déjà enregistré."
        )

    new_user = models.User(
        email=user_in.email,
        hashed_password=pwd_logic.get_password_hash(user_in.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login")
def login(
    response: Response,
    role: str = Form("client"),
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):

    if role == "admin":
        admin = db.query(models.AdminUser).filter(models.AdminUser.email == form_data.username).first()
        if admin and pwd_logic.verify_password(form_data.password, admin.password_hash):
            sub = str(admin.id)
            current_role = "admin"
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Identifiants admin invalides ou compte inexistant",
                headers={"WWW-Authenticate": "Bearer"},
            )
    else:

        user = db.query(models.User).filter(models.User.email == form_data.username).first()
        if user and pwd_logic.verify_password(form_data.password, user.hashed_password):
            sub = str(user.id)
            current_role = "client"
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Identifiants client invalides ou compte inexistant",
                headers={"WWW-Authenticate": "Bearer"},
            )

    access_token = pwd_logic.create_access_token(data={"sub": sub, "role": current_role})
    refresh_token = pwd_logic.create_refresh_token(data={"sub": sub, "role": current_role})

    response.set_cookie(
        key="refreshToken",
        value=refresh_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=7 * 24 * 60 * 60
    )

    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "role": current_role, 
        "user_id": sub
    }

@router.post("/refresh")
def refresh_token(db: Session = Depends(get_db), refreshToken: str = Cookie(None)):

    if not refreshToken:
        raise HTTPException(status_code=401, detail="Refresh token manquant")
    
    try:
        payload = pwd_logic.decode_access_token(refreshToken)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Token de type invalide")
        
        sub = payload.get("sub")
        role = payload.get("role")
        
        if not sub or not role:
            raise HTTPException(status_code=401, detail="Payload invalide")
            

        new_access_token = pwd_logic.create_access_token(data={"sub": sub, "role": role})
        

        user_info = None
        if role == "admin":
            admin = db.query(models.AdminUser).filter(models.AdminUser.id == sub).first()
            if admin:
                user_info = {
                    "user_id": str(admin.id),
                    "role": "admin",
                    "email": admin.email,
                    "firstname": "Admin",
                    "lastname": admin.username
                }
        else:
            user = db.query(models.User).filter(models.User.id == sub).first()
            if user:
                full_name = getattr(user, 'full_name', '') or ''
                parts = full_name.split(' ', 1)
                user_info = {
                    "user_id": str(user.id),
                    "role": getattr(user, 'role', 'client') or 'client',
                    "email": user.email,
                    "firstname": parts[0] if len(parts) > 0 and parts[0] else None,
                    "lastname": parts[1] if len(parts) > 1 and parts[1] else None
                }
        
        if not user_info:
            raise HTTPException(status_code=404, detail="Utilisateur lié au token non trouvé")

        return {
            "access_token": new_access_token, 
            "token_type": "bearer",
            "user": user_info
        }
        
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=401, detail="Refresh token invalide ou expiré")

@router.post("/logout")
def logout(response: Response):

    response.delete_cookie("refreshToken", secure=COOKIE_SECURE, samesite=COOKIE_SAMESITE)
    return {"detail": "Logged out"}

@router.get("/me", response_model=schemas.UserProfile)
def whoami(token: str = Depends(pwd_logic.oauth2_scheme), db: Session = Depends(get_db)):

    payload = pwd_logic.decode_access_token(token)
    user_id = payload.get("sub")
    role = payload.get("role")

    if not user_id or not role:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    if role == "admin":
        admin = db.query(models.AdminUser).filter(models.AdminUser.id == user_id).first()
        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found")
        return {
            "user_id": str(admin.id),
            "role": "admin",
            "email": admin.email,
            "firstname": "Admin",
            "lastname": admin.username
        }

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    full_name = getattr(user, 'full_name', '') or ''
    parts = full_name.split(' ', 1)
    firstname = parts[0] if len(parts) > 0 and parts[0] else None
    lastname = parts[1] if len(parts) > 1 and parts[1] else None

    return {
        "user_id": str(user.id),
        "role": getattr(user, 'role', 'client') or 'client',
        "email": user.email,
        "firstname": firstname,
        "lastname": lastname
    }
 
