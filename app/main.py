import os
import shutil
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import models, database, utils
from fastapi.responses import FileResponse


os.makedirs("storage", exist_ok=True)

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Document Control System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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

def get_current_user(db: Session) -> models.User:
    user = db.query(models.User).order_by(models.User.id.asc()).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/me")
def get_me(db: Session = Depends(get_db)):
    user = get_current_user(db)
    return {"id": user.id, "username": user.username}

@app.get("/me/projects")
def get_my_projects(db: Session = Depends(get_db)):
    user = get_current_user(db)
    projects = (
        db.query(models.Project)
        .join(models.UserProjectAssignment, models.UserProjectAssignment.project_id == models.Project.id)
        .filter(models.UserProjectAssignment.user_id == user.id)
        .order_by(models.Project.name.asc())
        .all()
    )
    return [
        {
            "id": project.id,
            "name": project.name,
            "owner_company_name": project.owner.name if project.owner else None,
        }
        for project in projects
    ]

@app.post("/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    project_id: int = Form(...),
    owner_company_id: int | None = Form(None),
    user_id: int | None = Form(None),
    db: Session = Depends(get_db)
):
    if file.content_type != "application/pdf" or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    if user_id is None:
        user = get_current_user(db)
        user_id = user.id
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


    os.makedirs("storage", exist_ok=True)
    safe_name = os.path.basename(file.filename)


    new_doc = models.Document(
        filename=safe_name,
        project_id=project_id,
        owner_company_id=owner_company_id,
    )
    db.add(new_doc)
    db.flush()
    db.refresh(new_doc)


    current_year = datetime.now().year
    serial = utils.generate_serial(owner.code, current_year, new_doc.id)
    new_doc.serial = serial


    input_path = f"storage/temp_{new_doc.id}_{safe_name}"
    output_path = f"storage/{serial}_{safe_name}"

    try:
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        utils.stamp_pdf(input_path, output_path, serial, project.name, owner.name)


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
def verify_document(serial: str, db: Session = Depends(get_db)):
    doc = db.query(models.Document).filter(
        models.Document.serial == serial
    ).first()

    if not doc:
        return {
            "valid": False,
            "message": "Document not found"
        }

    return {
        "valid": True,
        "serial": doc.serial,
        "document_id": doc.id,
        "filename": doc.filename,
        "project_id": doc.project_id,
        "owner_company_id": doc.owner_company_id,
    }


@app.get("/projects/{project_id}/documents")
def list_documents(project_id: int, db: Session = Depends(get_db)):
    user = get_current_user(db)
    assignment = db.query(models.UserProjectAssignment).filter(
        models.UserProjectAssignment.user_id == user.id,
        models.UserProjectAssignment.project_id == project_id
    ).first()
    if not assignment:
        raise HTTPException(status_code=403, detail="\u063a\u064a\u0631 \u0645\u0635\u0631\u062d \u0644\u0643 \u0628\u0627\u0644\u0648\u0635\u0648\u0644 \u0625\u0644\u0649 \u0647\u0630\u0627 \u0627\u0644\u0645\u0634\u0631\u0648\u0639")
    docs = db.query(models.Document).filter(models.Document.project_id == project_id).order_by(models.Document.id.desc()).all()


    return [
        {
            "id": d.id,
            "serial": d.serial,
            "filename": d.filename,
            "upload_date": d.upload_date.isoformat() if d.upload_date else None,
        }
        for d in docs
    ]


@app.get("/documents/{document_id}/download")
def download_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc or not doc.serial:
        raise HTTPException(status_code=404, detail="Document not found")

    # same naming convention used in upload
    file_path = f"storage/{doc.serial}_{doc.filename}"

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Stamped file missing on disk")

    # download_name is what the browser saves as
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=f"{doc.serial}_{doc.filename}",
        headers={"Content-Disposition": f'inline; filename="{doc.serial}_{doc.filename}"'}
    )
