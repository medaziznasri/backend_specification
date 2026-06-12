
import os
import json
import uuid
import logging
from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response
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
                    "pdf_url": f"/api/client/specification/pdf/{d.id}",
                    "content_summary": d.content_summary,
                }
                for d in docs
            ]


@router.get("/specification/pdf/{doc_id}")
def serve_pdf(doc_id: uuid.UUID, db: Session = Depends(get_db)):
    """Serve a generated PDF from the database (survives Render restarts).
    Falls back to disk for any legacy record that predates DB storage."""
    doc = (
        db.query(models.GeneratedSpecificationDocument)
        .filter(models.GeneratedSpecificationDocument.id == doc_id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document non trouvé")

    data = doc.file_data
    if not data and doc.file_path and os.path.exists(doc.file_path):
        with open(doc.file_path, "rb") as f:
            data = f.read()
    if not data:
        raise HTTPException(status_code=404, detail="Fichier PDF introuvable")

    filename = os.path.basename(doc.file_path) if doc.file_path else f"spec_{doc_id}.pdf"
    return Response(
        content=bytes(data),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )

