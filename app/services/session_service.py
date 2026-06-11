import uuid
import json
import logging
import os
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from typing import Optional, List, Any
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import text
from fastapi import HTTPException

from app.core import models
from app.schemas import base as schemas
from app.core.cache import cache
from app.services.pdf_generator import generate_physical_pdf

logger = logging.getLogger(__name__)

def create_new_session(
    db: Session,
    session_data: schemas.SessionCreate,
    current_user: Optional[models.User]
) -> dict:

    def is_valid_uuid(val):
        try:
            uuid.UUID(str(val))
            return True
        except ValueError:
            return False

    is_local_project = is_valid_uuid(session_data.project_type_id)

    if is_local_project:
        cache_key = f"project_type_{session_data.project_type_id}"
        project_type = cache.get(cache_key)
        
        if not project_type:
            project_type = db.query(models.ProjectType).filter(
                models.ProjectType.id == session_data.project_type_id,
                models.ProjectType.status == 'active'
            ).first()
            if project_type:
                cache.set(cache_key, project_type)

        if not project_type:
            raise HTTPException(
                status_code=404,
                detail="Project type not found or inactive",
            )
    else:

        if not session_data.project_type_name:

            session_data.project_type_name = f"Projet {session_data.project_type_id}"

    if current_user:
        recent_threshold = datetime.utcnow() - timedelta(seconds=60)
        
        existing_session_query = db.query(models.ClientSpecificationSession).filter(
            models.ClientSpecificationSession.user_id == current_user.id,
            models.ClientSpecificationSession.started_at >= recent_threshold,
            models.ClientSpecificationSession.completed_at == None
        )
        if is_local_project:
            existing_session = existing_session_query.filter(models.ClientSpecificationSession.project_type_id == session_data.project_type_id).order_by(models.ClientSpecificationSession.started_at.desc()).first()
        else:
            existing_session = existing_session_query.filter(models.ClientSpecificationSession.external_project_type_id == str(session_data.project_type_id)).order_by(models.ClientSpecificationSession.started_at.desc()).first()
        
        if existing_session:
            logger.info(f"Returning existing session {existing_session.id} for user {current_user.id}")
            
            existing_cat_ids = existing_session.selected_category_ids
            if isinstance(existing_cat_ids, str):
                existing_cat_ids = json.loads(existing_cat_ids)
            elif not existing_cat_ids:
                existing_cat_ids = []
                
            new_cat_ids = session_data.selected_category_ids or []
            new_cat_ids_str = [str(x) for x in new_cat_ids]
            existing_cat_ids_str = [str(x) for x in existing_cat_ids]
            
            if new_cat_ids and set(new_cat_ids_str) != set(existing_cat_ids_str):
                logger.info(f"Updating categories for existing session {existing_session.id}")
                
                existing_session.selected_category_ids = json.dumps(new_cat_ids_str)
                
                db.query(models.SessionCategory).filter(
                    models.SessionCategory.session_id == existing_session.id
                ).delete()
                
                for cat_id in new_cat_ids:
                    if is_valid_uuid(cat_id):
                        try:
                            sc = models.SessionCategory(
                                session_id=existing_session.id,
                                category_id=cat_id
                            )
                            db.add(sc)
                        except Exception as e:
                            logger.error(f"Error adding updated category {cat_id}: {e}")
                
                db.commit()
                selected_category_ids = new_cat_ids
            else:
                selected_category_ids = existing_cat_ids

            return {
                "id": existing_session.id,
                "project_type_id": existing_session.project_type_id,
                "selected_category_ids": selected_category_ids,
                "started_at": existing_session.started_at,
                "completed_at": existing_session.completed_at,
            }

    if session_data.selected_category_ids:
        local_uuids = [cid for cid in session_data.selected_category_ids if is_valid_uuid(cid)]
        if local_uuids:
            categories_count = db.query(models.Category).filter(
                models.Category.id.in_(local_uuids),
                models.Category.status == 'active'
            ).count()
            
            if categories_count != len(local_uuids):
                raise HTTPException(
                    status_code=400,
                    detail="One or more local categories not found or inactive",
                )

    new_session_id = uuid.uuid4()
    started_at = datetime.utcnow()
    user_id = current_user.id if current_user else None
    
    category_ids_json = [str(cid) for cid in (session_data.selected_category_ids or [])]
    
    new_session = models.ClientSpecificationSession(
        id=new_session_id,
        project_type_id=session_data.project_type_id if is_local_project else None,
        external_project_type_id=None if is_local_project else str(session_data.project_type_id),
        external_project_type_name=None if is_local_project else session_data.project_type_name,
        selected_category_ids=json.dumps(category_ids_json),
        started_at=started_at,
        user_id=user_id,
        client_email=session_data.client_email if not user_id else None,
    )
    db.add(new_session)
    db.flush()

    if session_data.selected_category_ids:
        for cat_id in session_data.selected_category_ids:
            if is_valid_uuid(cat_id):
                try:
                    session_category = models.SessionCategory(
                        session_id=new_session_id,
                        category_id=cat_id
                    )
                    db.add(session_category)
                except Exception as e:
                    logger.error(f"Error adding category {cat_id}: {e}")

    db.commit()
    db.refresh(new_session)

    selected_category_ids = new_session.selected_category_ids
    if isinstance(selected_category_ids, str):
        selected_category_ids = json.loads(selected_category_ids)
    elif not selected_category_ids:
        selected_category_ids = []

    return {
        "id": new_session.id,
        "project_type_id": new_session.project_type_id,
        "selected_category_ids": selected_category_ids,
        "started_at": new_session.started_at,
        "completed_at": new_session.completed_at,
    }

def _serialize_session(session, user_email: str, user_name: str) -> dict:

    return {
        "session_id": str(session.id),
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        "user_email": user_email,
        "user_name": user_name,
        "project_type": {
            "id": str(session.project_type.id) if session.project_type else None,
            "name": session.project_type.name if session.project_type else None,
            "description": session.project_type.description if session.project_type else None
        },
        "answers": [
            {"question_id": str(ans.question_id), "value": ans.value}
            for ans in session.answers
        ],
        "pdfs": [
            {
                "id": str(pdf.id),
                "created_at": pdf.created_at.isoformat() if pdf.created_at else None,
                "pdf_url": f"/files/{os.path.basename(pdf.file_path)}",
                "content_summary": pdf.content_summary,
            }
            for pdf in session.pdfs
        ]
    }

def get_all_sessions_for_admin(db: Session) -> List[dict]:

    result = []

    users = (
        db.query(models.User)
        .options(
            selectinload(models.User.sessions).options(
                joinedload(models.ClientSpecificationSession.project_type),
                selectinload(models.ClientSpecificationSession.pdfs),
                selectinload(models.ClientSpecificationSession.answers)
            )
        )
        .all()
    )
    for user in users:
        for session in user.sessions:
            result.append(_serialize_session(session, user.email, user.email))

    anon_sessions = (
        db.query(models.ClientSpecificationSession)
        .filter(models.ClientSpecificationSession.user_id.is_(None))
        .options(
            joinedload(models.ClientSpecificationSession.project_type),
            selectinload(models.ClientSpecificationSession.pdfs),
            selectinload(models.ClientSpecificationSession.answers)
        )
        .order_by(models.ClientSpecificationSession.started_at.desc())
        .all()
    )
    for session in anon_sessions:
        email = session.client_email or "client (non enregistré)"
        name = session.client_email or "Anonyme"
        result.append(_serialize_session(session, email, name))

    return result

def get_user_sessions(db: Session, user_id: int) -> dict:

    sessions = (
        db.query(models.ClientSpecificationSession)
        .filter(models.ClientSpecificationSession.user_id == user_id)
        .options(
            joinedload(models.ClientSpecificationSession.project_type),
            selectinload(models.ClientSpecificationSession.pdfs)
        )
        .order_by(models.ClientSpecificationSession.started_at.desc())
        .all()
    )
    
    sauvegardees = []
    projets = []
    
    for session in sessions:
        project_name = session.project_type.name if session.project_type else "Projet sans nom"
        

        if session.status == "COMPLETED":
            projets.append({
                "id": session.id,
                "project_name": project_name,
                "date": session.started_at,
                "pdfs": [
                    {
                        "id": str(pdf.id),
                        "pdf_url": f"/files/{os.path.basename(pdf.file_path)}",
                    }
                    for pdf in session.pdfs
                ]
            })
        else:
            sauvegardees.append({
                "id": session.id,
                "project_name": project_name,
                "date": session.started_at,
                "status": session.status
            })
            
    return {"sauvegardees": sauvegardees, "projets": projets}

def get_session_details(db: Session, session_id: uuid.UUID) -> dict:

    session = (
        db.query(models.ClientSpecificationSession)
        .filter(models.ClientSpecificationSession.id == session_id)
        .options(
            joinedload(models.ClientSpecificationSession.project_type),
            selectinload(models.ClientSpecificationSession.pdfs),
            selectinload(models.ClientSpecificationSession.answers).options(
                joinedload(models.ClientAnswer.question)
            )
        )
        .first()
    )
    
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvée")
        
    detailed_answers = []
    for ans in session.answers:
        if not ans.question: continue
        
        answer_value = ans.value
        if isinstance(answer_value, str):
            try: answer_value = json.loads(answer_value)
            except (json.JSONDecodeError, ValueError): pass
            
        detailed_answers.append({
            "question_id": str(ans.question.id),
            "question_text": ans.question.label,
            "question_label": ans.question.label,
            "question_category": str(ans.question.category_id),
            "answer_text": answer_value,
            "value": answer_value,
            "answer_type": ans.question.answer_type,
            "answered_at": ans.answered_at.isoformat() if ans.answered_at else None
        })
        
    return {
        "session_id": str(session.id),
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        "project_type": {
            "id": str(session.project_type.id) if session.project_type else None,
            "name": session.project_type.name if session.project_type else None,
            "description": session.project_type.description if session.project_type else None
        },
        "selected_category_ids": session.selected_category_ids or [],
        "answers": detailed_answers,
        "pdfs": [
            {
                "id": str(pdf.id),
                "created_at": pdf.created_at.isoformat() if pdf.created_at else None,
                "pdf_url": f"/files/{os.path.basename(pdf.file_path)}",
                "content_summary": pdf.content_summary,
            }
            for pdf in session.pdfs
        ]
    }

def submit_answers(db: Session, session_id: uuid.UUID, answers: List[Any]) -> dict:

    session = db.query(models.ClientSpecificationSession).filter_by(id=session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    existing_answers = db.query(models.ClientAnswer).filter_by(session_id=session_id).all()
    existing_map = {ans.question_id: ans for ans in existing_answers}
    
    count = 0
    for ans_data in answers:
        q_id = ans_data.question_id
        val = json.dumps(ans_data.value)
        
        if q_id in existing_map:
            existing_map[q_id].value = val
        else:
            new_ans = models.ClientAnswer(
                id=uuid.uuid4(),
                session_id=session_id,
                question_id=q_id,
                value=val
            )
            db.add(new_ans)
        count += 1
        
    db.commit()
    return {"message": "Answers submitted successfully", "session_id": str(session_id), "answers_count": count}

def log_to_task_file(message):

    try:
        log_path = "storage/generation.log"
        os.makedirs("storage", exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
        print(f"DEBUG_TASK: {message}")
    except:
        pass

def _notify_scoring_engine(session_id: str, payload: dict):
    base_url = os.getenv("SCORING_ENGINE_URL", "http://localhost:9000")
    endpoint = os.getenv("SCORING_ENGINE_ENDPOINT", "/api/sessions/from-spec")
    url = base_url + endpoint
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            log_to_task_file(f"Scoring engine notified (HTTP {resp.status}): {session_id}")
    except urllib.error.URLError as e:
        log_to_task_file(f"Could not reach scoring engine (non-critical): {e}")
    except Exception as e:
        log_to_task_file(f"Scoring engine notification failed (non-critical): {e}")


def generate_pdf_background_task(db_factory, session_id: uuid.UUID):

    log_to_task_file(f"--- TASK STARTED: Session {session_id} ---")
    db: Session = db_factory()

    is_shared_session = False
    
    try:

        log_to_task_file("Fetching session details...")
        session = db.query(models.ClientSpecificationSession).filter_by(id=session_id).options(
            joinedload(models.ClientSpecificationSession.project_type),
            selectinload(models.ClientSpecificationSession.answers).options(
                joinedload(models.ClientAnswer.question)
            )
        ).first()

        if not session:
            log_to_task_file(f"CRITICAL: Session {session_id} not found.")
            return

        session.status = "PROCESSING"
        db.commit()
        log_to_task_file("Status updated to PROCESSING.")

        log_to_task_file("Building structured data...")
        structured_answers = []
        category_ids = set()
        

        answers_list = session.answers if session.answers else []
        if not answers_list:
            log_to_task_file("No answers found, generating document with metadata only.")
        else:
            log_to_task_file(f"Processing {len(answers_list)} answers...")

        for ans in answers_list:
            label = ans.question.label if ans.question else "Question inconnue"
            val = ans.value if ans.value else "Non répondu"
            structured_answers.append({"question": label, "answer": val})
            if ans.question and ans.question.category_id:
                category_ids.add(ans.question.category_id)

        all_categories = []
        if category_ids:
            categories = db.query(models.Category).filter(
                models.Category.id.in_(list(category_ids))
            ).order_by(models.Category.is_general.desc(), models.Category.name.asc()).all()
            for cat in categories:
                all_categories.append(f"[GENERAL] {cat.name}" if cat.is_general else cat.name)
        

        log_to_task_file("Preparing physical PDF generation...")
        file_name = f"spec_{session.id}_{datetime.now().strftime('%Y%m%d%H%M')}.pdf"
        storage_dir = "storage/specifications"
        os.makedirs(storage_dir, exist_ok=True)
        file_path = os.path.join(storage_dir, file_name)
        
        project_metadata = {
            "project_name": session.project_type.name if session.project_type else "Projet",
            "project_description": session.project_type.description if session.project_type else "",
            "categories": all_categories
        }
        
        log_to_task_file(f"Calling generate_physical_pdf...")
        start_time = datetime.now()
        generate_physical_pdf(structured_answers, file_path, str(session.id), project_metadata)
        duration = (datetime.now() - start_time).total_seconds()
        log_to_task_file(f"Physical PDF generation completed in {duration:.2f}s.")

        log_to_task_file("Finalizing database records...")
        new_doc = models.GeneratedSpecificationDocument(
            id=uuid.uuid4(),
            session_id=session.id,
            file_path=file_path,
            content_summary=f"Technical spec with {len(structured_answers)} answers."
        )
        db.add(new_doc)
        session.completed_at = datetime.utcnow()
        session.status = "COMPLETED"
        db.commit()
        log_to_task_file(f"--- TASK SUCCESS: Session {session_id} ---")

        scoring_payload = {
            "session_id": str(session_id),
            "project_type": {
                "id": str(session.project_type.id) if session.project_type else None,
                "name": session.project_type.name if session.project_type else "Projet",
                "description": session.project_type.description if session.project_type else "",
            },
            "categories": all_categories,
            "answers": structured_answers,
        }
        _notify_scoring_engine(str(session_id), scoring_payload)

    except Exception as e:
        log_to_task_file(f"!!! TASK ERROR: {str(e)}")
        import traceback
        log_to_task_file(traceback.format_exc())
        db.rollback()
        
        try:
            session = db.query(models.ClientSpecificationSession).filter_by(id=session_id).first()
            if session:
                session.status = "FAILED"
                db.commit()
                log_to_task_file("Session marked as FAILED.")
        except:
            pass
    finally:

        db.close()
        log_to_task_file("Task finished.")

def get_session_status(db: Session, session_id: uuid.UUID) -> dict:

    session = (
        db.query(models.ClientSpecificationSession)
        .filter(models.ClientSpecificationSession.id == session_id)
        .options(selectinload(models.ClientSpecificationSession.pdfs))
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    latest_pdf_url = None
    if session.status == "COMPLETED" and session.pdfs:

        sorted_pdfs = sorted(session.pdfs, key=lambda x: x.created_at, reverse=True)
        if sorted_pdfs:
             latest_pdf_url = f"/files/{os.path.basename(sorted_pdfs[0].file_path)}"

    return {
        "id": str(session.id),
        "status": session.status,
        "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        "pdf_url": latest_pdf_url
    }

