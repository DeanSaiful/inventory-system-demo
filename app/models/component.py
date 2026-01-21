from sqlalchemy import Column, Integer, String, DateTime
from app.core.database import Base
from datetime import datetime


class Component(Base):
    __tablename__ = "components"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, nullable=False)
    description = Column(String, nullable=False)
    value = Column(String)
    size = Column(String)
    voltage = Column(String)
    watt = Column(String)
    type = Column(String)
    part_no = Column(String, unique=True)
    rack = Column(String)
    location = Column(String)
    quantity = Column(Integer, default=0)
    image_path = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)

