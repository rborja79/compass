from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from db import get_db
from app.models.scraper_job import ScraperJob

router = APIRouter(prefix="/scraper-jobs", tags=["Scraper Jobs"])

# ================================
# 🧾 Pydantic Schemas
# ================================
class ScraperJobBase(BaseModel):
    website_id: Optional[int] = None
    category: Optional[int] = None       # 1 = academic, 2 = jobs
    url: str
    status: Optional[str] = "pending"    # pending|running|finished|error|timeout
    error: Optional[str] = None

class ScraperJobUpdate(BaseModel):
    status: Optional[str] = None
    error: Optional[str] = None


# ================================
# 📌 CRUD Endpoints
# ================================
@router.get("/")
def list_jobs(db: Session = Depends(get_db)):
    """📄 Listar todos los scraper jobs"""
    return db.query(ScraperJob).order_by(ScraperJob.created_at.desc()).all()


@router.get("/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db)):
    """🔎 Obtener un job por ID"""
    job = db.query(ScraperJob).filter(ScraperJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="ScraperJob not found")
    return job


@router.post("/")
def create_job(job_data: ScraperJobBase, db: Session = Depends(get_db)):
    """➕ Crear un nuevo job"""
    job = ScraperJob(**job_data.dict())
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.put("/{job_id}")
def update_job(job_id: int, job_data: ScraperJobUpdate, db: Session = Depends(get_db)):
    """✏️ Actualizar estado o error de un job"""
    job = db.query(ScraperJob).filter(ScraperJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="ScraperJob not found")
    for key, value in job_data.dict(exclude_unset=True).items():
        setattr(job, key, value)
    db.commit()
    db.refresh(job)
    return job


@router.delete("/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db)):
    """🗑️ Eliminar un job"""
    job = db.query(ScraperJob).filter(ScraperJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="ScraperJob not found")
    db.delete(job)
    db.commit()
    return {"detail": f"ScraperJob {job_id} deleted successfully"}