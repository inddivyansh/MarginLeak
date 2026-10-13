from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    app_name: str = "MarginLeak"
    environment: str = "development"
    database_url: str = "sqlite:///./marginleak.db"
    tinker_api_key: Optional[str] = None
    tinker_model_path: Optional[str] = None
    backboard_api_key: Optional[str] = None
    tabpfn_enabled: bool = False
    default_currency: str = "USD"
    price_tolerance_percent: float = 2.0
    historical_alert_percent: float = 5.0
    upload_dir: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")

    # Render PostgreSQL uses postgres:// which needs to be postgresql:// for SQLAlchemy
    @property
    def normalized_database_url(self) -> str:
        url = self.database_url
        if url and url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url

settings = Settings()
os.makedirs(settings.upload_dir, exist_ok=True)
