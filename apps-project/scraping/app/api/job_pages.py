from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

from app.models.job_page_raw import JobPageRaw
from db import get_db

router = APIRouter(prefix="/job-pages", tags=["Job Pages"])

# 📌 Modelo de entrada (Request)
class JobPageCreate(BaseModel):
    website_id: int
    url: str
    status: Optional[str] = "pending"
    http_code: Optional[int] = None
    content_hash: Optional[str] = None
    html: Optional[str] = None

# 📥 Listar todos los registros
@router.get("/")
def list_job_pages(db: Session = Depends(get_db)):
    return db.query(JobPageRaw).all()

# 📥 Obtener un registro por ID
@router.get("/{page_id}")
def get_job_page(page_id: UUID, db: Session = Depends(get_db)):
    page = db.query(JobPageRaw).filter(JobPageRaw.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Job page not found")
    return page

# ➕ Crear un nuevo registro
@router.post("/")
def create_job_page(data: JobPageCreate, db: Session = Depends(get_db)):
    page = JobPageRaw(**data.dict())
    db.add(page)
    db.commit()
    db.refresh(page)
    return page

# ✏️ Actualizar un registro existente
@router.put("/{page_id}")
def update_job_page(page_id: UUID, data: JobPageCreate, db: Session = Depends(get_db)):
    page = db.query(JobPageRaw).filter(JobPageRaw.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Job page not found")
    for key, value in data.dict().items():
        setattr(page, key, value)
    db.commit()
    db.refresh(page)
    return page

# 🗑️ Eliminar un registro
@router.delete("/{page_id}")
def delete_job_page(page_id: UUID, db: Session = Depends(get_db)):
    page = db.query(JobPageRaw).filter(JobPageRaw.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Job page not found")
    db.delete(page)
    db.commit()
    return {"detail": "Job page deleted"}