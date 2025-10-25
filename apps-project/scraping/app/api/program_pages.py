from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

from app.models.program_page_raw import ProgramPageRaw
from db import get_db

router = APIRouter(prefix="/program-pages", tags=["Program Pages"])

class ProgramPageCreate(BaseModel):
    website_id: int
    url: str
    status: Optional[str] = "pending"
    http_code: Optional[int] = None
    content_hash: Optional[str] = None
    html: Optional[str] = None

@router.get("/")
def list_program_pages(db: Session = Depends(get_db)):
    return db.query(ProgramPageRaw).all()

@router.get("/{page_id}")
def get_program_page(page_id: UUID, db: Session = Depends(get_db)):
    page = db.query(ProgramPageRaw).filter(ProgramPageRaw.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Program page not found")
    return page

@router.post("/")
def create_program_page(data: ProgramPageCreate, db: Session = Depends(get_db)):
    page = ProgramPageRaw(**data.dict())
    db.add(page)
    db.commit()
    db.refresh(page)
    return page

@router.put("/{page_id}")
def update_program_page(page_id: UUID, data: ProgramPageCreate, db: Session = Depends(get_db)):
    page = db.query(ProgramPageRaw).filter(ProgramPageRaw.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Program page not found")
    for key, value in data.dict().items():
        setattr(page, key, value)
    db.commit()
    db.refresh(page)
    return page

@router.delete("/{page_id}")
def delete_program_page(page_id: UUID, db: Session = Depends(get_db)):
    page = db.query(ProgramPageRaw).filter(ProgramPageRaw.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Program page not found")
    db.delete(page)
    db.commit()
    return {"detail": "Program page deleted"}