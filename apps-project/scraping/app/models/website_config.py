from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, func
from db import Base

class WebsiteConfig(Base):
    __tablename__ = "website_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    website_id = Column(Integer, ForeignKey("websites.id", ondelete="CASCADE"))
    total_results_selector = Column(String, nullable=True)
    pagination_pattern = Column(String, nullable=True)
    link_selector = Column(String(500), nullable=True)
    link_job = Column(String(500), nullable=True)
    link_pattern = Column(String(500), nullable=True)
    job_data_selector = Column(String(500), nullable=True)
    job_detail_selector = Column(String(500), nullable=True)
    jobs_per_page = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())