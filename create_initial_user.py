import os
import sys
from getpass import getpass
from sqlalchemy import text
from sqlalchemy.orm import Session
from app import database,models, auth

# ... existing code ...

def create_admin():
    print("--- Create Initial Admin User ---")
    
    # Check database connection
    try:
        db = database.SessionLocal()
        db.execute(text("SELECT 1"))
    except Exception as e:
        print(f"Error connecting to database: {e}")
        print("Make sure DATABASE_URL is set in your environment (or .env file)")
        return

    email = input("Enter Email: ").strip().lower()
    password = getpass("Enter Password: ")
    
    if not email or not password:
        print("Email and password are required.")
        return

    # Check if user exists
    existing_user = db.query(models.User).filter(models.User.email == email).first()
    auth.ensure_default_roles_permissions(db)
    if existing_user:
        print(f"User '{email}' already exists. Updating password...")
        existing_user.hashed_password = auth.get_password_hash(password)
        try:
            auth.assign_role_to_user(db, existing_user, "admin")
        except ValueError:
            pass
    else:
        print(f"Creating new user '{email}'...")
        new_user = models.User(email=email, hashed_password=auth.get_password_hash(password))
        db.add(new_user)
        db.flush()
        auth.assign_role_to_user(db, new_user, "admin")
    
    try:
        db.commit()
        print("Success! User created/updated.")
    except Exception as e:
        db.rollback()
        print(f"Error saving user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
