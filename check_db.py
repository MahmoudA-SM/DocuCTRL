from app import database, models
from sqlalchemy import inspect

db = database.SessionLocal()

inspector = inspect(database.engine)
columns = inspector.get_columns('users')
print("Columns in 'users' table:")
for col in columns:
    print(f"  - {col['name']}: {col['type']}")

users = db.query(models.User).all()
print(f"\nTotal users in database: {len(users)}")
for user in users:
    print(f"  - {user.email} (id: {user.id})")
    print(f"    Has hashed_password: {hasattr(user, 'hashed_password') and user.hashed_password is not None}")

db.close()