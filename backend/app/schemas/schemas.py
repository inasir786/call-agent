from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CallOut(BaseModel):
    id: int
    vapi_call_id: Optional[str] = None
    status: str
    ended_reason: Optional[str] = None
    duration_seconds: Optional[float] = None
    recording_url: Optional[str] = None
    transcript: Optional[str] = None
    extracted_data: Optional[Any] = None
    started_at: datetime
    ended_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LeadOut(BaseModel):
    id: int
    phone: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    program_of_interest: Optional[str] = None
    wants_callback: bool
    status: str
    retry_count: int
    crm_synced: bool
    updated_at: datetime

    class Config:
        from_attributes = True


class LeadDetailOut(LeadOut):
    calls: List[CallOut] = []


class LeadListOut(BaseModel):
    total: int
    items: List[LeadOut]


class ImportResult(BaseModel):
    imported: int
    duplicates_skipped: int
    invalid_numbers: int


class ResetResult(BaseModel):
    reset_count: int


class CampaignOut(BaseModel):
    is_running: bool
    calling_start_hour: int
    calling_end_hour: int
    max_concurrent_calls: int
    max_retries: int
    scheduled_start_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CampaignUpdate(BaseModel):
    calling_start_hour: Optional[int] = None
    calling_end_hour: Optional[int] = None
    max_concurrent_calls: Optional[int] = None
    max_retries: Optional[int] = None


class CampaignSchedule(BaseModel):
    scheduled_start_at: datetime


class CrmStatusOut(BaseModel):
    configured: bool
    synced: int
    pending: int


class CrmSyncResult(BaseModel):
    synced: int


class ProgramCount(BaseModel):
    program: str
    count: int


class StatsOut(BaseModel):
    total: int
    pending: int
    calling: int
    no_answer: int
    qualified: int
    not_interested: int
    invalid: int
    failed: int
    total_calls_made: int
    is_running: bool
    by_program: List[ProgramCount] = []
