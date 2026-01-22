from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Sequence, func
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

class UserProjectAssignment(Base):
    __tablename__ = "user_project_assignments"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), primary_key=True)

    user = relationship("User", back_populates="assignments")
    project = relationship("Project", back_populates="assigned_users")
