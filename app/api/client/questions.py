
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import base as schemas
from app.services import question_service

router = APIRouter(prefix="/api/client", tags=["Client - Questions"])

@router.get("/question-type/{type_id}")
async def get_question_type_title(
    type_id: uuid.UUID,
    db: Session = Depends(get_db),
):

    try:
        title = question_service.get_question_type_title(db, type_id)
        return {"title": title}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/question/{question_id}/type")
async def get_type_by_question_id(
    question_id: uuid.UUID,
    db: Session = Depends(get_db),
):

    try:
        title = question_service.get_type_by_question_id(db, question_id)
        return {"title": title}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/questions/ids")
async def get_all_question_ids(db: Session = Depends(get_db)):

    try:
        return question_service.get_active_question_ids(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/questions/{answer_id}/subquestion", response_model=List[schemas.QuestionForClient])
async def get_subquestions_by_answer(
    answer_id: uuid.UUID,
    db: Session = Depends(get_db)
):

    try:
        return question_service.get_subquestions_by_answer(db, answer_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/questions/{question_id}/subquestion/text", response_model=List[schemas.QuestionForClient])
async def get_subquestions_by_text(
    question_id: uuid.UUID,
    value: str = Query(""),
    db: Session = Depends(get_db)
):

    try:
        return question_service.get_subquestions_by_text(db, question_id, value)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/specification/questions/{specifications_session_id}",
    response_model=List[schemas.QuestionForClient],
)
async def get_session_questions(
    specifications_session_id: uuid.UUID,
    db: Session = Depends(get_db),
):

    try:
        return question_service.get_session_questions(db, specifications_session_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
