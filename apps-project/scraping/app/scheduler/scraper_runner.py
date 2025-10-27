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
        db = None
        try:
            # Crear sesión para verificar y marcar jobs
            db = SessionLocal()

            # 🧭 1. Verificar si hay algún job en ejecución
            running_job = db.query(ScraperJob).filter(ScraperJob.status == "running").first()
            if running_job:
                logger.info(f"⏳ Ya hay un job corriendo (id={running_job.id}), esperando...")
                db.close()
                time.sleep(10)
                continue

            # 📝 2. Buscar primer job pendiente
            job = db.query(ScraperJob).filter_by(status="pending").order_by(ScraperJob.created_at).first()
            if not job:
                db.close()
                time.sleep(10)
                continue

            # 🚫 3. Evitar que corran múltiples jobs del mismo website
            already_running_for_site = db.query(ScraperJob).filter(
                ScraperJob.website_id == job.website_id,
                ScraperJob.status == "running"
            ).first()
            if already_running_for_site:
                logger.info(f"⚠️ Ya hay un job corriendo para website_id={job.website_id}, se salta este ciclo")
                db.close()
                time.sleep(10)
                continue

            website = db.query(Website).filter_by(id=job.website_id).first()
            if not website:
                logger.error(f"❌ Website con id={job.website_id} no encontrado. Marcando job como error.")
                job.status = "error"
                job.error = f"Website id={job.website_id} no encontrado"
                db.commit()
                db.close()
                time.sleep(10)
                continue

            # 🟡 4. Marcar job como en ejecución
            job.status = "running"
            job.started_at = func.now()
            db.commit()

            # Guardar datos necesarios antes de cerrar esta sesión
            job_id = job.id
            website_id = job.website_id
            website_url = website.url
            job_category = job.category
            job_max_depth = job.max_depth

            # Cerrar la sesión antes de iniciar el scraper
            db.close()
            db = None

            logger.info(f"🚀 Ejecutando job {job_id} para website_id={website_id}")

            # 🕷️ 5. Ejecutar el scraper correspondiente
            # El scraper crea su propia sesión internamente
            try:
                if job_category == 1:
                    scraper = AcademicScraper(start_url=website_url, max_depth=job_max_depth)
                else:
                    scraper = JobScraper(start_url=website_url, max_depth=job_max_depth)

                # Pasar job_id al scraper
                scraper.job_id = job_id
                scraper.run()

            except Exception as e:
                logger.error(f"💥 Error al ejecutar el scraper del job {job_id}: {e}")
                # Crear nueva sesión para actualizar el error
                try:
                    error_db = SessionLocal()
                    error_job = error_db.query(ScraperJob).filter_by(id=job_id).first()
                    if error_job:
                        error_job.status = "error"
                        error_job.error = str(e)[:500]
                        error_job.finished_at = func.now()
                        error_db.commit()
                    error_db.close()
                except Exception as update_error:
                    logger.error(f"💥 Error al actualizar estado de error del job {job_id}: {update_error}")

        except Exception as e:
            # 💥 Cualquier error inesperado del scheduler se captura aquí
            logger.error(f"💣 Error crítico en scheduler: {e}")
        finally:
            # Asegurar que la sesión se cierre si aún existe
            if db is not None:
                try:
                    db.close()
                except Exception as close_error:
                    logger.warning(f"⚠️ Error al cerrar sesión en finally: {close_error}")
            time.sleep(10)


def start_scheduler():
    """Inicia el thread de background para procesar jobs."""
    threading.Thread(target=process_jobs, daemon=True).start()