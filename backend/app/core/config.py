import os


class Settings:
    # Application
    APP_NAME = "BarbechAI"
    APP_VERSION = "1.0.0"
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

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

    # WebSocket
    DEFAULT_SESSION = "default"

    # User-Agent
    USER_AGENT = "BarbechAI/1.0"


settings = Settings()
