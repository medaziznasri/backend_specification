from pydantic import BaseModel, ConfigDict,EmailStr
from typing import List, Optional, Any
from uuid import UUID
from datetime import datetime

class ProjectTypeResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    status: str
    model_config = ConfigDict(from_attributes=True)

class CategoryResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    status: str
    is_general: bool
    project_type_id: Optional[UUID] = None
    model_config = ConfigDict(from_attributes=True)

class QuestionTypeResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    model_config = ConfigDict(from_attributes=True)

class QuestionOptionResponse(BaseModel):
    id: UUID
    option_text: str
    display_order: int
    model_config = ConfigDict(from_attributes=True)

class QuestionConditionResponse(BaseModel):
    id: UUID
    trigger_question_id: UUID
    trigger_option_id: Optional[UUID] = None
    trigger_value: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class QuestionForClient(BaseModel):
    id: str
    label: str
    description: Optional[str]
    answer_type: str
    options: Optional[Any]
    is_required: bool
    category_id: UUID
    category_name: Optional[str] = None
    question_type: Optional[QuestionTypeResponse] = None
    parent_question_id: Optional[UUID] = None
    question_options: List[QuestionOptionResponse] = []
    has_subquestions: bool = False
    model_config = ConfigDict(from_attributes=True)

class SessionCreate(BaseModel):
    project_type_id: str
    project_type_name: str | None = None
    selected_category_ids: List[str]
    client_email: str | None = None

class SessionResponse(BaseModel):
    id: UUID
    project_type_id: UUID
    started_at: datetime
    model_config = ConfigDict(from_attributes=True)

class AnswerItem(BaseModel):
    question_id: UUID
    value: Any

class AnswersSubmit(BaseModel):
    specifications_session_id: UUID
    answers: List[AnswerItem]

class GenerateRequest(BaseModel):
    session_id: UUID

class GenerateRequestBySpecId(BaseModel):

    specifications_session_id: UUID

class ProjectTypeCreate(BaseModel):
    name: str
    description: Optional[str] = None

class AdminLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role_id: Optional[str] = None

class UserBase(BaseModel):

    email: EmailStr

class UserCreate(UserBase):

    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    password: str

class UserOut(UserBase):

    id: int
    is_active: bool
    full_name: Optional[str] = None
    role: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class UserProfile(BaseModel):

    user_id: str
    email: Optional[str] = None
    role: str
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class DashboardSession(BaseModel):
    id: UUID
    project_name: str
    date: datetime
    status: str
    model_config = ConfigDict(from_attributes=True)

class DashboardProject(BaseModel):
    id: UUID
    project_name: str
    date: datetime
    pdfs: List[Any] = []
    model_config = ConfigDict(from_attributes=True)

class MySessionsResponse(BaseModel):
    sauvegardees: List[DashboardSession]
    projets: List[DashboardProject]
