import os
from fastapi import FastAPI
from db import engine, Base, SessionLocal
from app.seed import seed_from_csv
from app.scheduler.scraper_runner import start_scheduler

# 🔹 Importa tus routers
from app.api import (
    categories,
    websites,
    website_config,
    program_pages,
    program_records,
    job_pages,
    job_records,
    scraper_jobs,
    scraper
)

# 🏗️ Inicializa la base de datos
Base.metadata.create_all(bind=engine)

# 🧪 Ejecutar seed automático si la BD está vacía
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

session = SessionLocal()
seed_from_csv(session, base_path=DATA_DIR)
session.close()

# 🚀 Crea la instancia FastAPI
app = FastAPI(
    title="Scraper API",
    version="1.0.0",
    description="API para gestionar fuentes, páginas, registros y scraping jobs"
)

# 🧭 Monta los routers
app.include_router(categories.router)
app.include_router(websites.router)
app.include_router(website_config.router)
app.include_router(program_pages.router)
app.include_router(program_records.router)
app.include_router(job_pages.router)
app.include_router(job_records.router)
app.include_router(scraper_jobs.router)
app.include_router(scraper.router)

# 🩺 Healthcheck simple
@app.get("/health")
def healthcheck():
    return {"status": "ok"}

@app.on_event("startup")
def startup_event():
    start_scheduler()