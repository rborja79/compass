import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.website import Website
from app.models.website_config import WebsiteConfig
from app.models.category import Category

def seed_from_csv(session: Session, base_path: str = "/mnt/data"):
    """
    Seed automático desde los CSV cargados
    """
    print(f"✅ Seed base_path: {base_path}")
    # === 1. CATEGORIES ===
    categories_file = f"{base_path}/categories.csv"
    try:
        df_categories = pd.read_csv(categories_file)
        for _, row in df_categories.iterrows():
            exists = session.query(Category).filter_by(id=row["id"]).first()
            if not exists:
                category = Category(
                    id=int(row["id"]),
                    name=row["name"],
                    description=row.get("description", None)
                )
                session.add(category)
        session.commit()
        print(f"✅ Seed categories: {len(df_categories)} filas procesadas")
    except FileNotFoundError:
        print("⚠️ categories.csv no encontrado. Se omite este paso.")

    # === 2. WEBSITES ===
    websites_file = f"{base_path}/websites.csv"
    try:
        df_websites = pd.read_csv(websites_file)
        for _, row in df_websites.iterrows():
            exists = session.query(Website).filter_by(domain=row["domain"]).first()
            if not exists:
                website = Website(
                    id=int(row["id"]),
                    domain=row["domain"],
                    url=row["url"],
                    description=row.get("description", None),
                    category_id=row.get("category_id"),
                    institution=row.get("institution", None)
                )
                session.add(website)
        session.commit()
        print(f"✅ Seed websites: {len(df_websites)} filas procesadas")
    except FileNotFoundError:
        print("⚠️ websites.csv no encontrado. Se omite este paso.")
    except IntegrityError as e:
        session.rollback()
        print(f"❌ Error insertando websites: {e}")

    # === 3. WEBSITE CONFIG ===
    config_file = f"{base_path}/website_config.csv"
    try:
        df_config = pd.read_csv(config_file)
        for _, row in df_config.iterrows():
            exists = session.query(WebsiteConfig).filter_by(website_id=row["website_id"]).first()
            if not exists:
                config = WebsiteConfig(
                    website_id=int(row["website_id"]),
                    total_results_selector=row.get("total_results_selector"),
                    pagination_pattern=row.get("pagination_pattern"),
                    link_selector=row.get("link_selector"),
                    link_job=row.get("link_job"),
                    link_pattern=row.get("link_pattern"),
                    job_data_selector=row.get("job_data_selector"),
                    job_detail_selector=row.get("job_detail_selector"),
                    jobs_per_page=row.get("jobs_per_page")
                )
                session.add(config)
        session.commit()
        print(f"✅ Seed website_config: {len(df_config)} filas procesadas")
    except FileNotFoundError:
        print("⚠️ website_config.csv no encontrado. Se omite este paso.")
    except IntegrityError as e:
        session.rollback()
        print(f"❌ Error insertando website_config: {e}")