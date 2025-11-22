"""Application configuration."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://pump:pump@postgres:5432/pump_researcher"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # API Keys (from environment)
    anthropic_api_key: str = ""
    telegram_chat_id: str = ""

    # Agent settings
    pump_threshold_pct: float = 5.0
    pump_time_window_minutes: int = 60

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
