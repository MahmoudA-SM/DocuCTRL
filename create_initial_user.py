import os
import sys
from getpass import getpass

from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

from sqlalchemy import text
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app import auth, database, models
from app.rbac import seed_rbac_data


def create_admin():
    print("--- Assign Admin Role To Existing User ---")
    
    try:
        db = database.SessionLocal()
        db.execute(text("SELECT 1"))
    except Exception as e:
        print(f"Error connecting to database: {e}")
        print("Make sure DATABASE_URL is set in your environment (or .env file)")
        return
    try:
        inspector = inspect(db.bind)
        table_names = set(inspector.get_table_names())
        if "roles" in table_names:
            role_cols = {col["name"] for col in inspector.get_columns("roles")}
            if "description" not in role_cols:
                db.execute(text("ALTER TABLE roles ADD COLUMN description VARCHAR"))
                db.commit()
        if "permissions" in table_names:
            perm_cols = {col["name"] for col in inspector.get_columns("permissions")}
            if "name" not in perm_cols:
                db.execute(text("ALTER TABLE permissions ADD COLUMN name VARCHAR"))
            if "resource" not in perm_cols:
                db.execute(text("ALTER TABLE permissions ADD COLUMN resource VARCHAR"))
            if "action" not in perm_cols:
                db.execute(text("ALTER TABLE permissions ADD COLUMN action VARCHAR"))
            if "name" not in perm_cols:
                db.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_permissions_name ON permissions (name)"))
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error ensuring RBAC columns: {e}")
        return

    env_email = os.getenv("ADMIN_EMAIL")
    email = (env_email or input("Enter Email: ")).strip().lower()
    
    existing_user = db.query(models.User).filter(models.User.email == email).first()
    if not existing_user:
        print(f"User '{email}' does not exist. Create the user first, then re-run this script.")
        return
    print(f"User '{email}' found. Assigning admin role...")
    
    try:
        seed_rbac_data(db)
        db.commit()

        admin_role = db.query(models.Role).filter(models.Role.name == "admin").first()
        if not admin_role:
            print("Admin role not found. Seed failed.")
            return
        existing_role = db.query(models.UserRole).filter(
            models.UserRole.user_id == existing_user.id,
            models.UserRole.role_id == admin_role.id,
            models.UserRole.project_id == None,
        ).first()
        if existing_role:
            print("User already has admin role.")
            return
        db.add(models.UserRole(user_id=existing_user.id, role_id=admin_role.id, project_id=None))
        db.commit()
        print("Success! Admin role assigned.")
    except Exception as e:
        db.rollback()
        print(f"Error saving user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()