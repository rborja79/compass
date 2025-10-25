from sqlalchemy import Column, String, Text, Integer, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from db import Base

import uuid

class JobPageRaw(Base):
    __tablename__ = "job_pages_raw"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    website_id = Column(Integer, ForeignKey("websites.id", ondelete="CASCADE"))
    website = relationship("Website", backref="job_pages")
    url = Column(String(2048), unique=True)
    status = Column(Text, nullable=True)
    http_code = Column(Integer, nullable=True)
    content_hash = Column(Text, nullable=True)
    html = Column(Text, nullable=True)
    fetched_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(
        TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now()
    )