import json
import uuid
import logging
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.database import get_db
from app.rbac.dependencies import check_permission, get_current_admin
from app.schemas import admin as schemas_admin
from app.schemas import base as schemas
from app.core import models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin - Questions"])

def _serialize_question(q: models.Question) -> dict:

    cat_name = q.category.name if q.category else None
    is_gen = q.category.is_general if q.category else False

    sub_count = len(q.trigger_conditions) if q.trigger_conditions else 0

    options_list = None
    if q.options:
        if isinstance(q.options, str):
            try:
                options_list = json.loads(q.options)
            except (json.JSONDecodeError, ValueError):
                options_list = [q.options]
        elif isinstance(q.options, list):
            options_list = q.options

    return {
        "id": str(q.id),
        "label": q.label,
        "description": q.description,
        "answer_type": q.answer_type,
        "options": options_list,
        "is_required": q.is_required,
        "category_id": str(q.category_id) if q.category_id else None,
        "category_name": f"[GÉNÉRAL] {cat_name}" if is_gen and cat_name else cat_name,
        "type_id": str(q.type_id) if q.type_id else None,
        "question_type": {
            "id": str(q.question_type.id),
            "title": q.question_type.title,
        } if q.question_type else None,
        "project_type_id": str(q.project_type_id) if q.project_type_id else None,
        "project_type": {
            "id": str(q.project_type.id),
            "name": q.project_type.name,
        } if q.project_type else None,
        "display_order": q.display_order,
        "status": q.status,
        "parent_question_id": str(q.parent_question_id) if q.parent_question_id else None,
        "sub_questions_count": sub_count,
        "conditions_count": len(q.conditions) if q.conditions else 0,
        "question_options": [
            {
                "id": str(o.id),
                "option_text": o.option_text,
                "display_order": o.display_order
            } for o in (q.question_options or [])
        ],
    }

@router.post("/questions", 
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(check_permission("create", "question"))])
async def create_question(question_data: schemas_admin.QuestionCreate, db: Session = Depends(get_db)):

    answer_type_fixed = question_data.answer_type.lower()
    
    if answer_type_fixed in ["multi_choice", "single_choice"] and not question_data.options:
        raise HTTPException(status_code=400, detail="Les types CHOICE nécessitent des options")
    
    try:

        new_question = models.Question(
            id=uuid.uuid4(),
            label=question_data.label,
            description=question_data.description,
            answer_type=answer_type_fixed,
            options=json.dumps(question_data.options) if question_data.options else None,
            is_required=question_data.is_required,
            category_id=question_data.category_id,
            type_id=question_data.type_id,
            project_type_id=question_data.project_type_id,
            display_order=question_data.display_order,
            status="active",
            parent_question_id=question_data.parent_question_id
        )
        db.add(new_question)
        

        if question_data.options and answer_type_fixed in ["multi_choice", "single_choice", "boolean"]:
            for i, opt_text in enumerate(question_data.options):
                db.add(models.QuestionOption(
                    id=uuid.uuid4(),
                    question_id=new_question.id,
                    option_text=opt_text,
                    display_order=i+1
                ))

        if question_data.parent_question_id:
            new_condition = models.QuestionCondition(
                id=uuid.uuid4(),
                question_id=new_question.id,
                trigger_question_id=question_data.parent_question_id,
                trigger_option_id=getattr(question_data, 'trigger_option_id', None),
                trigger_value=question_data.trigger_value,
                trigger_value_operator=question_data.trigger_value_operator or "contains",
                logical_operator="OR",
                priority=1,
                is_required=question_data.is_required
            )
            db.add(new_condition)

        db.commit()
        db.refresh(new_question)
        return {"success": True, "message": "Question créée avec succès", "data": {"id": str(new_question.id)}}
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating question: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/questions/{id}", 
             dependencies=[Depends(check_permission("update", "question"))])
async def update_question(id: uuid.UUID, updates: schemas_admin.QuestionUpdate, db: Session = Depends(get_db)):

    question = db.query(models.Question).filter(models.Question.id == id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    update_data = updates.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")
    

    if "answer_type" in update_data: update_data["answer_type"] = update_data["answer_type"].lower()
    if "status" in update_data: update_data["status"] = update_data["status"].lower()
    if "options" in update_data: update_data["options"] = json.dumps(update_data["options"])

    if update_data.get("status") == "archived":
        protected_labels = ["Main Problem Solved by the Project", "Target Users (End-customers, Staff, etc.)"]
        if any(label in question.label for label in protected_labels):
            raise HTTPException(
                status_code=400, 
                detail=f"Action impossible: La question '{question.label}' est indispensable."
            )

    if "category_id" in update_data:
        new_cat_id = update_data["category_id"]
        if str(new_cat_id) != str(question.category_id):
            db.add(models.QuestionCategoryHistory(
                id=uuid.uuid4(),
                question_id=question.id,
                previous_category_id=question.category_id,
                new_category_id=new_cat_id,
                action="REASSIGNED",
                timestamp=datetime.utcnow()
            ))

    for key, value in update_data.items():
        if hasattr(question, key):
            setattr(question, key, value)

    if ("options" in update_data or "answer_type" in update_data) and question.answer_type in ["multi_choice", "single_choice", "boolean"]:
        final_options_texts = []
        if question.answer_type == "boolean":
            final_options_texts = ["Oui", "Non"]
        elif "options" in update_data:
            final_options_texts = json.loads(update_data["options"]) if isinstance(update_data["options"], str) else update_data["options"]
        
        existing_options = db.query(models.QuestionOption).filter_by(question_id=question.id).order_by(models.QuestionOption.display_order.asc()).all()
        if [o.option_text for o in existing_options] != final_options_texts:
            db.query(models.QuestionOption).filter_by(question_id=question.id).delete()
            for i, opt_text in enumerate(final_options_texts):
                db.add(models.QuestionOption(id=uuid.uuid4(), question_id=question.id, option_text=opt_text, display_order=i+1))

    db.commit()
    db.refresh(question)
    return {"success": True, "message": "Update successful"}

@router.get("/questions", 
             dependencies=[Depends(check_permission("read", "question"))])
async def list_all_questions_admin(db: Session = Depends(get_db)):

    questions = (
        db.query(models.Question)
        .options(
            joinedload(models.Question.category),
            joinedload(models.Question.question_type),
            joinedload(models.Question.project_type),
            selectinload(models.Question.question_options),
            selectinload(models.Question.trigger_conditions),
            selectinload(models.Question.conditions),
        )
        .order_by(
            models.Question.display_order.asc(),
            models.Question.created_at.asc()
        )
        .all()
    )

    return [_serialize_question(q) for q in questions]

@router.get("/questions/tree",
            dependencies=[Depends(check_permission("read", "question"))])
async def get_questions_tree(db: Session = Depends(get_db)):

    questions = (
        db.query(models.Question)
        .options(
            joinedload(models.Question.category),
            joinedload(models.Question.question_type),
            joinedload(models.Question.project_type),
            selectinload(models.Question.question_options),
            selectinload(models.Question.trigger_conditions).options(
                joinedload(models.QuestionCondition.question)
            ),
            selectinload(models.Question.conditions),
        )
        .order_by(models.Question.display_order.asc())
        .all()
    )

    q_map = {q.id: q for q in questions}
    

    def build_subtree(q):
        serialized = _serialize_question(q)
        sub_questions = []
        for cond in (q.trigger_conditions or []):
            sub_q = q_map.get(cond.question_id)
            if sub_q:
                sub_serialized = build_subtree(sub_q)
                sub_serialized["trigger_condition"] = {
                    "id": str(cond.id),
                    "trigger_option_id": str(cond.trigger_option_id) if cond.trigger_option_id else None,
                    "trigger_value": cond.trigger_value,
                    "trigger_value_operator": cond.trigger_value_operator,
                    "is_required": cond.is_required,
                }
                sub_questions.append(sub_serialized)
        
        serialized["sub_questions"] = sub_questions
        return serialized

    top_level = []
    for q in questions:
        if not q.parent_question_id:
            top_level.append(build_subtree(q))
    
    return top_level

@router.get("/questions/{id}", 
             dependencies=[Depends(check_permission("read", "question"))])
async def get_question_details_admin(id: uuid.UUID, db: Session = Depends(get_db)):

    question = (
        db.query(models.Question)
        .filter(models.Question.id == id)
        .options(
            joinedload(models.Question.category),
            joinedload(models.Question.question_type),
            joinedload(models.Question.project_type),
            selectinload(models.Question.question_options),
            selectinload(models.Question.trigger_conditions),
            selectinload(models.Question.conditions),
        )
        .first()
    )
    if not question:
        raise HTTPException(status_code=404, detail="Question non trouvée")
    
    return _serialize_question(question)

@router.get("/questions/{id}/options", 
             dependencies=[Depends(check_permission("read", "question"))])
async def list_question_options(id: uuid.UUID, db: Session = Depends(get_db)):
    return db.query(models.QuestionOption).filter_by(question_id=id).order_by(models.QuestionOption.display_order.asc()).all()

@router.post("/questions/options", 
              status_code=status.HTTP_201_CREATED,
              dependencies=[Depends(check_permission("create", "question"))])
async def create_question_option(data: schemas_admin.QuestionOptionCreate, db: Session = Depends(get_db)):
    try:
        new_option = models.QuestionOption(id=uuid.uuid4(), question_id=data.question_id, option_text=data.option_text, display_order=data.display_order)
        db.add(new_option)
        db.commit()
        db.refresh(new_option)
        return {"success": True, "message": "Option créée", "data": new_option}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/questions/conditions", 
              status_code=status.HTTP_201_CREATED,
              dependencies=[Depends(check_permission("create", "question"))])
async def create_question_condition(data: schemas_admin.QuestionConditionCreate, db: Session = Depends(get_db)):
    try:
        new_condition = models.QuestionCondition(
            id=uuid.uuid4(),
            question_id=data.question_id,
            trigger_question_id=data.trigger_question_id,
            trigger_option_id=data.trigger_option_id,
            trigger_value=data.trigger_value,
            trigger_value_operator=data.trigger_value_operator or "contains",
            logical_operator=data.logical_operator or "OR",
            priority=data.priority or 1,
            is_required=data.is_required or False
        )
        db.add(new_condition)
        

        question = db.query(models.Question).filter_by(id=data.question_id).first()
        if question and not question.parent_question_id:
            question.parent_question_id = data.trigger_question_id
            
        db.commit()
        db.refresh(new_condition)
        return {"success": True, "message": "Condition créée", "data": {"id": str(new_condition.id)}}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/questions/{id}/conditions", 
             dependencies=[Depends(check_permission("read", "question"))])
async def list_question_conditions(id: uuid.UUID, db: Session = Depends(get_db)):

    conditions = (
        db.query(models.QuestionCondition)
        .filter_by(trigger_question_id=id)
        .options(
            joinedload(models.QuestionCondition.question),
            joinedload(models.QuestionCondition.trigger_option)
        )
        .order_by(models.QuestionCondition.priority.asc())
        .all()
    )
    
    return [
        {
            "id": str(c.id),
            "question_id": str(c.question_id),
            "question_label": c.question.label if c.question else "Inconnue",
            "trigger_option_id": str(c.trigger_option_id) if c.trigger_option_id else None,
            "trigger_option_text": c.trigger_option.option_text if c.trigger_option else None,
            "trigger_value": c.trigger_value,
            "trigger_value_operator": c.trigger_value_operator or "contains",
            "logical_operator": c.logical_operator or "OR",
            "priority": c.priority or 1,
            "is_required": c.is_required or False
        } for c in conditions
    ]

@router.delete("/questions/conditions/{condition_id}", 
                dependencies=[Depends(check_permission("delete", "question"))])
async def delete_question_condition(condition_id: uuid.UUID, db: Session = Depends(get_db)):
    cond = db.query(models.QuestionCondition).filter_by(id=condition_id).first()
    if not cond:
        raise HTTPException(status_code=404, detail="Condition non trouvée")
    db.delete(cond)
    db.commit()
    return {"success": True, "message": "Condition supprimée"}
