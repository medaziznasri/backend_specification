from app.core.database import engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    statements = [
        text("""
            ALTER TABLE questions
            ADD COLUMN IF NOT EXISTS project_type_id UUID
            REFERENCES project_types(id)
            ON DELETE SET NULL
        """),
        text("""
            CREATE INDEX IF NOT EXISTS ix_questions_project_type_id
            ON questions(project_type_id)
        """),
    ]
    try:
        with engine.connect() as conn:
            for stmt in statements:
                conn.execute(stmt)
            conn.commit()
            logger.info("Migration complete: project_type_id added to questions table")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    migrate()
