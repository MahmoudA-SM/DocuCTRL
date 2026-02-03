
from functools import wraps
from typing import List, Optional, Set
from datetime import datetime

from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from . import models, database
from .auth import get_current_user


class AuthenticationError(HTTPException):
    def __init__(self, detail: str = "Authentication required"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class PermissionDenied(HTTPException):
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class Permissions:
    
    DOCUMENT_UPLOAD = "document:upload"
    DOCUMENT_READ = "document:read"
    DOCUMENT_UPDATE = "document:update"
    DOCUMENT_DELETE = "document:delete"
    DOCUMENT_DOWNLOAD = "document:download"
    
    PROJECT_CREATE = "project:create"
    PROJECT_READ = "project:read"
    PROJECT_UPDATE = "project:update"
    PROJECT_DELETE = "project:delete"
    PROJECT_MANAGE = "project:manage"
    
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_INVITE = "user:invite"
    USER_MANAGE = "user:manage"
    
    ROLE_CREATE = "role:create"
    ROLE_READ = "role:read"
    ROLE_UPDATE = "role:update"
    ROLE_DELETE = "role:delete"
    ROLE_MANAGE = "role:manage"
    ROLE_ASSIGN = "role:assign"
    
    COMPANY_CREATE = "company:create"
    COMPANY_READ = "company:read"
    COMPANY_UPDATE = "company:update"
    COMPANY_DELETE = "company:delete"
    COMPANY_MANAGE = "company:manage"
    
    ADMIN_ALL = "admin:all"
    SYSTEM_SETTINGS = "system:settings"


ROLE_HIERARCHY = ["admin", "manager", "uploader", "viewer"]
ROLE_RANK = {name: idx for idx, name in enumerate(ROLE_HIERARCHY)}

DEFAULT_ROLES = [
    (
        "admin",
        "Full system administrator with all permissions",
        [
            Permissions.DOCUMENT_UPLOAD,
            Permissions.DOCUMENT_READ,
            Permissions.DOCUMENT_UPDATE,
            Permissions.DOCUMENT_DELETE,
            Permissions.DOCUMENT_DOWNLOAD,
            Permissions.PROJECT_CREATE,
            Permissions.PROJECT_READ,
            Permissions.PROJECT_UPDATE,
            Permissions.PROJECT_DELETE,
            Permissions.PROJECT_MANAGE,
            Permissions.USER_CREATE,
            Permissions.USER_READ,
            Permissions.USER_UPDATE,
            Permissions.USER_DELETE,
            Permissions.USER_INVITE,
            Permissions.USER_MANAGE,
            Permissions.ROLE_CREATE,
            Permissions.ROLE_READ,
            Permissions.ROLE_UPDATE,
            Permissions.ROLE_DELETE,
            Permissions.ROLE_MANAGE,
            Permissions.ROLE_ASSIGN,
            Permissions.COMPANY_CREATE,
            Permissions.COMPANY_READ,
            Permissions.COMPANY_UPDATE,
            Permissions.COMPANY_DELETE,
            Permissions.COMPANY_MANAGE,
            Permissions.ADMIN_ALL,
            Permissions.SYSTEM_SETTINGS,
        ]
    ),
    (
        "manager",
        "Project manager - can manage projects, invite users, and manage documents",
        [
            Permissions.DOCUMENT_UPLOAD,
            Permissions.DOCUMENT_READ,
            Permissions.DOCUMENT_UPDATE,
            Permissions.DOCUMENT_DOWNLOAD,
            Permissions.PROJECT_CREATE,
            Permissions.PROJECT_READ,
            Permissions.PROJECT_UPDATE,
            Permissions.PROJECT_MANAGE,
            Permissions.USER_READ,
            Permissions.USER_INVITE,
            Permissions.ROLE_READ,
            Permissions.ROLE_ASSIGN,
            Permissions.COMPANY_CREATE,
            Permissions.COMPANY_READ,
        ]
    ),
    (
        "uploader",
        "Document uploader - can upload and view documents",
        [
            Permissions.DOCUMENT_UPLOAD,
            Permissions.DOCUMENT_READ,
            Permissions.DOCUMENT_DOWNLOAD,
            Permissions.PROJECT_READ,
            Permissions.USER_READ,
        ]
    ),
    (
        "viewer",
        "Read-only user - can view and download documents",
        [
            Permissions.DOCUMENT_READ,
            Permissions.DOCUMENT_DOWNLOAD,
            Permissions.PROJECT_READ,
            Permissions.USER_READ,
        ]
    ),
]


def seed_rbac_data(db: Session) -> None:
    
    for role_name, description, perm_names in DEFAULT_ROLES:
        role = db.query(models.Role).filter(models.Role.name == role_name).first()
        if not role:
            role = models.Role(name=role_name, description=description)
            db.add(role)
            db.flush()
        else:
            role.description = description
            db.flush()
        
        for perm_name in perm_names:
            perm = db.query(models.Permission).filter(
                models.Permission.name == perm_name
            ).first()
            
            if not perm:
                parts = perm_name.split(":")
                resource = parts[0] if len(parts) > 0 else "unknown"
                action = parts[1] if len(parts) > 1 else "unknown"
                
                perm = models.Permission(
                    name=perm_name,
                    resource=resource,
                    action=action
                )
                db.add(perm)
                db.flush()
            
            existing_link = db.query(models.RolePermission).filter(
                models.RolePermission.role_id == role.id,
                models.RolePermission.permission_id == perm.id
            ).first()
            
            if not existing_link:
                db.add(models.RolePermission(
                    role_id=role.id,
                    permission_id=perm.id
                ))
    
    db.commit()


def get_user_roles(
    db: Session,
    user_id: int,
    project_id: Optional[int] = None
) -> List[models.Role]:
    
    if project_id is None:
        return []
    query = db.query(models.Role).join(models.UserRole).filter(
        models.UserRole.user_id == user_id
    )
    
    if project_id is not None:
        query = query.filter(models.UserRole.project_id == project_id)
    
    return query.distinct().all()


def get_user_permissions(
    db: Session,
    user_id: int,
    project_id: Optional[int] = None
) -> Set[str]:
    
    roles = get_user_roles(db, user_id, project_id)
    permissions = set()
    
    for role in roles:
        for role_perm in role.permissions:
            permissions.add(role_perm.permission.name)

    if project_id is not None:
        direct_perms = db.query(models.Permission.name).join(
            models.UserPermission,
            models.UserPermission.permission_id == models.Permission.id,
        ).filter(
            models.UserPermission.user_id == user_id,
            models.UserPermission.project_id == project_id,
        ).all()
        for (perm_name,) in direct_perms:
            permissions.add(perm_name)
    
    return permissions


def has_permission(
    db: Session,
    user_id: int,
    permission: str,
    project_id: Optional[int] = None
) -> bool:
    
    user_perms = get_user_permissions(db, user_id, project_id)
    
    if Permissions.ADMIN_ALL in user_perms:
        return True
    
    return permission in user_perms


def require_permission(*permissions: str):
    
    async def permission_checker(
        request: Request,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(database.get_db)
    ):
        project_id = None
        try:
            project_id = request.path_params.get("project_id")
            if project_id:
                project_id = int(project_id)
        except (ValueError, TypeError):
            pass
        
        if project_id is None:
            try:
                project_id = request.query_params.get("project_id")
                if project_id:
                    project_id = int(project_id)
            except (ValueError, TypeError):
                pass
        
        if project_id is None and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.json()
                project_id = body.get("project_id")
                if project_id:
                    project_id = int(project_id)
            except Exception:
                pass
        
        user_perms = get_user_permissions(db, current_user.id, project_id)
        
        if Permissions.ADMIN_ALL in user_perms:
            return current_user
        
        for perm in permissions:
            if perm in user_perms:
                return current_user
        
        raise PermissionDenied(
            f"Permission denied. Required: {', '.join(permissions)}"
        )
    
    return permission_checker


def require_all_permissions(*permissions: str):
    
    async def permission_checker(
        request: Request,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(database.get_db)
    ):
        project_id = None
        try:
            project_id = request.path_params.get("project_id")
            if project_id:
                project_id = int(project_id)
        except (ValueError, TypeError):
            pass
        
        if project_id is None:
            try:
                project_id = request.query_params.get("project_id")
                if project_id:
                    project_id = int(project_id)
            except (ValueError, TypeError):
                pass
        
        user_perms = get_user_permissions(db, current_user.id, project_id)
        
        if Permissions.ADMIN_ALL in user_perms:
            return current_user
        
        missing = [p for p in permissions if p not in user_perms]
        if missing:
            raise PermissionDenied(
                f"Permission denied. Missing: {', '.join(missing)}"
            )
        
        return current_user
    
    return permission_checker


def assign_role_to_user(
    db: Session,
    user_id: int,
    role_name: str,
    project_id: Optional[int] = None,
    admin_user_id: Optional[int] = None
) -> models.UserRole:
    
    if project_id is None:
        raise HTTPException(status_code=400, detail="project_id is required for role assignment")
    role = db.query(models.Role).filter(models.Role.name == role_name).first()
    if not role:
        raise HTTPException(status_code=404, detail=f"Role '{role_name}' not found")
    
    existing_project_role = db.query(models.UserRole).filter(
        models.UserRole.user_id == user_id,
        models.UserRole.project_id == project_id
    ).first()
    if existing_project_role:
        raise HTTPException(status_code=400, detail="User already has a role for this project")
    
    existing = db.query(models.UserRole).filter(
        models.UserRole.user_id == user_id,
        models.UserRole.role_id == role.id,
        models.UserRole.project_id == project_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"User already has role '{role_name}'" + 
                   (f" for this project" if project_id else "")
        )
    
    user_role = models.UserRole(
        user_id=user_id,
        role_id=role.id,
        project_id=project_id
    )
    db.add(user_role)
    db.commit()
    db.refresh(user_role)
    
    return user_role


def remove_role_from_user(
    db: Session,
    user_id: int,
    role_name: str,
    project_id: Optional[int] = None
) -> bool:
    
    if project_id is None:
        return False
    role = db.query(models.Role).filter(models.Role.name == role_name).first()
    if not role:
        return False
    
    user_role = db.query(models.UserRole).filter(
        models.UserRole.user_id == user_id,
        models.UserRole.role_id == role.id,
        models.UserRole.project_id == project_id
    ).first()
    
    if user_role:
        db.delete(user_role)
        db.commit()
        return True
    
    return False


def get_user_effective_role(
    db: Session,
    user_id: int,
    project_id: Optional[int] = None
) -> Optional[str]:
    
    user_roles = get_user_roles(db, user_id, project_id)
    
    if not user_roles:
        return None
    
    user_role_names = {r.name for r in user_roles}
    
    for role_name in ROLE_HIERARCHY:
        if role_name in user_role_names:
            return role_name
    
    return next(iter(user_role_names)) if user_role_names else None


def get_role_rank(role_name: Optional[str]) -> int:
    
    if not role_name:
        return len(ROLE_HIERARCHY)
    return ROLE_RANK.get(role_name, len(ROLE_HIERARCHY))


def get_user_highest_role(
    db: Session,
    user_id: int,
    project_id: Optional[int] = None
) -> Optional[str]:
    
    user_roles = get_user_roles(db, user_id, project_id)
    if not user_roles:
        return None
    best_role = None
    best_rank = len(ROLE_HIERARCHY)
    for role in user_roles:
        rank = get_role_rank(role.name)
        if rank < best_rank:
            best_rank = rank
            best_role = role.name
    return best_role
