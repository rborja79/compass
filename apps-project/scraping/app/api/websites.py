from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.models.website import Website
from db import get_db

router = APIRouter(prefix="/websites", tags=["Websites"])

class WebsiteCreate(BaseModel):
    domain: str
    url: str
    tree: Optional[dict] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    institution: Optional[str] = None

@router.get("/")
def list_websites(db: Session = Depends(get_db)):
    return db.query(Website).all()

@router.get("/{website_id}")
def get_website(website_id: int, db: Session = Depends(get_db)):
    website = db.query(Website).filter(Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    return website

@router.post("/")
def create_website(data: WebsiteCreate, db: Session = Depends(get_db)):
    website = Website(**data.dict())
    db.add(website)
    db.commit()
    db.refresh(website)
    return website

@router.put("/{website_id}")
def update_website(website_id: int, data: WebsiteCreate, db: Session = Depends(get_db)):
    website = db.query(Website).filter(Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    for key, value in data.dict().items():
        setattr(website, key, value)
    db.commit()
    return website

@router.delete("/{website_id}")
def delete_website(website_id: int, db: Session = Depends(get_db)):
    website = db.query(Website).filter(Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    db.delete(website)
    db.commit()
    return {"detail": "Website deleted"}