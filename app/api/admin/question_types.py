import uuid
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.rbac.dependencies import check_permission
from app.schemas import admin as schemas_admin
from app.core import models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin - Question Types"])

@router.get("/question-types", 
             dependencies=[Depends(check_permission("read", "question"))])
async def list_question_types(db: Session = Depends(get_db)):

    return db.query(models.QuestionType).all()

@router.post("/question-types", 
               status_code=status.HTTP_201_CREATED,
               dependencies=[Depends(check_permission("create", "question"))])
async def create_question_type(data: schemas_admin.QuestionTypeCreate, db: Session = Depends(get_db)):

    try:
        new_type = models.QuestionType(
            id=uuid.uuid4(),
            title=data.title,
            description=data.description
        )
        db.add(new_type)
        db.commit()
        db.refresh(new_type)
        return {"success": True, "message": "Type de question créé", "data": new_type}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/question-types/{id}", 
               dependencies=[Depends(check_permission("update", "question"))])
async def update_question_type(id: uuid.UUID, updates: schemas_admin.QuestionTypeUpdate, db: Session = Depends(get_db)):

    qt = db.query(models.QuestionType).filter(models.QuestionType.id == id).first()
    if not qt:
        raise HTTPException(status_code=404, detail="Type de question non trouvé")
    
    data = updates.model_dump(exclude_unset=True)
    for key, value in data.items():
        if hasattr(qt, key):
            setattr(qt, key, value)
    
    try:
        db.commit()
        db.refresh(qt)
        return {"success": True, "message": "Type de question mis à jour", "data": qt}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/question-types/{id}", 
                 dependencies=[Depends(check_permission("delete", "question"))])
async def delete_question_type(id: uuid.UUID, db: Session = Depends(get_db)):

    qt = db.query(models.QuestionType).filter(models.QuestionType.id == id).first()
    if not qt:
        raise HTTPException(status_code=404, detail="Type de question non trouvé")
    
    try:
        db.delete(qt)
        db.commit()
        return {"success": True, "message": "Type de question supprimé"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
