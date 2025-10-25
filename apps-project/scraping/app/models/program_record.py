from sqlalchemy import Column, String, Text, TIMESTAMP, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from db import Base
import uuid

class ProgramRecord(Base):
    __tablename__ = "program_records_structured"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    page_id = Column(UUID(as_uuid=True), ForeignKey("program_pages_raw.id", ondelete="CASCADE"))
    program_name = Column(String(512), nullable=True)
    level = Column(String(64), nullable=True)         # pregrado|maestría|etc
    modality = Column(String(64), nullable=True)      # presencial|virtual|mixta
    duration = Column(String(128), nullable=True)     # texto original
    price = Column(String(128), nullable=True)
    subjects = Column(JSON, nullable=True)            # materias si se extraen
    description = Column(Text, nullable=True)
    extracted_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # 📌 Campos adicionales para NLP
    tags = Column(JSON, nullable=True)               # etiquetas inferidas
    skills_target = Column(JSON, nullable=True)      # skills objetivo
    profession_target = Column(String(255), nullable=True)  # profesión que forma el programa