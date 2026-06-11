from app.core.database import engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_column():
    query = text("ALTER TABLE client_specification_sessions ADD COLUMN IF NOT EXISTS status VARCHAR DEFAULT 'PENDING'")
    try:
        with engine.connect() as conn:
            conn.execute(query)
            conn.commit()
            logger.info("Successfully added 'status' column to client_specification_sessions")
    except Exception as e:
        logger.error(f"Failed to add column: {e}")

if __name__ == "__main__":
    add_column()
