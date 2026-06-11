from fastapi import APIRouter
from . import project_types
from . import categories
from . import questions
from . import sessions
from . import documents
router = APIRouter()
router.include_router(project_types.router)
router.include_router(categories.router)
router.include_router(questions.router)
router.include_router(sessions.router)
router.include_router(documents.router)
