import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean, JSON
from sqlalchemy.orm import relationship
from app.config.database import Base


class LeadStatus(str, enum.Enum):
    pending = "pending"
    calling = "calling"
    no_answer = "no_answer"
    reactivated = "reactivated"
    nurture = "nurture"
    closed_lost = "closed_lost"
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
    reschedule_time = Column(String, nullable=True)
    current_status = Column(String, nullable=True)
    timeline = Column(String, nullable=True)
    original_blocker = Column(String, nullable=True)
    last_qualification = Column(String, nullable=True)
    grade_or_cgpa = Column(String, nullable=True)
    meets_baseline = Column(Boolean, nullable=True)
    advisor_callback_time = Column(String, nullable=True)
    route_team = Column(String, nullable=True)
    dnc = Column(Boolean, default=False)
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
