import time
import logging
from app.scraper.base_scraper import BaseScraper

logger = logging.getLogger("ScraperLogger")


class AcademicScraper(BaseScraper):
    def __init__(self, start_url, max_depth=2, delay=(1, 3), proxies=None):
        super().__init__(start_url, max_depth=max_depth, delay=delay, proxies=proxies, category=1)

    def scrape(self, url, depth=0, parent=None):
        logger.info(f"🎯 AcademicScraper iniciado: {url} | Profundidad: {depth} | Padre: {parent}")

        # 🚫 Evitar URLs repetidas
        if url in self.visited:
            logger.debug(f"🔁 URL ya visitada, se omite: {url}")
            return

        # 📏 Profundidad máxima
        if depth > self.max_depth:
            logger.debug(f"📏 Profundidad máxima alcanzada en: {url}")
            return

        self.visited.add(url)

        # ==========================
        # 🌐 Obtener la página
        # ==========================
        result = self.get_page(url, referer=parent)

        if result.get("error"):
            # ❌ Error al obtener página
            error_msg = f"❌ Error: {result.get('message')} | Status: {result.get('status')}"
            logger.error(f"{error_msg}")

            self.save_page(url, status=result.get("status"), code=0, content_hash=None, html=error_msg)

            self.tree.append({
                "url": url,
                "parent": parent,
                "depth": depth,
                "hash": None,
                "timestamp": time.time(),
                "error": result.get("message")
            })
            return

        html = result.get("html")
        code = result.get("code")

        # ==========================
        # 🧮 Comparar hash
        # ==========================
        new_hash = self.hash_content(html)
        old_hash = self.get_page_hash(url)

        if old_hash == new_hash:
            logger.info(f"⏭️ {url} no ha cambiado desde la última vez")
            return

        # ==========================
        # 💾 Guardar página
        # ==========================
        try:
            self.save_page(url, status="scraped", code=code, content_hash=new_hash, html=html)
            logger.info(f"✅ Página académica guardada: {url}")
        except Exception as e:
            logger.error(f"💥 Error al guardar página {url}: {e}")
            return

        # ==========================
        # 🌳 Registrar nodo en árbol
        # ==========================
        self.tree.append({
            "url": url,
            "parent": parent,
            "depth": depth,
            "hash": new_hash,
            "timestamp": time.time()
        })

        # ==========================
        # 🔁 Recursividad
        # ==========================
        links = self.get_links(html, url)
        logger.info(f"🔗 {len(links)} enlaces encontrados en {url}")

        for link in links:
            self.scrape(link, depth + 1, parent=url)