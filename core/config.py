import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "Social Listening System"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database settings
    DATABASE_URL: str = "sqlite:///./data/social_listening.db"

    # Redis settings
    REDIS_URL: str = "redis://localhost:6379"

    # AWS Bedrock settings
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_SESSION_TOKEN: str = ""

    # API settings
    API_V1_STR: str = "/api/v1"
    ALLOWED_HOSTS: List[str] = ["127.0.0.1", "localhost"]

    # Security settings
    SECRET_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Social Media API settings
    TWITTER_BEARER_TOKEN: str = ""
    TWITTER_API_KEY: str = ""
    TWITTER_API_SECRET: str = ""
    TWITTER_ACCESS_TOKEN: str = ""
    TWITTER_ACCESS_TOKEN_SECRET: str = ""

    # External API settings
    YOUTUBE_API_KEY: str = ""
    REDDIT_CLIENT_ID: str = ""
    REDDIT_CLIENT_SECRET: str = ""

    # Collection settings
    COLLECTION_INTERVAL: int = 3600
    MAX_POSTS_PER_COLLECTION: int = 1000
    RATE_LIMIT_DELAY: float = 1.0
    
    # Rate limiting settings
    TWITTER_RATE_LIMIT_WINDOW: int = 900  # 15 minutes
    TWITTER_MAX_REQUESTS_PER_WINDOW: int = 300
    YOUTUBE_RATE_LIMIT_WINDOW: int = 3600  # 1 hour
    YOUTUBE_MAX_REQUESTS_PER_WINDOW: int = 10000
    REDDIT_RATE_LIMIT_WINDOW: int = 600  # 10 minutes
    REDDIT_MAX_REQUESTS_PER_WINDOW: int = 100
    
    # Retry settings
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.0
    MAX_RETRY_DELAY: float = 30.0

    # AI model settings
    DEFAULT_MODEL: str = "amazon.nova-lite-v1:0"
    EMBEDDING_MODEL: str = "amazon.titan-embed-text-v1"
    SENTIMENT_THRESHOLD: float = 0.7

    # Report settings
    REPORT_GENERATION_TIMEOUT: int = 900
    MAX_REPORT_ITEMS: int = 500

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True
    )


settings = Settings()
