from datetime import date, datetime
from functools import lru_cache
from zoneinfo import ZoneInfo

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://app:app@localhost:5434/payments"
    secret_key: str = "dev-secret-change-me"  # noqa: S105 - local default, production sets SECRET_KEY
    app_timezone: str = "Asia/Tashkent"

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.app_timezone)

    def now(self) -> datetime:
        return datetime.now(self.tz)

    def today(self) -> date:
        return self.now().date()


@lru_cache
def get_settings() -> Settings:
    return Settings()
