import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Smart Waste Management Analytics & Forecasting API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Secret & Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-municipal-waste-analytics-jwt-key-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 24 hours

    # Database Settings
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "waste_dw_db")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "waste_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "waste_password")

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.POSTGRES_DB}"

settings = Settings()
