from app import database
from sqlalchemy import text

db = database.SessionLocal()

result = db.execute(text())
print("Columns in users table:")
for row in result:
    print(f"  - {row[0]}")

result = db.execute(text("SELECT id, email, hashed_password FROM users"))
print("\nUsers in database:")
for row in result:
    print(f"  ID: {row[0]}, Email: {row[1]}, Has Password: {row[2] is not None}")
    if row[2]:
        print(f"    Password hash: {row[2][:50]}...")

db.close()