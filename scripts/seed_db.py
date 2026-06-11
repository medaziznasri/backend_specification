import uuid
from sqlalchemy import text
from app.core.database import SessionLocal, engine
from app.core import models
from app.core.models import Base
from app.core.security import get_password_hash


def seed_db():
    """Seed the database with initial data for testing and development."""
    
    # Create all tables first
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        print("--- STARTING DATABASE SEEDING ---")

        # 1. CLEANUP (Hierarchical wipe) - use try/except for tables that may not exist
        print("Wiping database for a clean start...")
        try:
            db.execute(text("DELETE FROM session_categories"))
        except Exception:
            db.rollback()
        try:
            db.execute(text("DELETE FROM client_answers"))
        except Exception:
            db.rollback()
        try:
            db.execute(text("DELETE FROM generated_documents"))
        except Exception:
            db.rollback()
        try:
            db.execute(text("DELETE FROM client_specification_sessions"))
        except Exception:
            db.rollback()
        try:
            db.execute(text("DELETE FROM questions"))
        except Exception:
            db.rollback()
        try:
            db.execute(text("DELETE FROM categories"))
        except Exception:
            db.rollback()
        try:
            db.execute(text("DELETE FROM project_types"))
        except Exception:
            db.rollback()
        try:
            db.execute(text("DELETE FROM role_permissions"))
        except Exception:
            db.rollback()
        try:
            db.execute(text("DELETE FROM permissions"))
        except Exception:
            db.rollback()
        try:
            db.execute(text("DELETE FROM admin_users"))
        except Exception:
            db.rollback()
        try:
            db.execute(text("DELETE FROM admin_roles"))
        except Exception:
            db.rollback()
        db.commit()

        # 2. CREATE PROJECT TYPES
        print("Creating project types...")
        p_types = ["Web Application", "Mobile App", "AI Solution", "Desktop Software", "E-commerce"]
        for name in p_types:
            db.add(models.ProjectType(id=uuid.uuid4(), name=name, status="active"))
        db.flush()

        # 3. CREATE CATEGORIES (only Project Identity is GENERAL, others are SPECIFIC)
        print("Creating categories...")
        cats = {
            "ID": models.Category(id=uuid.uuid4(), name="I. Project Identity", is_general=True, status="active"),
            "FUN": models.Category(id=uuid.uuid4(), name="II. Functional Features", is_general=False, status="active"),
            "TEC": models.Category(id=uuid.uuid4(), name="III. Technical Architecture", is_general=False, status="active"),
            "SEC": models.Category(id=uuid.uuid4(), name="IV. Security & Data", is_general=False, status="active"),
            "LOG": models.Category(id=uuid.uuid4(), name="V. Logistics & Budget", is_general=False, status="active")
        }
        for cat in cats.values():
            db.add(cat)
        db.flush()

        # 4. CREATE 22 PROFESSIONAL QUESTIONS
        print("Injecting 22 questions...")
        q_data = [
            (cats["ID"], "Full Project Name", 1),
            (cats["ID"], "Main Problem Solved by the Project", 2),
            (cats["ID"], "Target Users (End-customers, Staff, etc.)", 3),
            (cats["ID"], "Primary Language for the Interface", 4),
            (cats["FUN"], "Detailed User Registration Flow", 1),
            (cats["FUN"], "List of User Roles (Admin, User, Manager)", 2),
            (cats["FUN"], "Core Features (Describe the main dashboard)", 3),
            (cats["FUN"], "Should the system send automated Emails/SMS?", 4),
            (cats["FUN"], "Payment Gateway Integration (Stripe, PayPal, etc.)", 5),
            (cats["TEC"], "Preferred Backend Language (FastAPI, Node.js, Spring)", 1),
            (cats["TEC"], "Preferred Frontend Library (React, Vue, Angular)", 2),
            (cats["TEC"], "Database Preference (PostgreSQL, MongoDB)", 3),
            (cats["TEC"], "Cloud Hosting Provider (AWS, Azure, GCP)", 4),
            (cats["TEC"], "Do you require an Admin Panel?", 5),
            (cats["SEC"], "Expected Concurrent Users (Peak Traffic)", 1),
            (cats["SEC"], "Is Two-Factor Authentication (2FA) Required?", 2),
            (cats["SEC"], "Data Backup and Recovery Requirements", 3),
            (cats["SEC"], "GDPR / Data Privacy Compliance Needs", 4),
            (cats["LOG"], "Total Estimated Budget for the Project", 1),
            (cats["LOG"], "Desired Launch Date (MVP)", 2),
            (cats["LOG"], "Maintenance Support Requirements after Launch", 3),
            (cats["LOG"], "Internal Staff Training Required?", 4)
        ]

        for cat_obj, label, order in q_data:
            db.add(models.Question(
                id=uuid.uuid4(),
                category_id=cat_obj.id,
                label=label,
                answer_type="text",
                is_required=True,
                display_order=order,
                status="active"
            ))

        # 5. CREATE ADMIN ROLE & USER (FIXED FOR INTEGER ID)
        print("Setting up Admin (Integer ID fix)...")
        # We don't pass an ID here; let the DB generate the Integer 1, 2, 3...
        role = models.Role(name="Admin", description="Full Access")
        db.add(role)
        db.flush()
        
        admin = models.AdminUser(
            id=uuid.uuid4(),
            username="admin@example.com",
            email="admin@example.com",
            password_hash=get_password_hash("admin123"),
            role_id=role.id,
            is_active=True
        )
        db.add(admin)
        db.flush()

        # 6. CREATE PERMISSIONS & ROLE_PERMISSIONS (CRITICAL FOR RBAC)
        print("Setting up permissions...")
        permissions_data = [
            # Category permissions
            ("create_category", "create", "category"),
            ("read_category", "read", "category"),
            ("update_category", "update", "category"),
            ("delete_category", "delete", "category"),
            # Question permissions
            ("create_question", "create", "question"),
            ("read_question", "read", "question"),
            ("update_question", "update", "question"),
            ("delete_question", "delete", "question"),
            # Project type permissions
            ("create_project_type", "create", "project_type"),
            ("read_project_type", "read", "project_type"),
            ("update_project_type", "update", "project_type"),
            ("delete_project_type", "delete", "project_type"),
        ]
        
        for perm_name, action, resource in permissions_data:
            perm = models.Permission(name=perm_name, action=action, resource=resource)
            db.add(perm)
            db.flush()
            # Assign all permissions to Admin role
            role_perm = models.RolePermission(role_id=role.id, permission_id=perm.id)
            db.add(role_perm)
        
        db.commit()
        print("\n" + "="*50)
        print(" SUCCESS: DATABASE IS READY!")
        print(" 22 Questions / 5 Categories (1 General + 4 Specific)")
        print(" 12 Permissions assigned to Admin role")
        print(" Login: admin@example.com / admin123")
        print("="*50)

    except Exception as e:
        db.rollback()
        print(f"SEED ERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_db()