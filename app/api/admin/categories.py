import uuid
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.rbac.dependencies import check_permission, get_current_admin
from app.schemas import admin as schemas_admin
from app.schemas import base as schemas
from app.core import models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin - Categories"])

def _serialize_category(c: models.Category, question_count: int = 0) -> dict:

    return {
        "id": str(c.id),
        "name": c.name,
        "description": c.description,
        "status": c.status,
        "is_general": c.is_general,
        "question_count": question_count,
        "project_type_id": str(c.project_type_id) if c.project_type_id else None,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }

@router.get("/categories",
            dependencies=[Depends(check_permission("read", "category"))])
async def list_all_categories_admin(db: Session = Depends(get_db)):

    from sqlalchemy import func
    

    results = (
        db.query(models.Category, func.count(models.Question.id).label("q_count"))
        .outerjoin(models.Question, 
                   (models.Question.category_id == models.Category.id) & 
                   (models.Question.status == "active"))
        .group_by(models.Category.id)
        .order_by(
            models.Category.is_general.desc(),
            models.Category.name.asc()
        )
        .all()
    )
    
    return [_serialize_category(cat, q_count) for cat, q_count in results]

@router.post("/categories", 
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(check_permission("create", "category"))])
async def create_category(category_data: schemas_admin.CategoryCreate, db: Session = Depends(get_db)):

    try:
        new_category = models.Category(
            id=uuid.uuid4(),
            name=category_data.name,
            description=category_data.description,
            is_general=category_data.is_general,
            project_type_id=category_data.project_type_id,
            status="active"
        )
        db.add(new_category)
        db.commit()
        db.refresh(new_category)
        return {"success": True, "message": "Catégorie créée avec succès", "data": _serialize_category(new_category)}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/categories/{id}", 
              dependencies=[Depends(check_permission("update", "category"))])
async def update_category(id: uuid.UUID, updates: schemas_admin.CategoryUpdate, db: Session = Depends(get_db)):

    category = db.query(models.Category).filter(models.Category.id == id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Catégorie non trouvée")
        
    data = updates.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    if "status" in data and data["status"]:
        data["status"] = data["status"].lower()
    
    for key, value in data.items():
        if hasattr(category, key):
            setattr(category, key, value)
    
    try:
        db.commit()
        db.refresh(category)
        return {"success": True, "message": "Catégorie mise à jour", "data": _serialize_category(category)}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/categories/{id}", 
               dependencies=[Depends(check_permission("delete", "category"))])
async def delete_category(id: uuid.UUID, db: Session = Depends(get_db)):

    category = db.query(models.Category).filter(models.Category.id == id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Catégorie non trouvée")
    
    category.status = "archived"
    try:
        db.commit()
        return {"success": True, "message": "Catégorie archivée"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
