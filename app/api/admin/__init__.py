from fastapi import APIRouter
from . import project_types
from . import categories
from . import questions
from . import history
from . import question_types
from . import users
router = APIRouter()
router.include_router(project_types.router)
router.include_router(categories.router)
router.include_router(questions.router)
router.include_router(history.router)
router.include_router(question_types.router)
router.include_router(users.router)
