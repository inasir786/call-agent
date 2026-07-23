import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.database import Base, engine
from app.api import auth, leads, campaign, webhooks, export, crm, assistant
from app.workers.dialer_worker import dialer_loop
from app.config.settings import settings
from app.services.assistant_prompt import ANALYSIS_SCHEMA, ANALYSIS_INSTRUCTIONS
from app.services.structured_output_service import (
    ensure_structured_output,
    ensure_assistant_structured_output,
)
import app.models

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_structured_output(ANALYSIS_SCHEMA, ANALYSIS_INSTRUCTIONS)
    ensure_assistant_structured_output(settings.vapi_assistant_id)
    task = asyncio.create_task(dialer_loop())
    yield
    task.cancel()


app = FastAPI(title="AI Voice Calling Agent", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(leads.router)
app.include_router(campaign.router)
app.include_router(webhooks.router)
app.include_router(export.router)
app.include_router(crm.router)
app.include_router(assistant.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
