import os
import shutil
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.orm import Session
from . import models, database, utils


os.makedirs("storage", exist_ok=True)

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Document Control System")

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

    return x_user_id

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    project_id: int = Form(...),
    owner_company_id: int = Form(...),
    user_id: int = Form(...),
    db: Session = Depends(get_db)
):

    assignment = db.query(models.UserProjectAssignment).filter(
        models.UserProjectAssignment.user_id == user_id,
        models.UserProjectAssignment.project_id == project_id
    ).first()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not assigned to this project")


    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    owner = db.query(models.OwnerCompany).filter(models.OwnerCompany.id == owner_company_id).first()
    if not project or not owner:
        raise HTTPException(status_code=404, detail="Project or Owner Company not found")


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

        utils.stamp_pdf(input_path, output_path, serial, project.name)


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

    return {"status": "success", "serial": serial, "document_id": new_doc.id}


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
        "filename": doc.filename,
        "project_id": doc.project_id,
        "owner_company_id": doc.owner_company_id,
    }


@app.get("/projects/{project_id}/documents")
def list_documents(project_id: int, db: Session = Depends(get_db)):
    docs = db.query(models.Document).filter(
        models.Document.project_id == project_id
    ).all()

    return [
        {
            "id": d.id,
            "serial": d.serial,
            "filename": d.filename
        }
        for d in docs
    ]
