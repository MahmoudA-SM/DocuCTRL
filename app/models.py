from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Sequence, func, UniqueConstraint
from sqlalchemy.orm import relationship
from .database import Base


doc_id_seq = Sequence('documents_id_seq', start=2, metadata=Base.metadata)

class OwnerCompany(Base):
    __tablename__ = "owner_companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    code = Column(String, unique=True, index=True)

    projects = relationship("Project", back_populates="owner")
    documents = relationship("Document", back_populates="owner")

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)

    owner_id = Column(Integer, ForeignKey("owner_companies.id"))

    owner = relationship("OwnerCompany", back_populates="projects")
    documents = relationship("Document", back_populates="project")
    assigned_users = relationship("UserProjectAssignment", back_populates="project")
    user_roles = relationship("UserRole", back_populates="project")
    user_permissions = relationship("UserPermission", back_populates="project")

class Document(Base):
    __tablename__ = "documents"


    id = Column(Integer, doc_id_seq, server_default=doc_id_seq.next_value(), primary_key=True, index=True)
    serial = Column(String, unique=True, index=True)
    filename = Column(String)
    original_filename = Column(String)
    upload_date = Column(DateTime, server_default=func.now())
    
    project_id = Column(Integer, ForeignKey("projects.id"))
    owner_company_id = Column(Integer, ForeignKey("owner_companies.id"))

    project = relationship("Project", back_populates="documents")
    owner = relationship("OwnerCompany", back_populates="documents")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    assignments = relationship("UserProjectAssignment", back_populates="user")
    roles = relationship("UserRole", back_populates="user")
    permissions = relationship("UserPermission", back_populates="user")

class UserProjectAssignment(Base):
    __tablename__ = "user_project_assignments"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), primary_key=True)

    user = relationship("User", back_populates="assignments")
    project = relationship("Project", back_populates="assigned_users")



class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)

    users = relationship("UserRole", back_populates="role")
    permissions = relationship("RolePermission", back_populates="role")

    def __repr__(self):
        return f"<Role(name='{self.name}')>"


class Permission(Base):
    __tablename__ = "permissions"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    resource = Column(String)
    action = Column(String)

    roles = relationship("RolePermission", back_populates="permission")
    users = relationship("UserPermission", back_populates="permission")

    def __repr__(self):
        return f"<Permission(name='{self.name}')>"


class RolePermission(Base):
    __tablename__ = "role_permissions"
    role_id = Column(Integer, ForeignKey("roles.id"), primary_key=True)
    permission_id = Column(Integer, ForeignKey("permissions.id"), primary_key=True)

    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission", back_populates="roles")


class UserRole(Base):
    __tablename__ = "user_roles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)

    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users")
    project = relationship("Project", back_populates="user_roles")

    __table_args__ = (
        UniqueConstraint('user_id', 'role_id', 'project_id', name='uix_user_role_project'),
    )


class UserPermission(Base):
    __tablename__ = "user_permissions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    permission_id = Column(Integer, ForeignKey("permissions.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    user = relationship("User", back_populates="permissions")
    permission = relationship("Permission", back_populates="users")
    project = relationship("Project", back_populates="user_permissions")

    __table_args__ = (
        UniqueConstraint('user_id', 'permission_id', 'project_id', name='uix_user_permission_project'),
    )