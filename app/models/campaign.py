from datetime import datetime
from sqlalchemy import Column, Integer, Boolean, DateTime
from app.config.database import Base


class Campaign(Base):
    __tablename__ = "campaign"

    id = Column(Integer, primary_key=True)
    is_running = Column(Boolean, default=False)
    calling_start_hour = Column(Integer, default=10)
    calling_end_hour = Column(Integer, default=19)
    max_concurrent_calls = Column(Integer, default=5)
    max_retries = Column(Integer, default=3)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
