from datetime import datetime, timedelta
from typing import Optional, Iterable
import os
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from . import models, database

# Constants
SECRET_KEY = os.getenv("JWT_SECRET")
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET must be set for authentication to work safely.")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24)))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

PERMISSION_MANAGE_USERS = "manage_users"
PERMISSION_MANAGE_PROJECTS = "manage_projects"
PERMISSION_MANAGE_COMPANIES = "manage_companies"
PERMISSION_UPLOAD_DOCUMENTS = "upload_documents"
PERMISSION_VIEW_DOCUMENTS = "view_documents"
PERMISSION_VERIFY_DOCUMENTS = "verify_documents"

PERMISSION_DEFINITIONS = {
    PERMISSION_MANAGE_USERS: "Create and manage users",
    PERMISSION_MANAGE_PROJECTS: "Create and manage projects",
    PERMISSION_MANAGE_COMPANIES: "Create and manage owner companies",
    PERMISSION_UPLOAD_DOCUMENTS: "Upload and stamp documents",
    PERMISSION_VIEW_DOCUMENTS: "View and download documents",
    PERMISSION_VERIFY_DOCUMENTS: "Verify document serials",
}

ROLE_DEFINITIONS = {
    "admin": set(PERMISSION_DEFINITIONS.keys()),
    "manager": {
        PERMISSION_MANAGE_PROJECTS,
        PERMISSION_MANAGE_COMPANIES,
        PERMISSION_UPLOAD_DOCUMENTS,
        PERMISSION_VIEW_DOCUMENTS,
        PERMISSION_VERIFY_DOCUMENTS,
    },
    "uploader": {
        PERMISSION_UPLOAD_DOCUMENTS,
        PERMISSION_VIEW_DOCUMENTS,
        PERMISSION_VERIFY_DOCUMENTS,
    },
    "viewer": {
        PERMISSION_VIEW_DOCUMENTS,
        PERMISSION_VERIFY_DOCUMENTS,
    },
}

DEFAULT_ROLE = "viewer"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def ensure_default_roles_permissions(db: Session) -> None:
    existing_permissions = {perm.code: perm for perm in db.query(models.Permission).all()}
    created_permissions = False
    for code, description in PERMISSION_DEFINITIONS.items():
        if code not in existing_permissions:
            db.add(models.Permission(code=code, description=description))
            created_permissions = True
    if created_permissions:
        db.commit()
        existing_permissions = {perm.code: perm for perm in db.query(models.Permission).all()}

    existing_roles = {role.name: role for role in db.query(models.Role).all()}
    created_roles = False
    for role_name in ROLE_DEFINITIONS.keys():
        if role_name not in existing_roles:
            db.add(models.Role(name=role_name))
            created_roles = True
    if created_roles:
        db.commit()
        existing_roles = {role.name: role for role in db.query(models.Role).all()}

    for role_name, permission_codes in ROLE_DEFINITIONS.items():
        role = existing_roles.get(role_name)
        if not role:
            continue
        existing_codes = {perm.code for perm in role.permissions}
        missing = permission_codes - existing_codes
        for code in missing:
            perm = existing_permissions.get(code)
            if perm:
                role.permissions.append(perm)
    db.commit()

def ensure_default_user_roles(db: Session) -> None:
    default_role = db.query(models.Role).filter(models.Role.name == DEFAULT_ROLE).first()
    if not default_role:
        return
    users_without_roles = (
        db.query(models.User)
        .outerjoin(models.user_roles, models.User.id == models.user_roles.c.user_id)
        .filter(models.user_roles.c.user_id == None)
        .all()
    )
    for user in users_without_roles:
        user.roles.append(default_role)
    if users_without_roles:
        db.commit()

def assign_role_to_user(db: Session, user: models.User, role_name: str) -> None:
    role = db.query(models.Role).filter(models.Role.name == role_name).first()
    if not role:
        raise ValueError(f"Role '{role_name}' does not exist")
    if role not in user.roles:
        user.roles.append(role)
        db.commit()

def get_user_roles(user_id: int, db: Session) -> list[str]:
    rows = (
        db.query(models.Role.name)
        .join(models.user_roles, models.Role.id == models.user_roles.c.role_id)
        .filter(models.user_roles.c.user_id == user_id)
        .order_by(models.Role.name.asc())
        .all()
    )
    return [row[0] for row in rows]

def get_user_permissions(user_id: int, db: Session) -> set[str]:
    rows = (
        db.query(models.Permission.code)
        .join(models.role_permissions, models.Permission.id == models.role_permissions.c.permission_id)
        .join(models.user_roles, models.role_permissions.c.role_id == models.user_roles.c.role_id)
        .filter(models.user_roles.c.user_id == user_id)
        .distinct()
        .all()
    )
    return {row[0] for row in rows}

def require_permissions(required: Iterable[str]):
    required_set = set(required)

    def _dependency(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)) -> models.User:
        if not required_set:
            return user
        user_permissions = get_user_permissions(user.id, db)
        if not required_set.issubset(user_permissions):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        return user

    return _dependency

def _get_user_from_token(token: str, db: Session) -> models.User:
    if token.startswith("Bearer "):
        token = token.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

# Dependency for protecting routes
def get_current_user(request: Request, db: Session = Depends(get_db)) -> models.User:
    auth_header = request.headers.get("Authorization", "")
    token = None
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
    if not token:
        token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _get_user_from_token(token, db)

def get_user_from_token(token: str, db: Session) -> models.User:
    return _get_user_from_token(token, db)
