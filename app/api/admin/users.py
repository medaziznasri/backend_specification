from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.rbac.dependencies import get_current_admin
from app.core import models

router = APIRouter(prefix="/api/admin", tags=["Admin - Users & Stats"])


@router.get("/users")
def list_users(db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    users = db.query(models.User).order_by(models.User.created_at.desc()).all()
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "session_count": len(u.sessions),
        }
        for u in users
    ]


@router.patch("/users/{user_id}/deactivate")
def deactivate_user(user_id: int, db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    user.is_active = False
    db.commit()
    return {"success": True}


@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    db.delete(user)
    db.commit()
    return {"success": True}


@router.get("/stats")
def get_stats(db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    total_users = db.query(func.count(models.User.id)).scalar() or 0
    total_sessions = db.query(func.count(models.ClientSpecificationSession.id)).scalar() or 0
    completed_sessions = (
        db.query(func.count(models.ClientSpecificationSession.id))
        .filter(models.ClientSpecificationSession.completed_at.isnot(None))
        .scalar() or 0
    )
    total_project_types = (
        db.query(func.count(models.ProjectType.id))
        .filter(models.ProjectType.status == "active")
        .scalar() or 0
    )
    total_categories = (
        db.query(func.count(models.Category.id))
        .filter(models.Category.status == "active")
        .scalar() or 0
    )
    return {
        "total_users": total_users,
        "total_sessions": total_sessions,
        "completed_sessions": completed_sessions,
        "total_project_types": total_project_types,
        "total_categories": total_categories,
    }
