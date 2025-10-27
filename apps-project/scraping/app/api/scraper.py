# app/api/scraper.py
import os
import requests

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from db import get_db
from app.models.website import Website
from app.models.scraper_job import ScraperJob  # 👈 modelo del job
from sqlalchemy import func

router = APIRouter()

class StartScraperRequest(BaseModel):
    website_id: int
    category: int  # 1 = academic, 2 = jobs
    max_depth: int = 2

@router.post("/start")
def start_scraper(request: StartScraperRequest, db: Session = Depends(get_db)):
    website = db.query(Website).filter(Website.id == request.website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    # 🚀 En lugar de ejecutar, creamos un registro de job pendiente
    job = ScraperJob(
        website_id=request.website_id,
        category=request.category,
        url=website.url,
        status="pending",
        started_at=func.now(),
        max_depth=request.max_depth
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    return {
        "message": "✅ Job registrado en cola",
        "job_id": job.id,
        "website_id": request.website_id,
        "category": request.category,
        "url": website.url,
        "max_depth": request.max_depth
    }

@router.post("/flaresolver")
def proxy_to_flaresolver(request: dict):
    """
    📡 Endpoint para redirigir una solicitud a FlareSolverr desde tu propio contenedor.
    """
    flaresolverr_url = os.getenv("FLARESOLVERR_URL", "http://compass_flaresolverr:8191/v1")

    try:
        # Reenviamos el body al FlareSolverr
        response = requests.post(flaresolverr_url, json=request, timeout=70)
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FlareSolverr request failed: {str(e)}")