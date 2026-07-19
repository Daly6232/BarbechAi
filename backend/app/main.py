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
from app.services.audit import prune_old_audit_logs

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting BarbechAI backend...")
    init_db()
    prune_old_audit_logs()
    manager.bind_loop(asyncio.get_running_loop())
    yield
    logger.info("Stopping BarbechAI backend...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="BarbechAi CRM — by ZAYER Digital. Interactive docs at /docs, "
                 "versioned endpoints under /api/v1, legacy unprefixed paths "
                 "kept alive for existing clients.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=False,  # auth uses Bearer tokens, not cookies — no credentials needed
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mounted twice on purpose: unprefixed paths stay alive for the
# already-built/distributed mobile APK and any cached frontend bundle, while
# /api/v1/... is the versioned path new clients should use going forward.
# This is how you introduce versioning without a hard breaking cutover.
for router in (discover_router, crm_router, agent_router, ws_router, auth_router):
    app.include_router(router)
    app.include_router(router, prefix="/api/v1")


@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    return {
        "status": "ok",
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }
