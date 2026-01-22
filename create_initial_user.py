import os
import sys
from getpass import getpass

from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

from sqlalchemy import text
from sqlalchemy.orm import Session

from app import auth, database, models

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

    env_email = os.getenv("ADMIN_EMAIL")
    env_password = os.getenv("ADMIN_PASSWORD")
    email = (env_email or input("Enter Email: ")).strip().lower()
    password = env_password or ""
    
    # Check if user exists
    existing_user = db.query(models.User).filter(models.User.email == email).first()
    if existing_user:
        if password:
            print(f"User '{email}' already exists. Updating password...")
            existing_user.hashed_password = auth.get_password_hash(password)
        else:
            print(f"User '{email}' already exists.")
    else:
        if not password:
            print("Password is required to create a new user.")
            return
        print(f"Creating new user '{email}'...")
        new_user = models.User(email=email, hashed_password=auth.get_password_hash(password))
        db.add(new_user)
    
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
