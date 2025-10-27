# app/scraper/base_scraper.py
import os
import threading
import time
import random
import logging
import hashlib
import requests
import cloudscraper
from logging.handlers import RotatingFileHandler
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import tldextract
from sqlalchemy.orm import Session
from sqlalchemy import func

# ORM Models
from app.models.website import Website
from app.models.scraper_job import ScraperJob
from app.models.program_page_raw import ProgramPageRaw
from app.models.job_page_raw import JobPageRaw
from db import SessionLocal

# ==========================
# 📝 LOGGING CONFIG
# ==========================
logger = logging.getLogger("ScraperLogger")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler("logs/scraper.log", maxBytes=5*1024*1024, backupCount=3)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def clean_html(content: str) -> str:
    """Limpia caracteres NUL (\x00) y otros potencialmente problemáticos antes de guardar en la base de datos."""
    if content is None:
        return ""
    return content.replace("\x00", "")


class BaseScraper:
    def __init__(self, start_url: str, max_depth=2, delay=(1, 3), proxies=None, category=1):
        self.start_url = start_url
        self.max_depth = max_depth
        self.visited = set()
        self.tree = []
        self.job_id = None
        self.ua = UserAgent()
        self.delay_min, self.delay_max = delay
        self.session = cloudscraper.create_scraper()
        self.proxies = proxies or []
        self.proxy_index = 0
        self.category = category  # 1=Academic / 2=Jobs
        self.db: Session = SessionLocal()

        ext = tldextract.extract(self.start_url)
        self.base_domain = f"{ext.domain}.{ext.suffix}"
        website = self.db.query(Website).filter_by(domain=self.base_domain).first()
        self.website_id = website.id if website else None

        self.flaresolverr_url = os.getenv("FLARESOLVERR_URL", "http://compass_flaresolverr:8191/v1")
        logger.info(f"🕷️ Scraper inicializado para dominio: {self.base_domain}")

    # ==========================
    # 🌐 Network & proxy
    # ==========================
    def choose_proxy(self):
        if not self.proxies:
            return None
        p = self.proxies[self.proxy_index % len(self.proxies)]
        self.proxy_index += 1
        return {"http": p, "https": p} if isinstance(p, str) else p

    def get_page(self, url, referer=None):
        headers = {
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Upgrade-Insecure-Requests": "1",
            "Referer": referer or "https://www.google.com/"
        }
        proxy = self.choose_proxy()
        try:
            r = self.session.get(url, headers=headers, proxies=proxy, timeout=20)
            r.raise_for_status()
            if "cloudflare" in r.text.lower() or r.status_code in [403, 503]:
                logger.warning(f"[Cloudflare] {url} protegido — intentando FlareSolverr")
                flare_html = self.solve_with_flaresolverr(url, headers)
                if flare_html:
                    return {"html": flare_html, "status": "ok", "code": 200}
                return {"error": True, "status": "cloudflare", "message": "FlareSolverr no resolvió el challenge"}
            time.sleep(random.uniform(self.delay_min, self.delay_max))
            return {"html": r.text, "status": "ok", "code": r.status_code}

        except Exception as e:
            logger.error(f"[RequestError] {url} -> {e}")
            return {"error": True, "status": "error", "message": str(e)}

    def solve_with_flaresolverr(self, url, headers):
        try:
            payload = {"cmd": "request.get", "url": url, "maxTimeout": 60000, "headers": headers}
            r = requests.post(self.flaresolverr_url, json=payload, timeout=70)
            r.raise_for_status()
            data = r.json()
            if data.get("status") == "ok":
                return data.get("solution", {}).get("response")
        except Exception as e:
            logger.error(f"❌ FlareSolverr falló en {url}: {e}")
        return None

    # ==========================
    # 🧭 Job Lifecycle
    # ==========================
    def create_job(self):
        try:
            job = ScraperJob(
                website_id=self.website_id,
                category=self.category,
                url=self.start_url,
                status="running",
                started_at=func.now(),
            )
            self.db.add(job)
            self.db.commit()
            self.db.refresh(job)
            self.job_id = job.id
            logger.info(f"🧵 Job creado con ID {self.job_id}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error creando job: {e}")

    def update_job_status(self, status, error=None):
        try:
            job = self.db.query(ScraperJob).filter_by(id=self.job_id).first()
            if not job:
                return
            job.status = status
            if error:
                job.error = str(error)[:500]
            if status in ["finished", "error", "timeout"]:
                job.finished_at = func.now()
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"⚠️ No se pudo actualizar estado del job {self.job_id}: {e}")

    def heartbeat(self):
        try:
            job = self.db.query(ScraperJob).filter_by(id=self.job_id).first()
            if job:
                job.last_heartbeat = func.now()
                self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.warning(f"⚠️ Error al registrar heartbeat: {e}")

    def start_heartbeat(self, interval=60):
        def beat():
            while True:
                if not self.job_id:
                    break
                try:
                    self.heartbeat()
                    logger.info(f"💓 Heartbeat registrado para job_id={self.job_id}")
                except Exception as e:
                    logger.warning(f"⚠️ Error en heartbeat thread: {e}")
                time.sleep(interval)
        threading.Thread(target=beat, daemon=True).start()

    # ==========================
    # 💾 Save pages (ORM) — corregido
    # ==========================
    def save_page(self, url, status, code, content_hash, html):
        try:
            model = ProgramPageRaw if self.category == 1 else JobPageRaw
            clean_html_content = clean_html(html)

            # Buscar si ya existe
            existing = self.db.query(model).filter_by(url=url).first()
            if existing:
                existing.status = status
                existing.http_code = code
                existing.content_hash = content_hash
                existing.html = clean_html_content
                existing.fetched_at = func.now()
            else:
                new_page = model(
                    website_id=self.website_id,
                    url=url,
                    status=status,
                    http_code=code,
                    content_hash=content_hash,
                    html=clean_html_content,
                    fetched_at=func.now()
                )
                self.db.add(new_page)

            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"💥 Error guardando página {url}: {e}")

    def get_page_hash(self, url):
        model = ProgramPageRaw if self.category == 1 else JobPageRaw
        page = self.db.query(model).filter_by(url=url).first()
        return page.content_hash if page else None

    def hash_content(self, html):
        return hashlib.md5(html.encode('utf-8')).hexdigest()

    def get_links(self, html, current_url):
        soup = BeautifulSoup(html, 'html.parser')
        return {self.is_valid_link(a['href'], current_url) for a in soup.find_all('a', href=True) if self.is_valid_link(a['href'], current_url)}

    def is_valid_link(self, href, base_url):
        if not href:
            return None
        href = href.strip()
        if href.startswith(("javascript:", "mailto:", "#")):
            return None
        full_url = urljoin(base_url, href).split('#')[0]
        parsed = urlparse(full_url)
        if parsed.scheme not in ["http", "https"]:
            return None
        if any(full_url.lower().endswith(ext) for ext in [".jpg",".png",".pdf",".mp4",".zip",".doc",".docx"]):
            return None
        ext = tldextract.extract(full_url)
        domain = f"{ext.domain}.{ext.suffix}"
        if domain != self.base_domain:
            return None
        return full_url

    # ==========================
    # 🚀 Run
    # ==========================
    def run(self):
        if not self.job_id:
            self.create_job()

        self.start_heartbeat()

        try:
            self.scrape(self.start_url)
            self.update_job_status("finished")
            logger.info(f"✅ Job {self.job_id} finalizado correctamente ({len(self.visited)} páginas)")
        except Exception as e:
            self.update_job_status("error", str(e))
            logger.error(f"💥 Job {self.job_id} falló: {e}")
        finally:
            # 🔒 Asegurar que no hay operaciones pendientes antes de cerrar
            try:
                if self.db.in_transaction():
                    self.db.rollback()
            except Exception as e:
                logger.warning(f"⚠️ Error al hacer rollback final: {e}")
            finally:
                try:
                    self.db.close()
                except Exception as e:
                    logger.warning(f"⚠️ Error al cerrar sesión DB: {e}")
            return self.tree

    def scrape(self, url, depth=0, parent=None):
        raise NotImplementedError