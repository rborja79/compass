# app/scheduler/scraper_runner.py
import threading
import time
import logging
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from db import SessionLocal
from app.models.scraper_job import ScraperJob
from app.models.website import Website
from app.scraper.academic_scraper import AcademicScraper
from app.scraper.job_scraper import JobScraper

logger = logging.getLogger("ScraperRunner")
logger.setLevel(logging.INFO)


def process_jobs():
    """Loop infinito que revisa la cola de jobs y ejecuta uno a la vez."""
    while True:
        try:
            # Usar context manager para asegurar cierre de sesión SIEMPRE
            with SessionLocal() as db:
                # 🧭 1. Verificar si hay algún job en ejecución
                running_job = db.query(ScraperJob).filter(ScraperJob.status == "running").first()
                if running_job:
                    logger.info(f"⏳ Ya hay un job corriendo (id={running_job.id}), esperando...")
                    time.sleep(10)
                    continue

                # 📝 2. Buscar primer job pendiente
                job = db.query(ScraperJob).filter_by(status="pending").order_by(ScraperJob.created_at).first()
                if not job:
                    time.sleep(10)
                    continue

                # 🚫 3. Evitar que corran múltiples jobs del mismo website
                already_running_for_site = db.query(ScraperJob).filter(
                    ScraperJob.website_id == job.website_id,
                    ScraperJob.status == "running"
                ).first()
                if already_running_for_site:
                    logger.info(f"⚠️ Ya hay un job corriendo para website_id={job.website_id}, se salta este ciclo")
                    time.sleep(10)
                    continue

                website = db.query(Website).filter_by(id=job.website_id).first()
                if not website:
                    logger.error(f"❌ Website con id={job.website_id} no encontrado. Marcando job como error.")
                    job.status = "error"
                    job.error = f"Website id={job.website_id} no encontrado"
                    db.commit()
                    time.sleep(10)
                    continue

                # 🟡 4. Marcar job como en ejecución
                job.status = "running"
                job.started_at = func.now()
                db.commit()

                logger.info(f"🚀 Ejecutando job {job.id} para website_id={job.website_id}")

                # 🕷️ 5. Ejecutar el scraper correspondiente
                try:
                    if job.category == 1:
                        scraper = AcademicScraper(start_url=website.url, max_depth=job.max_depth)
                    else:
                        scraper = JobScraper(start_url=website.url, max_depth=job.max_depth)

                    # Pasar job_id al scraper
                    scraper.job_id = job.id
                    scraper.run()

                    # ❌ No actualizamos aquí — el scraper se encarga de poner "finished" o "error".
                except Exception as e:
                    job.status = "error"
                    job.error = str(e)
                    db.commit()
                    logger.error(f"💥 Error al ejecutar el scraper del job {job.id}: {e}")

        except Exception as e:
            # 💥 Cualquier error inesperado del scheduler se captura aquí
            logger.error(f"💣 Error crítico en scheduler: {e}")
            time.sleep(10)


def start_scheduler():
    """Inicia el thread de background para procesar jobs."""
    threading.Thread(target=process_jobs, daemon=True).start()