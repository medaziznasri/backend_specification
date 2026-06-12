from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, JSON, Enum, LargeBinary
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref
from app.core.database import Base
import uuid
import enum
from datetime import datetime
from sqlalchemy.sql import func

class ProjectType(Base):
    __tablename__ = "project_types"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

class Category(Base):
    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String)
    is_general = Column(Boolean, default=False)
    status = Column(String, default="active")
    project_type_id = Column(UUID(as_uuid=True), ForeignKey("project_types.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    questions = relationship("Question", back_populates="category")
    project_type = relationship("ProjectType")

class QuestionType(Base):
    __tablename__ = "question_types"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    questions = relationship("Question", back_populates="question_type")

class Question(Base):
    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    label = Column(String, nullable=False)
    description = Column(String)
    answer_type = Column(String, default="TEXT")
    options = Column(JSON, nullable=True)
    is_required = Column(Boolean, default=False)
    display_order = Column(Integer, default=1)
    status = Column(String, default="active")
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), index=True)
    type_id = Column(UUID(as_uuid=True), ForeignKey("question_types.id"), nullable=True, index=True)
    project_type_id = Column(UUID(as_uuid=True), ForeignKey("project_types.id"), nullable=True, index=True)
    parent_question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    category = relationship("Category", back_populates="questions")
    question_type = relationship("QuestionType", back_populates="questions")
    project_type = relationship("ProjectType")
    question_options = relationship("QuestionOption", back_populates="question", cascade="all, delete-orphan")
    conditions = relationship("QuestionCondition", foreign_keys="QuestionCondition.question_id", back_populates="question", cascade="all, delete-orphan")
    trigger_conditions = relationship("QuestionCondition", foreign_keys="QuestionCondition.trigger_question_id", back_populates="trigger_question")
    sub_questions = relationship(
        "Question",
        backref=backref("parent_ref", remote_side="Question.id"),
        foreign_keys=[parent_question_id],
        lazy="selectin"
    )

class QuestionOption(Base):
    __tablename__ = "question_options"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False, index=True)
    option_text = Column(String, nullable=False)
    display_order = Column(Integer, default=1)

    question = relationship("Question", back_populates="question_options")
    triggered_conditions = relationship("QuestionCondition", back_populates="trigger_option")

class QuestionCondition(Base):
    __tablename__ = "question_conditions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False, index=True)
    trigger_question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False, index=True)
    trigger_option_id = Column(UUID(as_uuid=True), ForeignKey("question_options.id"), nullable=True, index=True)
    trigger_value = Column(String, nullable=True)
    trigger_value_operator = Column(String, default="contains")
    logical_operator = Column(String, default="OR")
    priority = Column(Integer, default=1)
    is_required = Column(Boolean, default=False)

    question = relationship("Question", foreign_keys=[question_id], back_populates="conditions")
    trigger_question = relationship("Question", foreign_keys=[trigger_question_id], back_populates="trigger_conditions")
    trigger_option = relationship("QuestionOption", back_populates="triggered_conditions")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    role = Column(String, default="CLIENT")
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sessions = relationship("ClientSpecificationSession", back_populates="owner")

class ClientSpecificationSession(Base):
    __tablename__ = "client_specification_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_type_id = Column(UUID(as_uuid=True), ForeignKey("project_types.id"), index=True, nullable=True)
    external_project_type_id = Column(String, nullable=True)
    external_project_type_name = Column(String, nullable=True)
    selected_category_ids = Column(JSON) 
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String, default="PENDING")

    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    client_email = Column(String, nullable=True)
    owner = relationship("User", back_populates="sessions")

    project_type = relationship("ProjectType")
    answers = relationship("ClientAnswer", back_populates="session", cascade="all, delete-orphan")
    pdfs = relationship("GeneratedSpecificationDocument", back_populates="session", cascade="all, delete-orphan")

class SessionCategory(Base):
    __tablename__ = "session_categories"
    session_id = Column(UUID(as_uuid=True), ForeignKey("client_specification_sessions.id"), primary_key=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), primary_key=True)

class ClientAnswer(Base):
    __tablename__ = "client_answers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("client_specification_sessions.id"), index=True)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), index=True)
    value = Column(String)
    answered_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ClientSpecificationSession", back_populates="answers")
    question = relationship("Question")

class GeneratedSpecificationDocument(Base):
    __tablename__ = "generated_documents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("client_specification_sessions.id"), index=True)
    file_path = Column(String)
    content_summary = Column(String)
    # PDF bytes stored in the DB so they survive Render's ephemeral filesystem.
    file_data = Column(LargeBinary, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ClientSpecificationSession", back_populates="pdfs")

class Role(Base):
    __tablename__ = "admin_roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)

class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role_id = Column(Integer, ForeignKey("admin_roles.id"), index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    action = Column(String, nullable=False)
    resource = Column(String, nullable=False)

class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id = Column(Integer, ForeignKey("admin_roles.id"), primary_key=True)
    permission_id = Column(Integer, ForeignKey("permissions.id"), primary_key=True)

class AuditAction(enum.Enum):
    REASSIGNED = "REASSIGNED"
    ARCHIVED = "ARCHIVED"

class QuestionCategoryHistory(Base):
    __tablename__ = "question_category_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False, index=True)
    previous_category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True, index=True)
    new_category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True, index=True)
    action = Column(Enum(AuditAction), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
