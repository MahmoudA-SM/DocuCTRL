from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import auth, models


def test_role_permission_mapping_roundtrip():
    engine = create_engine("sqlite:///:memory:")
    models.Base.metadata.create_all(
        bind=engine,
        tables=[
            models.Role.__table__,
            models.Permission.__table__,
            models.user_roles,
            models.role_permissions,
            models.User.__table__,
        ],
    )
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        auth.ensure_default_roles_permissions(db)
        user = models.User(email="viewer@example.com", hashed_password="x")
        db.add(user)
        db.commit()
        db.refresh(user)

        auth.assign_role_to_user(db, user, "viewer")
        permissions = auth.get_user_permissions(user.id, db)

        assert auth.PERMISSION_VIEW_DOCUMENTS in permissions
        assert auth.PERMISSION_MANAGE_USERS not in permissions
    finally:
        db.close()
