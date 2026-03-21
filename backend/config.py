"""
config.py - Centralized application configuration.
Reads .env manually to handle Windows CRLF line endings.
"""
import os
from pathlib import Path
from functools import lru_cache


def _read_env_file() -> dict:
    """Read .env file manually, stripping Windows CRLF and spaces."""
    env_path = Path(".env")
    if not env_path.exists():
        env_path = Path(__file__).parent.parent / ".env"
    values = {}
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                values[key.strip()] = val.strip().strip('"').strip("'")
    return values


class Settings:
    def __init__(self):
        env = _read_env_file()

        self.app_env = env.get("APP_ENV", "development")
        self.app_host = env.get("APP_HOST", "0.0.0.0")
        self.app_port = int(env.get("APP_PORT", "8000"))
        self.secret_key = env.get("SECRET_KEY", "change_this_secret")
        self.allowed_origins = env.get("ALLOWED_ORIGINS", "http://localhost:8501")

        self.ai_provider = env.get("AI_PROVIDER", "groq").lower()

        self.openrouter_api_key = env.get("OPENROUTER_API_KEY", "")
        self.openrouter_base_url = env.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        self.openrouter_model = env.get("OPENROUTER_MODEL", "google/gemma-3-4b-it:free")

        self.groq_api_key = env.get("GROQ_API_KEY", "")
        self.groq_model = env.get("GROQ_MODEL", "llama3-8b-8192")

        self.gemini_api_key = env.get("GEMINI_API_KEY", "")

        self.upload_dir = env.get("UPLOAD_DIR", "data/uploads")
        self.max_file_size_mb = int(env.get("MAX_FILE_SIZE_MB", "10"))
        self.allowed_extensions = env.get("ALLOWED_EXTENSIONS", "pdf,docx")

        self.database_url = env.get("DATABASE_URL", "sqlite+aiosqlite:///./resume_analyzer.db")
        self.shortlist_score_threshold = int(env.get("SHORTLIST_SCORE_THRESHOLD", "7"))

        self.enable_auth = env.get("ENABLE_AUTH", "false").lower() == "true"
        self.auth_username = env.get("AUTH_USERNAME", "admin")
        self.auth_password = env.get("AUTH_PASSWORD", "changeme")

        self.log_level = env.get("LOG_LEVEL", "INFO")
        self.log_file = env.get("LOG_FILE", "logs/app.log")

    @property
    def allowed_origins_list(self):
        return [o.strip() for o in self.allowed_origins.split(",")]

    @property
    def allowed_extensions_list(self):
        return [e.strip().lower() for e in self.allowed_extensions.split(",")]

    @property
    def max_file_size_bytes(self):
        return self.max_file_size_mb * 1024 * 1024


@lru_cache()
def get_settings() -> Settings:
    return Settings()