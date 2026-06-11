from pydantic import BaseModel
from typing import List, Optional, Any
from uuid import UUID
from enum import Enum
from datetime import datetime

class StatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    INACTIVE = "INACTIVE"

class QuestionTypeCreate(BaseModel):
    title: str
    description: Optional[str] = ""

class QuestionTypeUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

class QuestionTypeResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    is_general: bool = False
    project_type_id: Optional[UUID] = None

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[StatusEnum] = None
    is_general: Optional[bool] = None
    project_type_id: Optional[UUID] = None

class QuestionCreate(BaseModel):
    label: str
    description: Optional[str] = ""
    answer_type: str = "TEXT"
    options: Optional[List[str]] = None
    is_required: bool = False
    category_id: Optional[UUID] = None
    type_id: Optional[UUID] = None
    project_type_id: Optional[UUID] = None
    display_order: int = 1
    parent_question_id: Optional[UUID] = None
    trigger_option_id: Optional[UUID] = None
    trigger_value: Optional[str] = None
    trigger_value_operator: Optional[str] = "contains"

class QuestionUpdate(BaseModel):
    label: Optional[str] = None
    description: Optional[str] = None
    answer_type: Optional[str] = None
    options: Optional[List[Any]] = None
    is_required: Optional[bool] = None
    category_id: Optional[UUID] = None
    type_id: Optional[UUID] = None
    project_type_id: Optional[UUID] = None
    display_order: Optional[int] = None
    status: Optional[StatusEnum] = None
    parent_question_id: Optional[UUID] = None

class QuestionOptionCreate(BaseModel):
    question_id: UUID
    option_text: str
    display_order: int = 1

class QuestionConditionCreate(BaseModel):
    question_id: UUID
    trigger_question_id: UUID
    trigger_option_id: Optional[UUID] = None
    trigger_value: Optional[str] = None
    trigger_value_operator: Optional[str] = "contains"
    logical_operator: Optional[str] = "OR"
    priority: Optional[int] = 1
    is_required: Optional[bool] = False
class ReassignmentHistoryResponse(BaseModel):
    id: UUID
    question_label: str
    old_category_name: Optional[str]
    new_category_name: Optional[str]
    action: str
    timestamp: datetime

    class Config:
        from_attributes = True
