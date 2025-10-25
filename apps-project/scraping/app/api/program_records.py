from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
from uuid import UUID

from app.models.program_record import ProgramRecord
from db import get_db

router = APIRouter(prefix="/program-records", tags=["Program Records"])

# 📝 Modelo de entrada
class ProgramRecordCreate(BaseModel):
    page_id: UUID
    program_name: Optional[str] = None
    level: Optional[str] = None
    modality: Optional[str] = None
    duration: Optional[str] = None
    price: Optional[str] = None
    subjects: Optional[Dict[str, Any]] = None
    description: Optional[str] = None

    # ✨ Campos NLP
    tags: Optional[Dict[str, Any]] = None
    skills_target: Optional[Dict[str, Any]] = None
    profession_target: Optional[str] = None


# 📥 Listar todos los registros
@router.get("/")
def list_program_records(db: Session = Depends(get_db)):
    return db.query(ProgramRecord).all()


# 📥 Obtener un registro por ID
@router.get("/{record_id}")
def get_program_record(record_id: UUID, db: Session = Depends(get_db)):
    record = db.query(ProgramRecord).filter(ProgramRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Program record not found")
    return record


# ➕ Crear un nuevo registro
@router.post("/")
def create_program_record(data: ProgramRecordCreate, db: Session = Depends(get_db)):
    record = ProgramRecord(**data.dict())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


# ✏️ Actualizar un registro existente
@router.put("/{record_id}")
def update_program_record(record_id: UUID, data: ProgramRecordCreate, db: Session = Depends(get_db)):
    record = db.query(ProgramRecord).filter(ProgramRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Program record not found")
    for key, value in data.dict().items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return record


# 🗑️ Eliminar un registro
@router.delete("/{record_id}")
def delete_program_record(record_id: UUID, db: Session = Depends(get_db)):
    record = db.query(ProgramRecord).filter(ProgramRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Program record not found")
    db.delete(record)
    db.commit()
    return {"detail": "Program record deleted"}