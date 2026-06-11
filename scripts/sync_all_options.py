import json
import uuid
import logging
from sqlalchemy import text
from app.core.database import SessionLocal
from app.core import models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sync_all_options():
    db = SessionLocal()
    try:
        # Get all questions
        questions = db.query(models.Question).all()
        logger.info(f"Checking {len(questions)} questions for option synchronization...")

        for q in questions:
            # Skip if it doesn't need options
            if q.answer_type not in ["MULTI_CHOICE", "SINGLE_CHOICE", "BOOLEAN", "multi_choice", "single_choice", "boolean"]:
                continue
            
            # Check existing options in the new table
            existing_count = db.query(models.QuestionOption).filter_by(question_id=q.id).count()
            
            if existing_count > 0:
                logger.debug(f"Question {q.id} ({q.label}) already has {existing_count} options. Skipping.")
                continue

            # Determine options to add
            final_options = []
            if q.answer_type.lower() == "boolean":
                final_options = ["Oui", "Non"]
            elif q.options:
                if isinstance(q.options, str):
                    try:
                        final_options = json.loads(q.options)
                    except:
                        final_options = [opt.strip() for opt in q.options.split(',') if opt.strip()]
                elif isinstance(q.options, list):
                    final_options = q.options
            
            if not final_options:
                logger.warning(f"Question {q.id} needs options but 'options' field is empty/invalid.")
                continue

            logger.info(f"Syncing {len(final_options)} options for Question: {q.label} ({q.id})")
            for i, opt_text in enumerate(final_options):
                db.add(models.QuestionOption(
                    id=uuid.uuid4(),
                    question_id=q.id,
                    option_text=opt_text,
                    display_order=i+1
                ))
        
        db.commit()
        logger.info("Synchronization complete!")

    except Exception as e:
        db.rollback()
        logger.error(f"Error during synchronization: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    sync_all_options()
