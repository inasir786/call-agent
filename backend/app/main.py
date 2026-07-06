import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.database import Base, engine
from app.api import auth, leads, campaign, webhooks, export, crm
from app.workers.dialer_worker import dialer_loop
import app.models


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
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


@app.get("/api/health")
def health():
    return {"status": "ok"}
