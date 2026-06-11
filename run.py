
#Usage: use venv\Scripts\activate and python run.py
import uvicorn
from app.core import config

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
    )
