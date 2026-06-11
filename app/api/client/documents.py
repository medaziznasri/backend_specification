
import os
import json
import uuid
import logging
from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import or_, text
from sqlalchemy.orm import Session

from app.core import models
from app.core import security
from app.core.security import get_current_client_user, oauth2_scheme

logger = logging.getLogger(__name__)
from app.schemas import base as schemas
from app.core.database import get_db
from app.services.pdf_generator import generate_physical_pdf

router = APIRouter(prefix="/api/client", tags=["Client - Documents"])

@router.get("/specification/documents/{specifications_session_id}")
async def list_generated_documents(
        specifications_session_id: uuid.UUID,
            db: Session = Depends(get_db),
        ):
        docs = (
                db.query(models.GeneratedSpecificationDocument)
                .filter(models.GeneratedSpecificationDocument.session_id == specifications_session_id)
                .order_by(models.GeneratedSpecificationDocument.created_at.desc())
                .all()
            )
        return [
                {
                    "id": str(d.id),
                    "created_at": d.created_at.isoformat() if d.created_at else None,
                    "pdf_url": f"/files/{os.path.basename(d.file_path)}",
                    "content_summary": d.content_summary,
                }
                for d in docs
            ]

