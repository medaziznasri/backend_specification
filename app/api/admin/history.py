import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload, aliased

from app.core.database import get_db
from app.rbac.dependencies import check_permission
from app.core import models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin - History"])

@router.get("/reassignment-history", 
            dependencies=[Depends(check_permission("read", "question"))])
async def get_reassignment_history(db: Session = Depends(get_db)):

    try:

        PrevCat = aliased(models.Category)
        NewCat = aliased(models.Category)
        

        history = (
            db.query(models.QuestionCategoryHistory)
            .options(
                joinedload(models.QuestionCategoryHistory.question),
                joinedload(models.QuestionCategoryHistory.previous_category.of_type(PrevCat)),
                joinedload(models.QuestionCategoryHistory.new_category.of_type(NewCat))
            )
            .order_by(models.QuestionCategoryHistory.timestamp.desc())
            .all()
        )
        
        return [
            {
                "id": str(h.id),
                "question_label": h.question.label if h.question else "Inconnue",
                "old_category_name": h.previous_category.name if h.previous_category else None,
                "new_category_name": h.new_category.name if h.new_category else None,
                "action": h.action.value if hasattr(h.action, 'value') else str(h.action),
                "timestamp": h.timestamp.isoformat()
            }
            for h in history
        ]
    except Exception as e:
        logger.error(f"Error fetching reassignment history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
