

import os
from pathlib import Path

env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    try:

        with open(env_path, "r", encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip())
    except Exception:
        pass

SECRET_KEY = os.getenv("SECRET_KEY", "UNE_CLE_TRES_SECRETE_ET_LONGUE_12345")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:0000@localhost/specifications_manager"
)

STORAGE_PATH = str((Path(__file__).parent.parent.parent / os.getenv("STORAGE_PATH", "storage/specifications")).resolve())

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
