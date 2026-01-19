import os
import sys
from getpass import getpass
from sqlalchemy.orm import Session
from app import database,models, auth

# Ensure we can import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_admin():
    print("--- Create Initial Admin User ---")
    
    # Check database connection
    try:
        db = database.SessionLocal()
        db.execute("SELECT 1")
    except Exception as e:
        print(f"Error connecting to database: {e}")
        print("Make sure DATABASE_URL is set in your environment (or .env file)")
        return

    username = input("Enter Username: ")
    password = getpass("Enter Password: ")
    
    if not username or not password:
        print("Username and password are required.")
        return

    # Check if user exists
    existing_user = db.query(models.User).filter(models.User.username == username).first()
    if existing_user:
        print(f"User '{username}' already exists. Updating password...")
        existing_user.hashed_password = auth.get_password_hash(password)
    else:
        print(f"Creating new user '{username}'...")
        new_user = models.User(username=username, hashed_password=auth.get_password_hash(password))
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
