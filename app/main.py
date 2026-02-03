import os
import shutil
import logging
from io import BytesIO
from datetime import datetime, timedelta

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError
from fastapi.responses import FileResponse, RedirectResponse, HTMLResponse, JSONResponse, StreamingResponse
from urllib.parse import quote
import urllib.request
from openpyxl import Workbook
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, constr, EmailStr
from typing import Optional

from . import models, database, utils, auth
from .rbac import (
    Permissions, require_permission, require_all_permissions,
    get_user_permissions, get_user_roles, assign_role_to_user,
    remove_role_from_user, get_user_effective_role, seed_rbac_data,
    has_permission, get_user_highest_role, get_role_rank
)
from supabase import create_client, Client

require_document_upload = require_permission(Permissions.DOCUMENT_UPLOAD)
require_document_read = require_permission(Permissions.DOCUMENT_READ)
require_document_download = require_permission(Permissions.DOCUMENT_DOWNLOAD)
require_document_delete = require_permission(Permissions.DOCUMENT_DELETE)
require_project_create = require_permission(Permissions.PROJECT_CREATE)
require_project_manage = require_permission(Permissions.PROJECT_MANAGE)
require_user_manage = require_permission(Permissions.USER_MANAGE)
require_user_read = require_permission(Permissions.USER_READ)
require_user_invite = require_permission(Permissions.USER_INVITE)
require_company_create = require_permission(Permissions.COMPANY_CREATE)
require_role_manage = require_permission(Permissions.ROLE_MANAGE)
require_role_assign = require_permission(Permissions.ROLE_ASSIGN)



BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "docuctrl-files")
SUPABASE_SIGNED_URL_TTL = int(os.getenv("SUPABASE_SIGNED_URL_TTL", "300"))
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "").strip().lower()

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def _resolve_storage_dir() -> str:
    configured = os.getenv("STORAGE_DIR")
    if configured:
        return configured
    candidates = [
        os.path.join(os.path.sep, "tmp", "docuctrl-storage"),
        os.path.join(BASE_DIR, "storage"),
    ]
    for path in candidates:
        try:
            os.makedirs(path, exist_ok=True)
            test_path = os.path.join(path, ".write_test")
            with open(test_path, "w") as test_file:
                test_file.write("ok")
            os.remove(test_path)
            return path
        except OSError:
            continue
    return os.path.join(BASE_DIR, "storage")

STORAGE_DIR = _resolve_storage_dir()
os.makedirs(STORAGE_DIR, exist_ok=True)

def ensure_user_email_column():
    inspector = inspect(database.engine)
    if "users" not in inspector.get_table_names():
        return
    columns = {col["name"] for col in inspector.get_columns("users")}
    if "email" in columns:
        return
    with database.engine.begin() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN email VARCHAR"))
        if "username" in columns:
            conn.execute(text("UPDATE users SET email = username WHERE email IS NULL"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)"))

def ensure_document_original_filename_column():
    inspector = inspect(database.engine)
    if "documents" not in inspector.get_table_names():
        return
    columns = {col["name"] for col in inspector.get_columns("documents")}
    if "original_filename" in columns:
        return
    with database.engine.begin() as conn:
        conn.execute(text("ALTER TABLE documents ADD COLUMN original_filename VARCHAR"))

logger = logging.getLogger("docuctrl")

def _initialize_database() -> None:
    try:
        models.Base.metadata.create_all(bind=database.engine)
        ensure_user_email_column()
        ensure_document_original_filename_column()
        
        db = database.SessionLocal()
        try:
            seed_rbac_data(db)
            logger.info("RBAC data seeded successfully")
        except Exception as exc:
            logger.warning("RBAC seeding skipped: %s", exc)
        finally:
            db.close()
    except SQLAlchemyError as exc:
        logger.warning("Database initialization skipped: %s", exc)

_initialize_database()

app = FastAPI(title="Document Control System")

REACT_BUILD_DIR = os.path.join(BASE_DIR, "frontend", "build")
if os.path.exists(REACT_BUILD_DIR):
    app.mount("/static", StaticFiles(directory=os.path.join(REACT_BUILD_DIR, "static")), name="static")

def _get_allowed_origins() -> list[str]:
    origins = os.getenv("ALLOWED_ORIGINS")
    if not origins:
        return ["*"]
    return [origin.strip() for origin in origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _has_admin_any_project(db: Session, user_id: int) -> bool:
    admin_perm = db.query(models.UserPermission).join(
        models.Permission, models.UserPermission.permission_id == models.Permission.id
    ).filter(
        models.UserPermission.user_id == user_id,
        models.Permission.name == Permissions.ADMIN_ALL,
    ).first()
    if admin_perm:
        return True
    admin_role = db.query(models.UserRole).join(
        models.Role, models.UserRole.role_id == models.Role.id
    ).filter(
        models.UserRole.user_id == user_id,
        models.Role.name == "admin",
    ).first()
    return bool(admin_role)


@app.get("/login", response_class=HTMLResponse)
def login_page():
    login_path = os.path.join(BASE_DIR, "frontend", "login.html")
    if not os.path.exists(login_path):
        return "Login page not found."
    with open(login_path, "r", encoding="utf-8") as f:
        return f.read()

@app.post("/token")
async def login_for_access_token(response: RedirectResponse, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    email = form_data.username.strip().lower()
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not user.hashed_password or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    
    content = {"access_token": access_token, "token_type": "bearer"}
    resp = JSONResponse(content=content)
    cookie_secure = os.getenv("COOKIE_SECURE", "true").lower() == "true"
    cookie_samesite = os.getenv("COOKIE_SAMESITE", "lax").lower()
    cookie_domain = os.getenv("COOKIE_DOMAIN")
    resp.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=cookie_secure,
        samesite=cookie_samesite,
        max_age=auth.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        domain=cookie_domain,
        path="/",
    )
    return resp

def get_current_user(request: Request, db: Session = Depends(get_db)) -> models.User:
    return auth.get_current_user(request, db)

@app.get("/")
def read_root(request: Request, db: Session = Depends(get_db)):
    react_index = os.path.join(BASE_DIR, "frontend", "build", "index.html")
    try:
        auth.get_current_user(request, db)
        if os.path.exists(react_index):
            return FileResponse(react_index)
        return RedirectResponse(url="/docs")
    except HTTPException:
        token = request.query_params.get("access_token")
        if not token:
            return RedirectResponse(url="/login")
        try:
            auth.get_user_from_token(token, db)
        except HTTPException:
            return RedirectResponse(url="/login")
        if os.path.exists(react_index):
            resp = FileResponse(react_index)
        else:
            resp = RedirectResponse(url="/docs")
        cookie_secure = os.getenv("COOKIE_SECURE", "true").lower() == "true"
        cookie_samesite = os.getenv("COOKIE_SAMESITE", "lax").lower()
        cookie_domain = os.getenv("COOKIE_DOMAIN")
        resp.set_cookie(
            key="access_token",
            value=f"Bearer {token}",
            httponly=True,
            secure=cookie_secure,
            samesite=cookie_samesite,
            max_age=auth.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            domain=cookie_domain,
            path="/",
        )
        return resp

@app.get("/me")
def get_me(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    
    roles_data = []
    user_roles = db.query(models.UserRole).filter(models.UserRole.user_id == user.id).all()
    
    for ur in user_roles:
        role = db.query(models.Role).filter(models.Role.id == ur.role_id).first()
        if role:
            permissions = [rp.permission.name for rp in role.permissions]
            role_info = {
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "project_id": ur.project_id,
                "permissions": permissions,
            }
            roles_data.append(role_info)
    
    global_perms = get_user_permissions(db, user.id, None)
    
    effective_role = get_user_effective_role(db, user.id, None)
    
    return {
        "id": user.id,
        "email": user.email,
        "roles": roles_data,
        "global_permissions": list(global_perms),
        "effective_role": effective_role
    }


class UserCreate(BaseModel):
    email: EmailStr
    password: constr(min_length=8, max_length=128)


class UserRoleAssignment(BaseModel):
    project_id: int
    role_name: constr(strip_whitespace=True, min_length=2, max_length=64) | None = None
    permissions: list[str] | None = None


class UserCreateWithRoles(UserCreate):
    assignments: list[UserRoleAssignment]


@app.post("/users", status_code=status.HTTP_201_CREATED)
@app.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(
    payload: UserCreateWithRoles,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    email = payload.email.strip().lower()
    existing = db.query(models.User).filter(models.User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")
    hashed_password = auth.get_password_hash(payload.password)
    if not payload.assignments:
        raise HTTPException(status_code=400, detail="At least one project assignment is required")

    user = models.User(email=email, hashed_password=hashed_password)
    db.add(user)
    db.flush()

    seen_projects = set()
    for assignment in payload.assignments:
        if assignment.project_id in seen_projects:
            raise HTTPException(status_code=400, detail="Duplicate project assignment is not allowed")
        seen_projects.add(assignment.project_id)
        if not has_permission(db, current_user.id, Permissions.USER_CREATE, assignment.project_id):
            raise HTTPException(status_code=403, detail="Permission denied to create user for project")
        project = db.query(models.Project).filter(models.Project.id == assignment.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail=f"Project not found: {assignment.project_id}")
        if not assignment.role_name and not assignment.permissions:
            raise HTTPException(status_code=400, detail="Role or permissions are required for each project assignment")

        existing_assignment = db.query(models.UserProjectAssignment).filter(
            models.UserProjectAssignment.user_id == user.id,
            models.UserProjectAssignment.project_id == assignment.project_id,
        ).first()
        if not existing_assignment:
            db.add(
                models.UserProjectAssignment(
                    user_id=user.id,
                    project_id=assignment.project_id,
                )
            )

        if assignment.role_name:
            current_role = get_user_highest_role(db, current_user.id, assignment.project_id)
            if not current_role:
                raise HTTPException(status_code=403, detail="Cannot assign role without a project role")
            current_rank = get_role_rank(current_role)
            target_rank = get_role_rank(assignment.role_name)
            if target_rank < current_rank and Permissions.ADMIN_ALL not in get_user_permissions(db, current_user.id, assignment.project_id):
                raise HTTPException(status_code=403, detail="Cannot assign a higher role")
            role = db.query(models.Role).filter(models.Role.name == assignment.role_name).first()
            if not role:
                raise HTTPException(status_code=404, detail=f"Role not found: {assignment.role_name}")
            db.add(
                models.UserRole(
                    user_id=user.id,
                    role_id=role.id,
                    project_id=assignment.project_id,
                )
            )

        if assignment.permissions:
            current_perms = get_user_permissions(db, current_user.id, assignment.project_id)
            if Permissions.ADMIN_ALL not in current_perms:
                missing = set(assignment.permissions) - current_perms
                if missing:
                    raise HTTPException(status_code=403, detail=f"Cannot grant permissions: {', '.join(sorted(missing))}")
            permission_rows = db.query(models.Permission).filter(
                models.Permission.name.in_(assignment.permissions)
            ).all()
            permission_by_name = {perm.name: perm for perm in permission_rows}
            unknown = set(assignment.permissions) - set(permission_by_name.keys())
            if unknown:
                raise HTTPException(status_code=400, detail=f"Unknown permissions: {', '.join(sorted(unknown))}")
            for perm in permission_by_name.values():
                db.add(
                    models.UserPermission(
                        user_id=user.id,
                        permission_id=perm.id,
                        project_id=assignment.project_id,
                    )
                )

    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email}

@app.get("/me/projects")
def get_my_projects(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        if Permissions.ADMIN_ALL in get_user_permissions(db, user.id, None):
            projects = db.query(models.Project).order_by(models.Project.name.asc()).all()
        else:
            projects = (
                db.query(models.Project)
                .join(models.UserProjectAssignment, models.UserProjectAssignment.project_id == models.Project.id)
                .filter(models.UserProjectAssignment.user_id == user.id)
                .order_by(models.Project.name.asc())
                .all()
            )
    except SQLAlchemyError as exc:
        logger.exception("Failed to load user projects for user_id=%s", user.id)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "PROJECTS_QUERY_FAILED",
                "message": "تعذر تحميل المشروعات من قاعدة البيانات.",
            },
        )
    return [
        {
            "id": project.id,
            "name": project.name,
            "owner_company_name": project.owner.name if project.owner else None,
        }
        for project in projects
    ]


@app.get("/users/visible")
def list_visible_users(
    project_id: int | None = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if project_id is None:
        raise HTTPException(status_code=400, detail="project_id is required")
    current_perms = get_user_permissions(db, current_user.id, project_id)
    has_admin_perm = Permissions.ADMIN_ALL in current_perms
    has_admin_role = db.query(models.UserRole).join(
        models.Role, models.UserRole.role_id == models.Role.id
    ).filter(
        models.UserRole.user_id == current_user.id,
        models.UserRole.project_id == project_id,
        models.Role.name == "admin",
    ).first()
    if not has_admin_perm and not has_admin_role and Permissions.USER_READ not in current_perms:
        raise HTTPException(status_code=403, detail="Permission denied")

    if has_admin_perm or has_admin_role:
        users = db.query(models.User).order_by(models.User.email.asc()).all()
    else:
        users = (
            db.query(models.User)
            .join(models.UserProjectAssignment, models.UserProjectAssignment.user_id == models.User.id)
            .filter(models.UserProjectAssignment.project_id == project_id)
            .order_by(models.User.email.asc())
            .all()
        )
    visible = []
    for user in users:
        if user.id == current_user.id:
            continue
        user_role = get_user_highest_role(db, user.id, project_id)
        role_assignments = db.query(models.UserRole).filter(
            models.UserRole.user_id == user.id,
            models.UserRole.project_id == project_id,
        ).all()
        roles = []
        for assignment in role_assignments:
            role = db.query(models.Role).filter(models.Role.id == assignment.role_id).first()
            if role:
                roles.append(
                    {
                        "name": role.name,
                        "project_id": assignment.project_id,
                    }
                )
        visible.append(
            {
                "id": user.id,
                "email": user.email,
                "effective_role": user_role,
                "roles": roles,
            }
        )
    return visible


@app.get("/permissions")
def list_permissions(
    project_id: int | None = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if project_id is None:
        raise HTTPException(status_code=400, detail="project_id is required")
    if not has_permission(db, current_user.id, Permissions.USER_READ, project_id):
        raise HTTPException(status_code=403, detail="Permission denied")
    perms = db.query(models.Permission).order_by(
        models.Permission.resource.asc(),
        models.Permission.action.asc(),
    ).all()
    return [
        {
            "name": perm.name,
            "resource": perm.resource,
            "action": perm.action,
        }
        for perm in perms
    ]


@app.get("/roles/presets")
def list_role_presets(
    project_id: int | None = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if project_id is None:
        raise HTTPException(status_code=400, detail="project_id is required")
    if not has_permission(db, current_user.id, Permissions.USER_READ, project_id):
        raise HTTPException(status_code=403, detail="Permission denied")
    roles = db.query(models.Role).order_by(models.Role.name.asc()).all()
    result = []
    for role in roles:
        permissions = [rp.permission.name for rp in role.permissions]
        result.append(
            {
                "name": role.name,
                "description": role.description,
                "permissions": permissions,
            }
        )
    return result


@app.get("/projects/{project_id}/users/{user_id}/permissions")
def get_user_permissions_for_project(
    project_id: int,
    user_id: int,
    current_user: models.User = Depends(require_user_read),
    db: Session = Depends(get_db),
):
    if not has_permission(db, current_user.id, Permissions.USER_READ, project_id):
        raise HTTPException(status_code=403, detail="Permission denied")
    direct_perms = db.query(models.Permission.name).join(
        models.UserPermission,
        models.UserPermission.permission_id == models.Permission.id,
    ).filter(
        models.UserPermission.user_id == user_id,
        models.UserPermission.project_id == project_id,
    ).all()
    direct_list = [name for (name,) in direct_perms]
    effective = list(get_user_permissions(db, user_id, project_id))
    return {
        "direct_permissions": sorted(direct_list),
        "effective_permissions": sorted(effective),
    }


@app.post("/projects/{project_id}/users/{user_id}/assign")
def assign_user_to_project(
    project_id: int,
    user_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not has_permission(db, current_user.id, Permissions.USER_MANAGE, project_id):
        raise HTTPException(status_code=403, detail="Permission denied")
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    existing = db.query(models.UserProjectAssignment).filter(
        models.UserProjectAssignment.user_id == user_id,
        models.UserProjectAssignment.project_id == project_id,
    ).first()
    if existing:
        return {"status": "already_assigned", "user_id": user_id, "project_id": project_id}

    db.add(models.UserProjectAssignment(user_id=user_id, project_id=project_id))
    db.commit()
    return {"status": "assigned", "user_id": user_id, "project_id": project_id}


@app.delete("/projects/{project_id}/users/{user_id}/assign")
def remove_user_from_project(
    project_id: int,
    user_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not has_permission(db, current_user.id, Permissions.USER_MANAGE, project_id):
        raise HTTPException(status_code=403, detail="Permission denied")
    assignment = db.query(models.UserProjectAssignment).filter(
        models.UserProjectAssignment.user_id == user_id,
        models.UserProjectAssignment.project_id == project_id,
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    db.delete(assignment)
    db.commit()
    return {"status": "removed", "user_id": user_id, "project_id": project_id}


@app.get("/admin/users")
def list_all_users_admin(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    has_admin_perm = db.query(models.UserPermission).join(
        models.Permission,
        models.UserPermission.permission_id == models.Permission.id,
    ).filter(
        models.UserPermission.user_id == current_user.id,
        models.Permission.name == Permissions.ADMIN_ALL,
    ).first()
    has_admin_role = db.query(models.UserRole).join(
        models.Role,
        models.UserRole.role_id == models.Role.id,
    ).filter(
        models.UserRole.user_id == current_user.id,
        models.Role.name == "admin",
    ).first()
    if not has_admin_perm and not has_admin_role:
        raise HTTPException(status_code=403, detail="Admin access required")

    users = db.query(models.User).order_by(models.User.email.asc()).all()
    result = []
    for user in users:
        role_rows = db.query(models.UserRole, models.Role).join(
            models.Role, models.UserRole.role_id == models.Role.id
        ).filter(models.UserRole.user_id == user.id).all()
        perm_rows = db.query(models.UserPermission, models.Permission).join(
            models.Permission, models.UserPermission.permission_id == models.Permission.id
        ).filter(models.UserPermission.user_id == user.id).all()

        projects = {}
        for role_assignment, role in role_rows:
            key = role_assignment.project_id
            entry = projects.setdefault(key, {"project_id": key, "roles": [], "permissions": []})
            entry["roles"].append(role.name)
        for perm_assignment, perm in perm_rows:
            key = perm_assignment.project_id
            entry = projects.setdefault(key, {"project_id": key, "roles": [], "permissions": []})
            entry["permissions"].append(perm.name)

        result.append(
            {
                "id": user.id,
                "email": user.email,
                "projects": list(projects.values()),
            }
        )
    return result


class UserPermissionUpdate(BaseModel):
    permissions: list[str]


@app.put("/projects/{project_id}/users/{user_id}/permissions")
def set_user_permissions_for_project(
    project_id: int,
    user_id: int,
    payload: UserPermissionUpdate,
    current_user: models.User = Depends(require_user_manage),
    db: Session = Depends(get_db),
):
    if not has_permission(db, current_user.id, Permissions.USER_MANAGE, project_id):
        raise HTTPException(status_code=403, detail="Permission denied")
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    target_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    requested = {name.strip() for name in payload.permissions if name.strip()}
    if not requested:
        requested = set()

    current_perms = get_user_permissions(db, current_user.id, project_id)
    if Permissions.ADMIN_ALL not in current_perms:
        unauthorized = requested - current_perms
        if unauthorized:
            raise HTTPException(status_code=403, detail=f"Cannot grant permissions: {', '.join(sorted(unauthorized))}")

    permission_rows = db.query(models.Permission).filter(
        models.Permission.name.in_(requested)
    ).all()
    permission_by_name = {perm.name: perm for perm in permission_rows}
    missing = requested.difference(permission_by_name.keys())
    if missing:
        raise HTTPException(status_code=400, detail=f"Unknown permissions: {', '.join(sorted(missing))}")

    db.query(models.UserPermission).filter(
        models.UserPermission.user_id == user_id,
        models.UserPermission.project_id == project_id,
    ).delete()

    for perm in permission_by_name.values():
        db.add(
            models.UserPermission(
                user_id=user_id,
                permission_id=perm.id,
                project_id=project_id,
            )
        )
    db.commit()
    return {"status": "updated", "user_id": user_id, "project_id": project_id, "count": len(permission_by_name)}


class ProjectCreate(BaseModel):
    name: str
    owner_company_id: int

class OwnerCompanyCreate(BaseModel):
    name: constr(strip_whitespace=True, min_length=2, max_length=128)
    code: constr(strip_whitespace=True, min_length=2, max_length=32)

@app.post("/owner-companies", status_code=status.HTTP_201_CREATED)
def create_owner_company(
    payload: OwnerCompanyCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_company_create),
):
    normalized_code = payload.code.strip().upper()
    existing = db.query(models.OwnerCompany).filter(
        (models.OwnerCompany.name == payload.name) | (models.OwnerCompany.code == normalized_code)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Owner company name or code already exists")

    owner = models.OwnerCompany(name=payload.name, code=normalized_code)
    db.add(owner)
    db.commit()
    db.refresh(owner)
    return {"id": owner.id, "name": owner.name, "code": owner.code}

@app.post("/projects", status_code=status.HTTP_201_CREATED)
def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_project_create)
):
    owner = db.query(models.OwnerCompany).filter(
        models.OwnerCompany.id == project_data.owner_company_id
    ).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Owner company not found")
    
    new_project = models.Project(
        name=project_data.name,
        owner_id=project_data.owner_company_id
    )
    db.add(new_project)
    db.flush()  
    db.refresh(new_project)
    
    assignment = models.UserProjectAssignment(
        user_id=current_user.id,
        project_id=new_project.id
    )
    db.add(assignment)
    db.commit()
    db.refresh(new_project)

    if ADMIN_EMAIL:
        admin_user = db.query(models.User).filter(models.User.email == ADMIN_EMAIL).first()
        if admin_user:
            admin_role = db.query(models.Role).filter(models.Role.name == "admin").first()
            if admin_role:
                existing_role = db.query(models.UserRole).filter(
                    models.UserRole.user_id == admin_user.id,
                    models.UserRole.project_id == new_project.id,
                ).first()
                if not existing_role:
                    db.add(
                        models.UserRole(
                            user_id=admin_user.id,
                            role_id=admin_role.id,
                            project_id=new_project.id,
                        )
                    )
            admin_perm = db.query(models.Permission).filter(
                models.Permission.name == Permissions.ADMIN_ALL
            ).first()
            if admin_perm:
                existing_perm = db.query(models.UserPermission).filter(
                    models.UserPermission.user_id == admin_user.id,
                    models.UserPermission.permission_id == admin_perm.id,
                    models.UserPermission.project_id == new_project.id,
                ).first()
                if not existing_perm:
                    db.add(
                        models.UserPermission(
                            user_id=admin_user.id,
                            permission_id=admin_perm.id,
                            project_id=new_project.id,
                        )
                    )
            db.commit()
    
    return {
        "id": new_project.id,
        "name": new_project.name,
        "owner_company_name": owner.name
    }

@app.get("/owner-companies")
def get_owner_companies(db: Session = Depends(get_db)):
    companies = db.query(models.OwnerCompany).order_by(models.OwnerCompany.name.asc()).all()
    return [{"id": c.id, "name": c.name, "code": c.code} for c in companies]

@app.post("/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    project_id: int = Form(...),
    owner_company_id: int | None = Form(None),
    user_id: int | None = Form(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_document_upload)
):
    filename_lower = file.filename.lower()
    content_type = (file.content_type or "").lower()
    allowed_content_types = {
        "application/pdf",
        "application/x-pdf",
        "application/octet-stream",
    }
    if not filename_lower.endswith(".pdf") or (content_type and content_type not in allowed_content_types):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    if user_id is None:
        user_id = current_user.id
    
    if not has_permission(db, current_user.id, Permissions.DOCUMENT_UPLOAD, project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to upload documents to this project"
        )
    
    assignment = db.query(models.UserProjectAssignment).filter(
        models.UserProjectAssignment.user_id == user_id,
        models.UserProjectAssignment.project_id == project_id
    ).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="\u063a\u064a\u0631 \u0645\u0635\u0631\u062d \u0644\u0643 \u0628\u0627\u0644\u0631\u0641\u0639 \u0644\u0647\u0630\u0627 \u0627\u0644\u0645\u0634\u0631\u0648\u0639"
        )


    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if owner_company_id is None:
        owner_company_id = project.owner_id
    owner = db.query(models.OwnerCompany).filter(models.OwnerCompany.id == owner_company_id).first()
    if project.owner_id != owner_company_id:
        raise HTTPException(status_code=400, detail="Owner company does not match project owner")
    if not owner:
        raise HTTPException(status_code=404, detail="Owner Company not found")


    os.makedirs(STORAGE_DIR, exist_ok=True)
    def _sanitize_filename(name: str) -> str:
        base = os.path.basename(name or "")
        cleaned = "".join(
            ch if ch.isascii() and (ch.isalnum() or ch in {".", "-", "_"}) else "_"
            for ch in base
        )
        return cleaned or "document.pdf"

    original_name = os.path.basename(file.filename or "")
    safe_name = _sanitize_filename(original_name)


    new_doc = models.Document(
        filename=safe_name,
        original_filename=original_name,
        project_id=project_id,
        owner_company_id=owner_company_id,
    )
    db.add(new_doc)
    db.flush()
    db.refresh(new_doc)


    current_year = datetime.now().year
    serial = utils.generate_serial(owner.code, current_year, new_doc.id)
    new_doc.serial = serial


    input_path = os.path.join(STORAGE_DIR, f"temp_{new_doc.id}_{safe_name}")
    output_path = os.path.join(STORAGE_DIR, f"{serial}_{safe_name}")

    try:
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        utils.stamp_pdf(input_path, output_path, serial, project.name, owner.name)

        if supabase:
            with open(output_path, "rb") as f:
                destination = f"{serial}_{safe_name}"
                supabase.storage.from_(SUPABASE_BUCKET).upload(destination, f, {"content-type": "application/pdf"})

        db.commit()

    except Exception as e:
        db.rollback()

        try:
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Upload/stamp failed: {str(e)}")

    finally:
        try:
            if os.path.exists(input_path):
                os.remove(input_path)
            if supabase and os.path.exists(output_path):
                 os.remove(output_path)
        except Exception:
            pass

    base_url = str(request.base_url).rstrip("/") if request else ""
    download_url = f"{base_url}/documents/{new_doc.id}/download"
    verify_url = f"{base_url}/verify/{serial}"

    return {
        "status": "success",
        "serial": serial,
        "document_id": new_doc.id,
        "project_id": project_id,
        "download_url": download_url,
        "verify_url": verify_url,
        "project_name": project.name,
        "owner_company_name": owner.name,
    }


@app.get("/verify/{serial}")
def verify_document(
    serial: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    doc = db.query(models.Document).filter(
        models.Document.serial == serial
    ).first()

    if not doc:
        return {
            "valid": False,
            "message": "Document not found"
        }

    base_url = str(request.base_url).rstrip("/") if request else ""
    download_url = f"{base_url}/documents/{doc.id}/download"

    exists = False
    storage_path = None
    if supabase:
        try:
            res = supabase.storage.from_(SUPABASE_BUCKET).list(
                path="",
                options={"search": f"{doc.serial}_"},
            )
            if res:
                exact_name = f"{doc.serial}_{doc.filename}"
                match = next((item for item in res if item.get("name") == exact_name), None)
                storage_path = (match or res[0]).get("name")
                exists = True
            else:
                exists = False
        except Exception:
            exists = False

    return {
        "valid": True,
        "serial": doc.serial,
        "document_id": doc.id,
        "filename": doc.filename,
        "project_id": doc.project_id,
        "owner_company_id": doc.owner_company_id,
        "file_exists": exists,
        "storage_path": storage_path,
        "download_url": download_url,
    }


@app.get("/projects/{project_id}/documents")
def list_documents(
    project_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not has_permission(db, user.id, Permissions.DOCUMENT_READ, project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to read documents for this project"
        )
    if has_permission(db, user.id, Permissions.ADMIN_ALL, project_id):
        docs = db.query(models.Document).filter(models.Document.project_id == project_id).order_by(models.Document.id.desc()).all()
        return [
            {
                "id": d.id,
                "serial": d.serial,
                "filename": d.original_filename or d.filename,
                "upload_date": d.upload_date.isoformat() if d.upload_date else None,
            }
            for d in docs
        ]
    assignment = db.query(models.UserProjectAssignment).filter(
        models.UserProjectAssignment.user_id == user.id,
        models.UserProjectAssignment.project_id == project_id
    ).first()
    if not assignment:
        raise HTTPException(
            status_code=403,
            detail="\u063a\u064a\u0631 \u0645\u0635\u0631\u062d \u0644\u0643 \u0628\u0627\u0644\u0648\u0635\u0648\u0644 \u0625\u0644\u0649 \u0647\u0630\u0627 \u0627\u0644\u0645\u0634\u0631\u0648\u0639",
        )
    docs = db.query(models.Document).filter(models.Document.project_id == project_id).order_by(models.Document.id.desc()).all()


    return [
        {
            "id": d.id,
            "serial": d.serial,
            "filename": d.original_filename or d.filename,
            "upload_date": d.upload_date.isoformat() if d.upload_date else None,
        }
        for d in docs
    ]


@app.get("/documents")
def list_all_documents(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = (
        db.query(models.Document, models.Project)
        .join(models.Project, models.Document.project_id == models.Project.id)
        .order_by(models.Document.id.desc())
    )
    if not _has_admin_any_project(db, user.id):
        query = (
            query.join(
                models.UserProjectAssignment,
                models.UserProjectAssignment.project_id == models.Project.id,
            )
            .filter(models.UserProjectAssignment.user_id == user.id)
        )
    docs = query.all()
    return [
        {
            "id": doc.id,
            "serial": doc.serial,
            "filename": doc.original_filename or doc.filename,
            "upload_date": doc.upload_date.isoformat() if doc.upload_date else None,
            "project_id": project.id,
            "project_name": project.name,
        }
        for doc, project in docs
    ]


@app.get("/documents/export")
def export_documents(
    project_id: int | None = None,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = (
        db.query(models.Document, models.Project)
        .join(models.Project, models.Document.project_id == models.Project.id)
        .order_by(models.Document.id.desc())
    )
    if project_id:
        if not has_permission(db, user.id, Permissions.DOCUMENT_READ, project_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to export documents for this project"
            )
        query = query.filter(models.Document.project_id == project_id)
    else:
        if not _has_admin_any_project(db, user.id):
            query = (
                query.join(
                    models.UserProjectAssignment,
                    models.UserProjectAssignment.project_id == models.Project.id,
                )
                .filter(models.UserProjectAssignment.user_id == user.id)
            )
    rows = query.all()

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Documents"
    sheet.append(["Serial", "Filename", "Project", "Upload Date"])
    for doc, project in rows:
        sheet.append(
            [
                doc.serial,
                doc.original_filename or doc.filename,
                project.name,
                doc.upload_date.date().isoformat() if doc.upload_date else "",
            ]
        )

    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=\"documents.xlsx\""},
    )


@app.get("/documents/{document_id}/download")
def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc or not doc.serial:
        raise HTTPException(status_code=404, detail="Document not found")
    if not has_permission(db, current_user.id, Permissions.DOCUMENT_DOWNLOAD, doc.project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to download this document"
        )
    if has_permission(db, current_user.id, Permissions.ADMIN_ALL, doc.project_id):
        assignment = True
    else:
        assignment = db.query(models.UserProjectAssignment).filter(
            models.UserProjectAssignment.user_id == current_user.id,
            models.UserProjectAssignment.project_id == doc.project_id
        ).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this project"
        )

    download_name = doc.original_filename or doc.filename
    fallback_name = "".join(
        ch if ch.isascii() and (ch.isalnum() or ch in {".", "-", "_"}) else "_"
        for ch in download_name
    ) or "document.pdf"
    filename = f"{doc.serial}_{doc.filename}"
    content_disposition = (
        f"inline; filename=\"{fallback_name}\"; filename*=UTF-8''{quote(download_name)}"
    )
    
    if supabase:
        signed_url = None
        try:
            res = supabase.storage.from_(SUPABASE_BUCKET).create_signed_url(
                filename,
                SUPABASE_SIGNED_URL_TTL,
            )
            if isinstance(res, dict):
                signed_url = res.get("signedURL") or res.get("signedUrl") or res.get("signed_url")
        except Exception:
            signed_url = None

        if not signed_url:
            try:
                matches = supabase.storage.from_(SUPABASE_BUCKET).list(
                    path="",
                    options={"search": f"{doc.serial}_"},
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to locate file: {str(e)}")

            if matches:
                storage_name = matches[0].get("name")
                try:
                    res = supabase.storage.from_(SUPABASE_BUCKET).create_signed_url(
                        storage_name,
                        SUPABASE_SIGNED_URL_TTL,
                    )
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Failed to create signed URL: {str(e)}")
                if isinstance(res, dict):
                    signed_url = res.get("signedURL") or res.get("signedUrl") or res.get("signed_url")

        if not signed_url:
            raise HTTPException(status_code=500, detail="Signed URL generation failed")
        def _stream_from_url(url: str):
            try:
                with urllib.request.urlopen(url) as response:
                    while True:
                        chunk = response.read(1024 * 256)
                        if not chunk:
                            break
                        yield chunk
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}")

        return StreamingResponse(
            _stream_from_url(signed_url),
            media_type="application/pdf",
            headers={"Content-Disposition": content_disposition},
        )


class RoleAssignmentRequest(BaseModel):
    role_name: constr(strip_whitespace=True, min_length=2, max_length=64)


@app.post("/projects/{project_id}/users/{user_id}/roles")
def assign_user_role_to_project(
    project_id: int,
    user_id: int,
    payload: RoleAssignmentRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role_assign),
):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    target_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    current_role = get_user_highest_role(db, current_user.id, project_id)
    if not current_role:
        raise HTTPException(status_code=403, detail="Cannot assign role without a project role")
    current_rank = get_role_rank(current_role)
    target_rank = get_role_rank(payload.role_name)
    current_perms = get_user_permissions(db, current_user.id, project_id)
    if target_rank < current_rank and Permissions.ADMIN_ALL not in current_perms:
        raise HTTPException(status_code=403, detail="Cannot assign a higher role")

    user_role = assign_role_to_user(
        db=db,
        user_id=user_id,
        role_name=payload.role_name,
        project_id=project_id,
        admin_user_id=current_user.id,
    )
    return {
        "status": "assigned",
        "user_id": user_id,
        "project_id": project_id,
        "role_name": payload.role_name,
        "assignment_id": user_role.id,
    }


@app.delete("/projects/{project_id}/users/{user_id}/roles/{role_name}")
def remove_user_role_from_project(
    project_id: int,
    user_id: int,
    role_name: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role_assign),
):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    removed = remove_role_from_user(
        db=db,
        user_id=user_id,
        role_name=role_name,
        project_id=project_id,
    )
    if not removed:
        raise HTTPException(status_code=404, detail="Role assignment not found")
    return {"status": "removed", "user_id": user_id, "project_id": project_id, "role_name": role_name}




@app.delete("/documents/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if not has_permission(db, current_user.id, Permissions.DOCUMENT_DELETE, doc.project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this document"
        )
    assignment = db.query(models.UserProjectAssignment).filter(
        models.UserProjectAssignment.user_id == current_user.id,
        models.UserProjectAssignment.project_id == doc.project_id
    ).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this project"
        )

    storage_name = f"{doc.serial}_{doc.filename}" if doc.serial else None
    local_path = os.path.join(STORAGE_DIR, storage_name) if storage_name else None

    if supabase and storage_name:
        try:
            supabase.storage.from_(SUPABASE_BUCKET).remove([storage_name])
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(exc)}")
    if local_path and os.path.exists(local_path):
        try:
            os.remove(local_path)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to delete local file: {str(exc)}")

    db.delete(doc)
    db.commit()
    return {"status": "deleted", "document_id": document_id}
