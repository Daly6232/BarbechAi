import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.agents import router as agent_router
from app.api.crm import router as crm_router
from app.api.discover import router as discover_router
from app.api.ws import router as ws_router
from app.api.auth import router as auth_router
from app.core.config import settings
from app.core.logging import get_logger
from app.database import init_db
from app.services.websocket_manager import manager

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting BarbechAI backend...")
    init_db()
    manager.bind_loop(asyncio.get_running_loop())
    yield
    logger.info("Stopping BarbechAI backend...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # auth uses Bearer tokens, not cookies — no credentials needed
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(discover_router)
app.include_router(crm_router)
app.include_router(agent_router)
app.include_router(ws_router)
app.include_router(auth_router)


@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    return {
        "status": "ok",
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }
