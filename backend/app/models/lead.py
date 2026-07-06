import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean, JSON
from sqlalchemy.orm import relationship
from app.config.database import Base


class LeadStatus(str, enum.Enum):
    pending = "pending"
    calling = "calling"
    no_answer = "no_answer"
    qualified = "qualified"
    not_interested = "not_interested"
    invalid = "invalid"
    failed = "failed"
    needs_review = "needs_review"


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    program_of_interest = Column(String, nullable=True)
    wants_callback = Column(Boolean, default=False)
    status = Column(Enum(LeadStatus), default=LeadStatus.pending, index=True)
    retry_count = Column(Integer, default=0)
    next_retry_at = Column(DateTime, nullable=True)
    crm_id = Column(String, nullable=True)
    crm_synced = Column(Boolean, default=False)
    review_reason = Column(String, nullable=True)
    field_confidence = Column(JSON, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    calls = relationship("Call", back_populates="lead", cascade="all, delete-orphan")
