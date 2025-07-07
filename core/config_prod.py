import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "Social Listening System"
    ENVIRONMENT: str = "production"
    DEBUG: bool = False

    # Database settings - for production, use RDS or external database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/social_listening.db")

    # Redis settings
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # AWS Bedrock settings
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")

    # API Keys
    TWITTER_API_KEY: str = os.getenv("TWITTER_API_KEY", "")
    TWITTER_API_SECRET: str = os.getenv("TWITTER_API_SECRET", "")
    TWITTER_ACCESS_TOKEN: str = os.getenv("TWITTER_ACCESS_TOKEN", "")
    TWITTER_ACCESS_TOKEN_SECRET: str = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")

    # Security
    ALLOWED_ORIGINS: List[str] = os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else ["*"]
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8002"))

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
