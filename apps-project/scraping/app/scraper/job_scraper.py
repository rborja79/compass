import time
import logging
import math
import re
from bs4 import BeautifulSoup
from sqlalchemy import text
from app.scraper.base_scraper import BaseScraper

logger = logging.getLogger("ScraperLogger")

class JobScraper(BaseScraper):
    def __init__(self, start_url, max_depth=2, delay=(1, 3), proxies=None):
        super().__init__(start_url, max_depth=max_depth, delay=delay, proxies=proxies, category=2)

    def scrape(self, url, depth=0, parent=None):
        logger.info(f"🎯 JobScraper iniciado: {url} | Profundidad: {depth} | Padre: {parent}")

        # ===============================
        # 📦 1. Obtener configuración desde BD
        # ===============================
        config_query = text("""
            SELECT pagination_pattern, jobs_per_page, total_results_selector, link_selector
            FROM website_config
            WHERE website_id = :website_id
        """)
        config = self.db.execute(config_query, {"website_id": self.website_id}).fetchone()

        if not config:
            logger.error(f"❌ No se encontró configuración para website_id={self.website_id}")
            return

        pagination_pattern = config[0]
        jobs_per_page = config[1] or 50
        total_selector = config[2]
        link_selector = config[3]

        # ===============================
        # 🌐 2. Obtener página inicial
        # ===============================
        html = self._get_page_with_flaresolverr(url, parent)
        if not html:
            logger.error(f"❌ No se pudo obtener la página inicial {url}")
            return

        self._save_and_hash_page(url, html, parent, depth)

        # ===============================
        # 🧮 3. Extraer número total de resultados
        # ===============================
        soup = BeautifulSoup(html, "html.parser")
        total_element = soup.select_one(total_selector) if total_selector else None

        total_results = 0
        if total_element:
            text_content = total_element.get_text()
            match = re.search(r"de\s+(\d+)", text_content)
            if match:
                total_results = int(match.group(1))
        else:
            logger.warning(f"⚠️ No se encontró el selector {total_selector}, usando 1 página")
            total_results = jobs_per_page

        total_pages = max(1, math.ceil(total_results / jobs_per_page))
        logger.info(f"📊 Total de resultados: {total_results} — Páginas estimadas: {total_pages}")

        # ===============================
        # 🔁 4. Iterar sobre cada página de paginación
        # ===============================
        for page in range(1, total_pages + 1):
            page_url = pagination_pattern.replace("{page}", str(page))
            logger.info(f"➡️ Página {page}/{total_pages}: {page_url}")

            page_html = self._get_page_with_flaresolverr(page_url, parent=url)
            if not page_html:
                logger.warning(f"⚠️ No se pudo obtener la página {page_url}")
                continue

            self._save_and_hash_page(page_url, page_html, url, depth+1)

            # ===============================
            # 🧭 5. Extraer links de ofertas
            # ===============================
            page_soup = BeautifulSoup(page_html, "html.parser")
            offer_links = [a.get("href") for a in page_soup.select(link_selector) if a.get("href")]

            logger.info(f"📝 {len(offer_links)} ofertas encontradas en página {page}")

            for offer_link in offer_links:
                if not offer_link.startswith("http"):
                    offer_link = f"https://{self.base_domain}{offer_link}"
                self._scrape_offer(offer_link, page_url, depth+2)

    # ===============================
    # 🧰 Métodos auxiliares
    # ===============================
    def _get_page_with_flaresolverr(self, url, parent=None):
        try:
            flare_html = self.solve_with_flaresolverr(url, {
                "User-Agent": self.ua.random,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "Upgrade-Insecure-Requests": "1",
                "Referer": parent or "https://www.google.com/"
            })
            return flare_html
        except Exception as e:
            logger.error(f"❌ FlareSolverr falló para {url}: {e}")
            self.save_page(url, status="error", code=0, content_hash=None, html=f"ERROR: {e}")
            return None

    def _save_and_hash_page(self, url, html, parent, depth):
        new_hash = self.hash_content(html)
        old_hash = self.get_page_hash(url)
        if old_hash == new_hash:
            logger.info(f"⏭️ {url} no ha cambiado desde la última vez")
            return
        self.save_page(url, status="scraped", code=200, content_hash=new_hash, html=html)
        self.tree.append({
            "url": url,
            "parent": parent,
            "depth": depth,
            "hash": new_hash,
            "timestamp": time.time()
        })
        logger.info(f"✅ Página guardada: {url}")

    def _scrape_offer(self, offer_url, parent, depth):
        html = self._get_page_with_flaresolverr(offer_url, parent)
        if html:
            self._save_and_hash_page(offer_url, html, parent, depth)