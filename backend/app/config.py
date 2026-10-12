"""Application settings, loaded from environment / .env via pydantic-settings."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "{{APP_NAME}} TMS"
    environment: str = "development"

    # Database — SQLite for local dev, Postgres-ready via DATABASE_URL.
    database_url: str = "sqlite:///./tms.db"

    # Auth / JWT. Override JWT_SECRET in every non-dev environment.
    jwt_secret: str = "dev-insecure-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 12  # 12 hours

    # CORS — comma-separated list of allowed origins.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Telematics — per-provider shared secrets as "provider:secret,provider:secret".
    telematics_secrets: str = "mock:dev-mock-secret,samsara:dev-samsara-secret,geotab:dev-geotab-secret"
    geofence_enabled: bool = True
    telematics_stale_hours: int = 3

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def telematics_secret_map(self) -> dict[str, str]:
        out: dict[str, str] = {}
        for pair in self.telematics_secrets.split(","):
            pair = pair.strip()
            if not pair or ":" not in pair:
                continue
            provider, secret = pair.split(":", 1)
            out[provider.strip().lower()] = secret.strip()
        return out


@lru_cache
def get_settings() -> Settings:
    return Settings()
