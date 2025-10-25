from sqlalchemy import Column, String, Text, TIMESTAMP, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from db import Base
import uuid

class JobRecord(Base):
    __tablename__ = "job_records_structured"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    page_id = Column(UUID(as_uuid=True), ForeignKey("job_pages_raw.id", ondelete="CASCADE"), unique=True)
    domain = Column(String(255), nullable=True)
    job_title = Column(Text, nullable=True)
    company = Column(Text, nullable=True)
    location = Column(Text, nullable=True)
    salary = Column(Text, nullable=True)
    posted_at = Column(TIMESTAMP, nullable=True)
    tags = Column(JSON, nullable=True)
    description = Column(Text, nullable=True)
    extracted_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # 📌 Campos adicionales para enriquecer con NLP
    profession = Column(String(255), nullable=True)
    skills_hard = Column(JSON, nullable=True)      # habilidades técnicas
    skills_soft = Column(JSON, nullable=True)      # habilidades blandas
    experience_level = Column(String(128), nullable=True)
    years_experience = Column(String(64), nullable=True)
    salary_min = Column(String(64), nullable=True)
    salary_max = Column(String(64), nullable=True)
    salary_currency = Column(String(32), nullable=True)
    salary_period = Column(String(32), nullable=True)