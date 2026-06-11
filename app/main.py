import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.database import engine
from app.core import models

from app.auth.auth import router as auth_router
from app.api.admin import router as admin_router
from app.api.client import router as client_router

from app.core.config import STORAGE_PATH

if not os.path.exists(STORAGE_PATH):
    os.makedirs(STORAGE_PATH, exist_ok=True)
print(f"DEBUG: Serving PDFs from {STORAGE_PATH}")

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="PFE Specification Manager",
    description="API for managing project specifications",
    version="1.0.0"
)

# Allowed origins: localhost for dev + anything in the ALLOWED_ORIGINS env var
# (comma-separated) for production, e.g. "https://your-app.vercel.app".
_default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:3000",
]
_env_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_default_origins + _env_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/files", StaticFiles(directory=STORAGE_PATH), name="specifications")

app.include_router(auth_router, prefix="/auth", tags=["auth"])

app.include_router(admin_router)

app.include_router(client_router)

@app.get("/health")
def health_check():

    return {
        "status": "online",
        "version": "1.0.0",
        "docs": "/docs"
    }

FRONTEND_PATH = "frontend"
if os.path.exists(FRONTEND_PATH):
    app.mount("/", StaticFiles(directory=FRONTEND_PATH, html=True), name="frontend")