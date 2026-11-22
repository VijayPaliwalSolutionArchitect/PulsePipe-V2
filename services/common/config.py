import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    API_PORT: int = int(os.getenv("API_PORT", "8093"))
    GATEWAY_PORT: int = int(os.getenv("GATEWAY_PORT", "8087"))
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///pulsepipe.db")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "pulsepipe_dev_jwt_secret_32_bytes_min")
    ALGORITHM: str = "HS256"
    SIMULATE: bool = os.getenv("SIMULATE", "true").lower() == "true"
    DEFAULT_TENANT_ID: str = "acme-sales"
    MAX_EMAILS_PER_HOUR_DOMAIN: int = 40
    COMPANY_PHYSICAL_ADDRESS: str = "100 Enterprise Way, Suite 400, San Francisco, CA 94105"

settings = Settings()
