import uuid
import json
import logging
import re as re_module
from typing import List, Optional, Any
from sqlalchemy import or_, text
from sqlalchemy.orm import Session, joinedload, selectinload
from fastapi import HTTPException

def _parse_options(raw) -> list:

    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, list) else []
        except (json.JSONDecodeError, ValueError):
            return []
    return []

from app.core import models
from app.schemas import base as schemas
from app.core.cache import cache

logger = logging.getLogger(__name__)

def get_question_type_title(db: Session, type_id: uuid.UUID) -> str:

    cache_key = f"q_type_{type_id}"
    cached_title = cache.get(cache_key)
    if cached_title:
        return cached_title

    q_type = db.query(models.QuestionType).filter_by(id=type_id).first()
    if not q_type:
        raise HTTPException(status_code=404, detail="Question type not found")
    
    cache.set(cache_key, q_type.title)
    return q_type.title

def get_type_by_question_id(db: Session, question_id: uuid.UUID) -> str:

    result = db.query(models.QuestionType.title).join(
        models.Question, models.Question.type_id == models.QuestionType.id
    ).filter(models.Question.id == question_id).first()
    
    if not result:
        q_exists = db.query(models.Question).filter_by(id=question_id).first()
        if not q_exists:
            raise HTTPException(status_code=404, detail="Question not found")
        return q_exists.answer_type
        
    return result[0]

def get_active_question_ids(db: Session) -> List[str]:

    result = db.query(models.Question.id).filter(models.Question.status == "active").all()
    return [str(row[0]) for row in result]

def _format_question_for_client(question: models.Question, cond: Optional[models.QuestionCondition] = None) -> dict:

    cat_name = question.category.name if question.category else "Unknown"
    is_gen = question.category.is_general if question.category else False
    

    
    return {
        "id": str(question.id),
        "label": question.label,
        "description": question.description,
        "answer_type": question.answer_type,
        "options": _parse_options(question.options),
        "question_options": [
            {
                "id": str(o.id),
                "option_text": o.option_text,
                "display_order": o.display_order
            } for o in question.question_options
        ],
        "is_required": cond.is_required if cond else question.is_required,
        "category_id": str(question.category_id),
        "category_name": f"[GENERAL] {cat_name}" if is_gen else cat_name,
        "display_order": question.display_order,
        "has_subquestions": len(question.trigger_conditions) > 0,
        "question_type": {
            "id": str(question.question_type.id),
            "title": question.question_type.title,
            "description": question.question_type.description
        } if question.question_type else None
    }

def get_subquestions_by_answer(db: Session, answer_id: uuid.UUID) -> List[dict]:

    conditions = db.query(models.QuestionCondition).filter_by(
        trigger_option_id=answer_id
    ).order_by(models.QuestionCondition.priority.asc()).all()
    
    if not conditions:
        return []
        
    sub_question_ids = [c.question_id for c in conditions]
    
    questions = (
        db.query(models.Question)
        .options(
            joinedload(models.Question.category),
            joinedload(models.Question.question_type),
            selectinload(models.Question.question_options),
            selectinload(models.Question.trigger_conditions)
        )
        .filter(
            models.Question.id.in_(sub_question_ids),
            models.Question.status == "active"
        )
        .all()
    )
    

    cond_map = {c.question_id: c for c in conditions}
    
    return [_format_question_for_client(q, cond_map.get(q.id)) for q in questions]

def get_subquestions_by_text(db: Session, question_id: uuid.UUID, value: str) -> List[dict]:

    conditions = (
        db.query(models.QuestionCondition)
        .filter(
            models.QuestionCondition.trigger_question_id == question_id,
            models.QuestionCondition.trigger_option_id == None
        )
        .order_by(models.QuestionCondition.priority.asc())
        .all()
    )

    if not conditions:
        return []

    def matches(condition: models.QuestionCondition, text_val: str) -> bool:
        if condition.trigger_value is None:
            return True
            
        tv = condition.trigger_value or ""
        op = (condition.trigger_value_operator or "contains").lower()
        t = (text_val or "").lower()
        v = tv.lower()
        if op == "equals": return t == v
        elif op == "starts_with": return t.startswith(v)
        elif op == "ends_with": return t.endswith(v)
        elif op == "regex":
            try: return bool(re_module.search(tv, text_val, re_module.IGNORECASE))
            except Exception: return False
        else: return v in t

    triggered_conditions = [c for c in conditions if matches(c, value)]
    if not triggered_conditions:
        return []

    sub_question_ids = list({c.question_id for c in triggered_conditions})
    
    questions = (
        db.query(models.Question)
        .options(
            joinedload(models.Question.category),
            joinedload(models.Question.question_type),
            selectinload(models.Question.question_options),
            selectinload(models.Question.trigger_conditions)
        )
        .filter(
            models.Question.id.in_(sub_question_ids),
            models.Question.status == "active"
        )
        .all()
    )
    
    cond_map = {c.question_id: c for c in triggered_conditions}
    return [_format_question_for_client(q, cond_map.get(q.id)) for q in questions]

def get_session_questions(db: Session, session_id: uuid.UUID) -> List[dict]:

    session = db.query(models.ClientSpecificationSession).filter_by(id=session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session_categories = db.query(models.SessionCategory).filter_by(session_id=session_id).all()
    category_ids = [sc.category_id for sc in session_categories]
    project_type_id = session.project_type_id

    sub_question_ids_subquery = db.query(models.QuestionCondition.question_id).scalar_subquery()

    questions = (
        db.query(models.Question)
        .join(models.Category, models.Question.category_id == models.Category.id)
        .options(
            joinedload(models.Question.category),
            joinedload(models.Question.question_type),
            selectinload(models.Question.question_options),
            selectinload(models.Question.trigger_conditions)
        )
        .filter(
            or_(
                models.Category.is_general == True,
                models.Category.id.in_(category_ids) if category_ids else False
            ),
            models.Category.status.in_(["active", "ACTIVE"]),
            models.Question.status == "active",
            ~models.Question.id.in_(sub_question_ids_subquery),

            or_(
                models.Question.project_type_id == None,
                models.Question.project_type_id == project_type_id
            )
        )
        .order_by(
            models.Category.is_general.desc(),
            models.Category.name.asc(),
            models.Question.display_order.asc()
        )
        .all()
    )

    return [_format_question_for_client(q) for q in questions]
