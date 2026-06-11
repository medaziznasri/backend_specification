
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core import models
from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/client", tags=["Client - Categories"])

@router.get("/categories")
async def get_categories(db: Session = Depends(get_db)):

    try:
        categories = db.query(models.Category).filter(models.Category.status == 'active').all()
        return [
            {
                "id": str(c.id),
                "name": c.name,
                "description": c.description,
                "status": c.status,
                "is_general": c.is_general,
                "project_type_id": str(c.project_type_id) if c.project_type_id else None,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            } for c in categories
        ]
    except Exception as e:
        logger.error(f"Error in get_categories: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
