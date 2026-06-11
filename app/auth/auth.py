import os
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core import models
from app.schemas import base as schemas
from app.core import security as pwd_logic
from app.core.database import get_db

logger = logging.getLogger(__name__)

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


# ── Password reset ──────────────────────────────────────────────────────
# Where the reset link points (the deployed frontend). Falls back to the
# first ALLOWED_ORIGINS entry, then localhost.
FRONTEND_URL = (
    os.getenv("FRONTEND_URL")
    or (os.getenv("ALLOWED_ORIGINS", "").split(",")[0].strip() if os.getenv("ALLOWED_ORIGINS") else "")
    or "http://localhost:5173"
)


def _send_reset_email(to_email: str, reset_url: str) -> bool:
    """Send the reset link by email. Returns False if SMTP isn't configured
    or the send fails (the caller decides what to do)."""
    import smtplib, ssl
    from email.message import EmailMessage

    host = (os.getenv("SMTP_HOST") or "").strip()
    port = (os.getenv("SMTP_PORT") or "").strip()
    user = (os.getenv("SMTP_USER") or "").strip()
    # App passwords are shown with spaces for readability but must be sent
    # without them — strip all whitespace so a pasted value still works.
    password = "".join((os.getenv("SMTP_PASSWORD") or "").split())
    sender = (os.getenv("SMTP_FROM") or user or "").strip()
    if not (host and port and user and password):
        return False
    try:
        msg = EmailMessage()
        msg["Subject"] = "Réinitialisation de votre mot de passe"
        msg["From"] = sender
        msg["To"] = to_email
        msg.set_content(
            "Vous avez demandé à réinitialiser votre mot de passe.\n\n"
            f"Cliquez sur ce lien (valable 30 minutes) :\n{reset_url}\n\n"
            "Si vous n'êtes pas à l'origine de cette demande, ignorez cet email."
        )
        msg.add_alternative(
            f"""\
<div style="font-family:Arial,Helvetica,sans-serif;max-width:480px;margin:0 auto;padding:24px;color:#1e293b">
  <h2 style="margin:0 0 8px;font-size:20px">Réinitialisation du mot de passe</h2>
  <p style="color:#475569;line-height:1.6">
    Vous avez demandé à réinitialiser votre mot de passe. Cliquez sur le bouton
    ci-dessous pour en choisir un nouveau. Ce lien est valable <strong>30 minutes</strong>.
  </p>
  <p style="text-align:center;margin:28px 0">
    <a href="{reset_url}" style="background:#4f46e5;color:#fff;text-decoration:none;
       padding:12px 28px;border-radius:10px;font-weight:bold;display:inline-block">
      Réinitialiser mon mot de passe
    </a>
  </p>
  <p style="color:#94a3b8;font-size:12px;line-height:1.6">
    Si le bouton ne fonctionne pas, copiez ce lien dans votre navigateur :<br>
    <a href="{reset_url}" style="color:#4f46e5;word-break:break-all">{reset_url}</a>
  </p>
  <p style="color:#94a3b8;font-size:12px">
    Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.
  </p>
</div>""",
            subtype="html",
        )
        ctx = ssl.create_default_context()
        with smtplib.SMTP(host, int(port)) as server:
            server.starttls(context=ctx)
            server.login(user, password)
            server.send_message(msg)
        return True
    except Exception as e:
        logger.error(f"Failed to send reset email to {to_email}: {e}")
        return False


@router.post("/forgot-password")
def forgot_password(payload: schemas.ForgotPasswordRequest, db: Session = Depends(get_db)):
    # Always return the same message so we don't reveal which emails exist.
    generic = {"message": "Si un compte existe pour cet email, un lien de réinitialisation a été envoyé."}

    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user:
        return generic

    token = pwd_logic.create_reset_token({"sub": str(user.id), "email": user.email})
    reset_url = f"{FRONTEND_URL.rstrip('/')}/reset-password?token={token}"

    sent = _send_reset_email(user.email, reset_url)
    if not sent:
        logger.warning(
            "Reset email NOT sent for %s (SMTP not configured or send failed).", user.email
        )
        # Only ever expose the link when explicitly running in dev/demo mode.
        # In production this stays secret — the link goes to the inbox only.
        if os.getenv("EXPOSE_RESET_LINK", "false").lower() in ("true", "1", "yes"):
            return {**generic, "reset_url": reset_url}

    return generic


@router.post("/reset-password")
def reset_password(payload: schemas.ResetPasswordRequest, db: Session = Depends(get_db)):
    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Le mot de passe doit contenir au moins 8 caractères.")

    try:
        data = pwd_logic.decode_access_token(payload.token)
    except HTTPException:
        raise HTTPException(status_code=400, detail="Lien invalide ou expiré.")

    if data.get("type") != "reset":
        raise HTTPException(status_code=400, detail="Lien invalide.")

    user_id = data.get("sub")
    user = None
    if user_id:
        try:
            user = db.query(models.User).filter(models.User.id == int(user_id)).first()
        except (ValueError, TypeError):
            user = None
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")

    user.hashed_password = pwd_logic.get_password_hash(payload.password)
    db.commit()
    return {"message": "Mot de passe réinitialisé avec succès."}

