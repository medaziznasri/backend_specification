
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core import models
from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/client", tags=["Client - Project Types"])

@router.get("/project-types")
async def get_project_types(db: Session = Depends(get_db)):

    try:
        project_types = db.query(models.ProjectType).filter(models.ProjectType.status == 'active').all()
        return [
            {
                "id": str(pt.id),
                "name": pt.name,
                "description": pt.description,
                "status": pt.status,
                "created_at": pt.created_at.isoformat() if pt.created_at else None,
            } for pt in project_types
        ]
    except Exception as e:
        logger.error(f"Error in get_project_types: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
