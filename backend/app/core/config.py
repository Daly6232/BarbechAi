import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Application
    APP_NAME = "BarbechAI"
    APP_VERSION = "1.1.0"
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

    # Auto-detect Termux (local phone testing) to disable Rust-based
    # libraries (ddgs) that crash on Android due to missing NDK context.
    IS_TERMUX = "com.termux" in os.getenv("PREFIX", "") or os.path.exists("/data/data/com.termux")

    # Database
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "sqlite:///barbechai.db"
    )

    # Discovery APIs
    FOURSQUARE_API_KEY = os.getenv("FOURSQUARE_API_KEY", "")
    HERE_API_KEY = os.getenv("HERE_API_KEY", "")
    GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY", "")
    TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY", "")
    LOCATIONIQ_API_KEY = os.getenv("LOCATIONIQ_API_KEY", "")
    OPENCAGE_API_KEY = os.getenv("OPENCAGE_API_KEY", "")

    # Networking
    REQUEST_TIMEOUT = 10
    MAX_WORKERS = 4

    # CORS — comma-separated list in env. Defaults to the actual deployed
    # frontend + local dev, replacing the previous wildcard "*" which let
    # any website make authenticated requests against this API.
    ALLOWED_ORIGINS = [
        o.strip() for o in os.getenv(
            "ALLOWED_ORIGINS",
            "https://barbech-ai.vercel.app,http://localhost:5173,http://localhost:3000"
        ).split(",") if o.strip()
    ]

    # WebSocket
    DEFAULT_SESSION = "default"

    # User-Agent
    USER_AGENT = "BarbechAI/1.0"

    # Audit log retention — SOC 2-style expectation is 1+ year. Pruned on
    # each backend startup (best-effort; there's no standalone cron worker
    # in this deployment, so this runs whenever Render restarts the service).
    AUDIT_LOG_RETENTION_DAYS = int(os.getenv("AUDIT_LOG_RETENTION_DAYS", "400"))

    # Data retention policy for lost/dead leads (GDPR-style). This is a
    # documented policy surfaced to admins for manual review — leads are
    # never auto-deleted without a human confirming, since that's real
    # business data. Default: 2 years after a lead is marked LOST.
    LOST_LEAD_RETENTION_DAYS = int(os.getenv("LOST_LEAD_RETENTION_DAYS", "730"))


settings = Settings()
