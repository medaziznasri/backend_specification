import os
import uuid
from sqlalchemy import text
from app.core.database import SessionLocal, engine
from app.core import models

def migrate_db():
    db = SessionLocal()
    try:
        print("--- RUNNING DB MIGRATION FOR SUB-QUESTIONS ---")
        
        # 1. Add parent_question_id to questions table
        print("Checking if parent_question_id exists in questions...")
        try:
            db.execute(text("SELECT parent_question_id FROM questions LIMIT 1"))
            print(" - Column parent_question_id already exists.")
        except Exception:
            db.rollback()
            print(" - Adding column parent_question_id to questions...")
            db.execute(text("ALTER TABLE questions ADD COLUMN parent_question_id UUID REFERENCES questions(id)"))
            db.commit()
            print(" - Column added successfully.")

        # 2. Create question_options table if not exists
        print("Checking if question_options table exists...")
        try:
            db.execute(text("SELECT id FROM question_options LIMIT 1"))
            print(" - Table question_options already exists.")
        except Exception:
            db.rollback()
            print(" - Creating table question_options...")
            db.execute(text("""
                CREATE TABLE question_options (
                    id UUID PRIMARY KEY,
                    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
                    option_text VARCHAR NOT NULL,
                    display_order INTEGER DEFAULT 1
                )
            """))
            db.commit()
            print(" - Table created successfully.")

        # 3. Create question_conditions table if not exists
        print("Checking if question_conditions table exists...")
        try:
            db.execute(text("SELECT id FROM question_conditions LIMIT 1"))
            print(" - Table question_conditions already exists.")
        except Exception:
            db.rollback()
            print(" - Creating table question_conditions...")
            db.execute(text("""
                CREATE TABLE question_conditions (
                    id UUID PRIMARY KEY,
                    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
                    trigger_question_id UUID NOT NULL REFERENCES questions(id),
                    trigger_option_id UUID REFERENCES question_options(id),
                    trigger_value VARCHAR
                )
            """))
            db.commit()
            print(" - Table created successfully.")

        print("\nSUCCESS: Database migration completed!")

    except Exception as e:
        db.rollback()
        print(f"MIGRATION ERROR: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_db()
