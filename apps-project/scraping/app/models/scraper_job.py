from sqlalchemy import Column, Integer, Text, String, TIMESTAMP
from sqlalchemy.sql import func
from db import Base

class ScraperJob(Base):
    __tablename__ = "scraper_jobs"

    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, nullable=True)
    category = Column(Integer, nullable=True)  # 1 = academic, 2 = jobs
    max_depth = Column(Integer, nullable=True)
    url = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="pending")  # pending|running|finished|error|timeout
    started_at = Column(TIMESTAMP, nullable=True)
    finished_at = Column(TIMESTAMP, nullable=True)
    last_heartbeat = Column(TIMESTAMP, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())