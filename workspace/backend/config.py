import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'dev.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")
    NEWS_API_PROVIDER = os.environ.get("NEWS_API_PROVIDER", "marketaux")

    # AI Suggestions (Phase 17). Groq's free tier; the app degrades to a
    # "not configured" panel rather than erroring when this is unset.
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
    GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

    PRICE_SYNC_INTERVAL_MIN = int(os.environ.get("PRICE_SYNC_INTERVAL_MIN", "30"))

    API_TITLE = "Portfolio Manager API"
    API_VERSION = "v1"
    OPENAPI_VERSION = "3.0.3"
    OPENAPI_URL_PREFIX = "/"
    OPENAPI_SWAGGER_UI_PATH = "/docs"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
