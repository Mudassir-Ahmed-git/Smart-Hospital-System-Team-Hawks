"""Application settings, loaded from environment variables / .env file."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Smart Hospital Bed & Emergency Capacity System"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"

    # PostgreSQL by default. SQLite also works for quick local runs/tests:
    #   DATABASE_URL=sqlite:///./smart_hospital.db
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/smart_hospital"

    # JWT
    SECRET_KEY: str = "change-me-in-production-please-use-a-long-random-string"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 12

    # CORS (the Vite dev server runs on 5173)
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Demo-friendliness. The frontend lets people pick any role on the register page.
    # Set to false in production so only patients can self-register.
    ALLOW_OPEN_ROLE_REGISTRATION: bool = True
    # Hospital staff who register without a hospital are attached to this one
    # (the frontend's staff pages are hard-wired to hospital 1).
    DEFAULT_STAFF_HOSPITAL_ID: int = 1

    # Fallback user location (Karachi) when the client does not send lat/lng.
    DEFAULT_LATITUDE: float = 24.8607
    DEFAULT_LONGITUDE: float = 67.0011
    MAX_SEARCH_RADIUS_KM: float = 50.0

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
