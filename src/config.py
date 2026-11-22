"""Настройки приложения (переопределяются переменными окружения, см. .env.example)."""

import os
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent


class Settings:
    app_name: str = "EcoSavior API"
    version: str = "1.0.0"

    jwt_secret: str = os.getenv("JWT_SECRET", "dev-secret-change-me-in-production")
    access_token_ttl_minutes: int = int(os.getenv("ACCESS_TOKEN_TTL_MINUTES", "15"))
    refresh_token_ttl_days: int = int(os.getenv("REFRESH_TOKEN_TTL_DAYS", "30"))

    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{PROJECT_ROOT / 'data' / 'ecosavior.db'}")
    static_dir: Path = SRC_DIR / "static"

    rate_limit_enabled: bool = os.getenv("RATE_LIMIT_ENABLED", "1") == "1"
    auth_rate_limit: str = os.getenv("AUTH_RATE_LIMIT", "30/minute")

    cors_origins: list[str] = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]


settings = Settings()
