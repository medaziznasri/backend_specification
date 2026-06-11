from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core import models
from app.core.database import get_db
from app.core.security import decode_access_token, oauth2_scheme
import uuid

def get_current_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    sub = payload.get("sub")
    role = payload.get("role")
    if not sub or role != "admin":
        raise HTTPException(status_code=401, detail="Invalid token payload or not an admin")
    

    admin = None
    try:
        admin_id = uuid.UUID(sub)
        admin = db.query(models.AdminUser).filter(models.AdminUser.id == admin_id).first()
    except (ValueError, TypeError):
        admin = db.query(models.AdminUser).filter(models.AdminUser.email == sub).first()
    
    if not admin:
        raise HTTPException(status_code=401, detail="Admin user not found")
    return admin
def check_permission(action: str, resource: str):
    def permission_checker(admin: models.AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):

        permission_exists = db.query(models.Permission).join(
            models.RolePermission
        ).filter(
            models.RolePermission.role_id == admin.role_id,
            models.Permission.action == action,
            models.Permission.resource == resource
        ).first()
        
        if not permission_exists:
            raise HTTPException(status_code=403, detail="Access denied")
        return True
    return permission_checker
