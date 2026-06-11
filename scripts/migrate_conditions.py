"""
Migration: Add advanced rule engine columns to question_conditions table.
Run once: python migrate_conditions.py
"""
from app.core.database import engine
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        # Add columns if they don't exist (PostgreSQL syntax)
        migrations = [
            "ALTER TABLE question_conditions ADD COLUMN IF NOT EXISTS trigger_value_operator VARCHAR DEFAULT 'contains'",
            "ALTER TABLE question_conditions ADD COLUMN IF NOT EXISTS logical_operator VARCHAR DEFAULT 'OR'",
            "ALTER TABLE question_conditions ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 1",
            "ALTER TABLE question_conditions ADD COLUMN IF NOT EXISTS is_required BOOLEAN DEFAULT FALSE",
        ]
        for sql in migrations:
            try:
                conn.execute(text(sql))
                print(f"OK: {sql[:60]}...")
            except Exception as e:
                print(f"SKIP (already exists?): {e}")
        conn.commit()
    print("\nMigration complete!")

if __name__ == "__main__":
    migrate()
