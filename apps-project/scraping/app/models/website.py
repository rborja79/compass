from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, JSON, func
from db import Base

class Website(Base):
    __tablename__ = "websites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    institution = Column(String(200), nullable=True)
    domain = Column(String(255), nullable=False)
    url = Column(String(1024), nullable=False)
    tree = Column(JSON, nullable=True)
    description = Column(Text, nullable=True)
    category_id = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())