
import uuid
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.core import models, security
from app.schemas import base as schemas
from app.core.database import get_db, SessionLocal
from app.services import session_service
from app.rbac.dependencies import get_current_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/client", tags=["Client - Sessions"])

@router.post("/specification/specifications_session", response_model=schemas.SessionResponse)
async def create_session(
    session_data: schemas.SessionCreate,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(security.get_current_client_user_optional),
):

    try:
        return session_service.create_new_session(db, session_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception(f"Error in create_session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@router.get("/specification/sessions",
            dependencies=[Depends(get_current_admin)])
async def get_all_sessions_with_pdfs(db: Session = Depends(get_db)):

    try:
        return session_service.get_all_sessions_for_admin(db)
    except Exception as e:
        logger.exception(f"Error in get_all_sessions_with_pdfs: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/my-sessions")
async def get_my_sessions(
    current_user: models.User = Depends(security.get_current_client_user),
    db: Session = Depends(get_db)
):

    try:
        return session_service.get_user_sessions(db, current_user.id)
    except Exception as e:
        logger.exception(f"Error in get_my_sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/sessions/by-email")
async def get_sessions_by_email(email: str, db: Session = Depends(get_db)):

    sessions = (
        db.query(models.ClientSpecificationSession.id)
        .filter(models.ClientSpecificationSession.client_email == email)
        .order_by(models.ClientSpecificationSession.started_at.desc())
        .all()
    )
    return [str(row.id) for row in sessions]

@router.get("/specification/sessions/{session_id}/details")
async def get_session_details(
    session_id: uuid.UUID,
    db: Session = Depends(get_db)
):

    try:
        return session_service.get_session_details(db, session_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in get_session_details: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/specification/answers")
async def submit_answers(
    request: schemas.AnswersSubmit,
    db: Session = Depends(get_db)
):

    try:
        return session_service.submit_answers(db, request.specifications_session_id, request.answers)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in submit_answers: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.post("/specification/generate")
async def generate_specification(
    request: schemas.GenerateRequestBySpecId,
    db: Session = Depends(get_db),
):

    session = db.query(models.ClientSpecificationSession).filter_by(id=request.specifications_session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:

        session_service.generate_pdf_background_task(SessionLocal, session.id)
        

        db.refresh(session)
        

        return session_service.get_session_status(db, session.id)

    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/specification/analysis/{session_id}")
async def get_session_analysis_data(
    session_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    try:
        return session_service.get_session_details(db, session_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in get_session_analysis_data: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/specification/status/{session_id}")
async def get_specification_status(
    session_id: uuid.UUID,
    db: Session = Depends(get_db)
):

    try:
        return session_service.get_session_status(db, session_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in get_specification_status: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
