from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from app.models.job_record import JobRecord
from db import get_db

router = APIRouter(prefix="/job-records", tags=["Job Records"])

# 📝 Modelo de entrada
class JobRecordCreate(BaseModel):
    page_id: UUID
    domain: Optional[str] = None
    job_title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    salary: Optional[str] = None
    posted_at: Optional[datetime] = None
    tags: Optional[Dict[str, Any]] = None
    description: Optional[str] = None

    # ✨ Campos NLP
    profession: Optional[str] = None
    skills_hard: Optional[Dict[str, Any]] = None
    skills_soft: Optional[Dict[str, Any]] = None
    experience_level: Optional[str] = None
    years_experience: Optional[str] = None
    salary_min: Optional[str] = None
    salary_max: Optional[str] = None
    salary_currency: Optional[str] = None
    salary_period: Optional[str] = None

# 📥 Listar todos los registros
@router.get("/")
def list_job_records(db: Session = Depends(get_db)):
    return db.query(JobRecord).all()

# 📥 Obtener un registro por ID
@router.get("/{record_id}")
def get_job_record(record_id: UUID, db: Session = Depends(get_db)):
    record = db.query(JobRecord).filter(JobRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Job record not found")
    return record

# ➕ Crear un nuevo registro
@router.post("/")
def create_job_record(data: JobRecordCreate, db: Session = Depends(get_db)):
    record = JobRecord(**data.dict())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

# ✏️ Actualizar un registro existente
@router.put("/{record_id}")
def update_job_record(record_id: UUID, data: JobRecordCreate, db: Session = Depends(get_db)):
    record = db.query(JobRecord).filter(JobRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Job record not found")
    for key, value in data.dict().items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return record

# 🗑️ Eliminar un registro
@router.delete("/{record_id}")
def delete_job_record(record_id: UUID, db: Session = Depends(get_db)):
    record = db.query(JobRecord).filter(JobRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Job record not found")
    db.delete(record)
    db.commit()
    return {"detail": "Job record deleted"}