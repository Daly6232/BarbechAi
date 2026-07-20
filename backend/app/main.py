import asyncio
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.agents import router as agent_router
from app.api.crm import router as crm_router
from app.api.discover import router as discover_router
from app.api.ws import router as ws_router
from app.api.auth import router as auth_router
from app.core.config import settings
from app.core.logging import get_logger, request_id_var
from app.database import init_db
from app.services.websocket_manager import manager
from app.services.audit import prune_old_audit_logs

logger = get_logger(__name__)

# Dormant unless SENTRY_DSN is actually set — no-ops otherwise, and never
# crashes the app if the sentry_sdk package isn't installed for any reason,
# since the last two production incidents this app had were both import-time
# crashes and that's exactly the failure mode to avoid introducing here.
if settings.SENTRY_DSN:
    try:
        import sentry_sdk
        sentry_sdk.init(dsn=settings.SENTRY_DSN, environment=settings.ENVIRONMENT,
                         traces_sample_rate=0.1)
        logger.info("Sentry error tracking enabled")
    except ImportError:
        logger.warning("SENTRY_DSN is set but sentry-sdk isn't installed — skipping")


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


@app.middleware("http")
async def request_id_and_timing_middleware(request: Request, call_next):
    """Tags every request with an ID (reused from X-Request-ID if the
    client already sent one) so its log lines can be correlated, and logs
    method/path/status/duration for every request — the basic 'what is
    this service actually doing' visibility that didn't exist before."""
    req_id = request.headers.get("x-request-id", str(uuid.uuid4())[:8])
    token = request_id_var.set(req_id)
    start = time.monotonic()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((time.monotonic() - start) * 1000, 1)
        logger.exception("Unhandled exception on %s %s (%sms)", request.method, request.url.path, duration_ms)
        raise
    finally:
        request_id_var.reset(token)
    duration_ms = round((time.monotonic() - start) * 1000, 1)
    response.headers["X-Request-ID"] = req_id
    logger.info("%s %s -> %s (%sms)", request.method, request.url.path, response.status_code, duration_ms)
    return response


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
