from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.models.website_config import WebsiteConfig
from db import get_db

router = APIRouter(prefix="/websites/config", tags=["WebsiteConfig"])

class WebsiteConfigCreate(BaseModel):
    website_id: int
    total_results_selector: str = None
    pagination_pattern: str = None
    link_selector: str = None
    link_job: str = None
    link_pattern: str = None
    job_data_selector: str = None
    job_detail_selector: str = None
    jobs_per_page: int = None

@router.get("/")
def list_websites_config(db: Session = Depends(get_db)):
    return db.query(WebsiteConfig).all()

@router.get("/{website_config_id}")
def get_website_config(website_config_id: int, db: Session = Depends(get_db)):
    website_config = db.query(WebsiteConfig).filter(WebsiteConfig.id == website_config_id).first()
    if not website_config:
        raise HTTPException(status_code=404, detail="WebsiteConfig not found")
    return website_config

@router.post("/")
def create_website_config(data: WebsiteConfigCreate, db: Session = Depends(get_db)):
    website_config = WebsiteConfig(**data.dict())
    db.add(website_config)
    db.commit()
    db.refresh(website_config)
    return website_config

@router.put("/{website_config_id}")
def update_website_config(website_config_id: int, data: WebsiteConfigCreate, db: Session = Depends(get_db)):
    website_config = db.query(WebsiteConfig).filter(WebsiteConfig.id == website_config_id).first()
    if not website_config:
        raise HTTPException(status_code=404, detail="WebsiteConfig not found")
    for key, value in data.dict().items():
        setattr(website_config, key, value)
    db.commit()
    return website_config

@router.delete("/{website_config_id}")
def delete_website_config(website_config_id: int, db: Session = Depends(get_db)):
    website_config = db.query(WebsiteConfig).filter(WebsiteConfig.id == website_config_id).first()
    if not website_config:
        raise HTTPException(status_code=404, detail="WebsiteConfig not found")
    db.delete(website_config)
    db.commit()
    return {"detail": "WebsiteConfig deleted"}