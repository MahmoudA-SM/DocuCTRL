import os
import shutil
from datetime import datetime, timedelta
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from . import models, database, utils
from fastapi.responses import FileResponse, RedirectResponse
from supabase import create_client, Client
from pydantic import BaseModel, constr


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "docuctrl-files")
SUPABASE_SIGNED_URL_TTL = int(os.getenv("SUPABASE_SIGNED_URL_TTL", "300"))

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Use /tmp for ephemeral storage on cloud configurations
STORAGE_DIR = os.getenv("STORAGE_DIR", os.path.join(BASE_DIR, "storage"))
os.makedirs(STORAGE_DIR, exist_ok=True)

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Document Control System")

# Mount static files for React frontend
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

from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse, JSONResponse
from . import auth

# ... existing code ...

@app.get("/login", response_class=HTMLResponse)
def login_page():
    login_path = os.path.join(BASE_DIR, "frontend", "login.html")
    if not os.path.exists(login_path):
        return "Login page not found."
    with open(login_path, "r") as f:
        return f.read()

@app.post("/token")
async def login_for_access_token(response: RedirectResponse, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not user.hashed_password or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    
    # Return JSON but also set cookie for browser access
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

# Replace the dummy get_current_user with the real one
def get_current_user(request: Request, db: Session = Depends(get_db)) -> models.User:
    return auth.get_current_user(request, db)

@app.get("/")
def read_root():
    react_index = os.path.join(BASE_DIR, "frontend", "build", "index.html")
    if os.path.exists(react_index):
        return FileResponse(react_index)
    return RedirectResponse(url="/docs")

@app.get("/")
def read_root():
    return RedirectResponse(url="/docs")

@app.get("/me")
def get_me(user: models.User = Depends(get_current_user)):
    return {"id": user.id, "username": user.username}


class UserCreate(BaseModel):
    username: constr(strip_whitespace=True, min_length=3, max_length=64)
    password: constr(min_length=8, max_length=128)


@app.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.username == payload.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed_password = auth.get_password_hash(payload.password)
    user = models.User(username=payload.username, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "username": user.username}

@app.get("/me/projects")
def get_my_projects(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
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
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if file.content_type != "application/pdf" or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    if user_id is None:
        user_id = current_user.id
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


    input_path = os.path.join(STORAGE_DIR, f"temp_{new_doc.id}_{safe_name}")
    output_path = os.path.join(STORAGE_DIR, f"{serial}_{safe_name}")

    try:
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        utils.stamp_pdf(input_path, output_path, serial, project.name, owner.name)

        # Upload to Supabase
        if supabase:
            with open(output_path, "rb") as f:
                destination = f"{serial}_{safe_name}"
                # content_type="application/pdf"
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
        # Cleanup
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

    assignment = db.query(models.UserProjectAssignment).filter(
        models.UserProjectAssignment.user_id == current_user.id,
        models.UserProjectAssignment.project_id == doc.project_id,
    ).first()
    if not assignment:
        raise HTTPException(status_code=403, detail="Not authorized for this document")

    base_url = str(request.base_url).rstrip("/") if request else ""
    download_url = f"{base_url}/documents/{doc.id}/download"

    # Check existence
    exists = False
    if supabase:
        try:
            res = supabase.storage.from_(SUPABASE_BUCKET).list(path="", options={"search": f"{doc.serial}_{doc.filename}"})
            exists = len(res) > 0 if res else False
        except:
            exists = False
    else:
        file_path = os.path.join(STORAGE_DIR, f"{doc.serial}_{doc.filename}")
        exists = os.path.exists(file_path)

    return {
        "valid": True,
        "serial": doc.serial,
        "document_id": doc.id,
        "filename": doc.filename,
        "project_id": doc.project_id,
        "owner_company_id": doc.owner_company_id,
        "file_exists": exists,
        "download_url": download_url,
    }


@app.get("/projects/{project_id}/documents")
def list_documents(project_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
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
def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc or not doc.serial:
        raise HTTPException(status_code=404, detail="Document not found")

    assignment = db.query(models.UserProjectAssignment).filter(
        models.UserProjectAssignment.user_id == current_user.id,
        models.UserProjectAssignment.project_id == doc.project_id,
    ).first()
    if not assignment:
        raise HTTPException(status_code=403, detail="Not authorized for this document")

    filename = f"{doc.serial}_{doc.filename}"
    
    if supabase:
        try:
            res = supabase.storage.from_(SUPABASE_BUCKET).create_signed_url(
                filename,
                SUPABASE_SIGNED_URL_TTL,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create signed URL: {str(e)}")

        signed_url = None
        if isinstance(res, dict):
            signed_url = res.get("signedURL") or res.get("signedUrl") or res.get("signed_url")
        if not signed_url:
            raise HTTPException(status_code=500, detail="Signed URL generation failed")
        return RedirectResponse(url=signed_url)
    else:
        file_path = os.path.join(STORAGE_DIR, filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Stamped file missing on disk")

        return FileResponse(
            path=file_path,
            media_type="application/pdf",
            filename=filename,
            headers={"Content-Disposition": f'inline; filename="{filename}"'}
        )
