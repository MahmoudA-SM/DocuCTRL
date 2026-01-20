from app import database
from sqlalchemy import text

db = database.SessionLocal()

# Check if column exists
result = db.execute(text("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'users'
"""))
print("Columns in users table:")
for row in result:
    print(f"  - {row[0]}")

# Check users
result = db.execute(text("SELECT id, email, hashed_password FROM users"))
print("\nUsers in database:")
for row in result:
    print(f"  ID: {row[0]}, Email: {row[1]}, Has Password: {row[2] is not None}")
    if row[2]:
        print(f"    Password hash: {row[2][:50]}...")

db.close()
