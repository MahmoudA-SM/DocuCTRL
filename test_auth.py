import bcrypt
from app import auth, database, models
from app import main

password = "password123"
hashed = auth.get_password_hash(password)
print(f"Generated hash: {hashed}")
print(f"Verification result: {auth.verify_password(password, hashed)}")

db = database.SessionLocal()
user = db.query(models.User).filter(models.User.email == "admin@example.com").first()
if user:
    print(f"\nUser found: {user.email}")
    print(f"Stored hash: {user.hashed_password}")
    if user.hashed_password:
        print(f"Password verification: {auth.verify_password(password, user.hashed_password)}")
else:
    print("\nNo user found in database")
db.close()