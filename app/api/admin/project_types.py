import uuid
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.rbac.dependencies import check_permission, get_current_admin
from app.schemas import base as schemas
from app.core import models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin - Project Types"])

class ProjectTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

def _serialize_project_type(pt: models.ProjectType) -> dict:
    return {
        "id": str(pt.id),
        "name": pt.name,
        "description": pt.description,
        "status": pt.status,
        "created_at": pt.created_at.isoformat() if pt.created_at else None,
    }

@router.get("/project-types",
            dependencies=[Depends(check_permission("read", "category"))])
async def admin_list_project_types(db: Session = Depends(get_db)):

    pts = db.query(models.ProjectType).order_by(models.ProjectType.created_at.asc()).all()
    return [_serialize_project_type(pt) for pt in pts]

@router.post("/project-types",
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(check_permission("create", "category"))])
async def admin_create_project_type(
    data: schemas.ProjectTypeCreate,
    db: Session = Depends(get_db),
    current_admin: models.AdminUser = Depends(get_current_admin)
):

    try:
        new_project_type = models.ProjectType(
            id=uuid.uuid4(),
            name=data.name,
            description=data.description,
            status="active"
        )
        db.add(new_project_type)
        db.commit()
        db.refresh(new_project_type)
        return {"message": "Project type created", "id": str(new_project_type.id), "data": _serialize_project_type(new_project_type)}
    except Exception as e:
        db.rollback()
        logger.error(f"Error in admin_create_project_type: {e}")
        raise HTTPException(status_code=500, detail="Database commit failed")

@router.patch("/project-types/{id}",
              dependencies=[Depends(check_permission("update", "category"))])
async def admin_update_project_type(
    id: uuid.UUID,
    updates: ProjectTypeUpdate,
    db: Session = Depends(get_db),
):

    pt = db.query(models.ProjectType).filter(models.ProjectType.id == id).first()
    if not pt:
        raise HTTPException(status_code=404, detail="Type de projet non trouvé")

    data = updates.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No updates provided")

    if "status" in data:
        data["status"] = data["status"].lower()

    for key, value in data.items():
        if hasattr(pt, key):
            setattr(pt, key, value)

    try:
        db.commit()
        db.refresh(pt)
        return {"success": True, "message": "Type de projet mis à jour", "data": _serialize_project_type(pt)}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/project-types/{id}",
               dependencies=[Depends(check_permission("delete", "category"))])
async def admin_delete_project_type(
    id: uuid.UUID,
    db: Session = Depends(get_db),
):

    pt = db.query(models.ProjectType).filter(models.ProjectType.id == id).first()
    if not pt:
        raise HTTPException(status_code=404, detail="Type de projet non trouvé")

    try:
        db.query(models.ClientSpecificationSession).filter(
            models.ClientSpecificationSession.project_type_id == id
        ).update({models.ClientSpecificationSession.project_type_id: None}, synchronize_session=False)
        db.query(models.Question).filter(
            models.Question.project_type_id == id
        ).update({models.Question.project_type_id: None}, synchronize_session=False)
        db.delete(pt)
        db.commit()
        return {"success": True, "message": "Type de projet supprimé"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
