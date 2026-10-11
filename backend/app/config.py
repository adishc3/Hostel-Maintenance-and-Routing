from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongodb_uri: str = Field(default="", validation_alias="MONGODB_URI")
    mongodb_database: str = Field(default="smart_hostel", validation_alias="MONGODB_DATABASE")
    backend_cors_origins: str = Field(default="http://localhost:5173", validation_alias="BACKEND_CORS_ORIGINS")
    app_name: str = "Smart Hostel Backend"
    app_environment: str = Field(default="development", validation_alias="APP_ENVIRONMENT")

    model_config = SettingsConfigDict(
        env_file=(
            ".env",
            Path(__file__).resolve().parents[2] / ".env",
            Path(__file__).resolve().parents[2] / "atlas-credentials.env",
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
