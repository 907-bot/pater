# Configuration and environment variables

import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # ============ API Configuration ============
    api_title: str = "Pater API"
    api_version: str = "0.1.0"
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    debug: bool = Field(default=False, alias="DEBUG")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    
    # ============ Database Configuration ============
    mongodb_url: str = Field(
        default="mongodb://localhost:27017",
        alias="MONGODB_URL"
    )
    mongodb_db_name: str = Field(default="pater", alias="MONGODB_DB_NAME")
    
    neo4j_url: str = Field(
        default="neo4j://localhost:7687",
        alias="NEO4J_URL"
    )
    neo4j_user: str = Field(default="neo4j", alias="NEO4J_USER")
    neo4j_password: str = Field(default="password", alias="NEO4J_PASSWORD")
    
    redis_url: str = Field(
        default="redis://localhost:6379",
        alias="REDIS_URL"
    )
    redis_ttl: int = Field(default=3600, alias="REDIS_TTL")
    
    # ============ ML Models Configuration ============
    models_path: str = Field(default="./ml/models", alias="MODELS_PATH")
    enable_arima: bool = Field(default=True, alias="ENABLE_ARIMA")
    enable_lgbm: bool = Field(default=True, alias="ENABLE_LGBM")
    enable_gnn: bool = Field(default=False, alias="ENABLE_GNN")
    
    # ============ Scraping Configuration ============
    scraper_timeout: int = Field(default=30, alias="SCRAPER_TIMEOUT")
    scraper_retry_count: int = Field(default=3, alias="SCRAPER_RETRY_COUNT")
    scraper_rate_limit: int = Field(default=2, alias="SCRAPER_RATE_LIMIT")
    
    # ============ Feature Flags ============
    enable_predictions: bool = Field(default=True, alias="ENABLE_PREDICTIONS")
    enable_websocket: bool = Field(default=False, alias="ENABLE_WEBSOCKET")
    enable_affiliate: bool = Field(default=False, alias="ENABLE_AFFILIATE")
    
    # ============ Rate Limiting ============
    rate_limit_enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(default=100, alias="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=3600, alias="RATE_LIMIT_WINDOW")
    
    # ============ Security ============
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        alias="SECRET_KEY"
    )
    cors_origins: list = Field(
        default=["*"],
        alias="CORS_ORIGINS"
    )
    allowed_hosts: list = Field(
        default=["*"],
        alias="ALLOWED_HOSTS"
    )
    
    # ============ Logging ============
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")
    
    # ============ Notification ============
    enable_notifications: bool = Field(default=True, alias="ENABLE_NOTIFICATIONS")
    notification_email: str = Field(default="", alias="NOTIFICATION_EMAIL")
    
    # ============ Analytics ============
    analytics_enabled: bool = Field(default=True, alias="ANALYTICS_ENABLED")
    analytics_api_key: str = Field(default="", alias="ANALYTICS_API_KEY")
    
    # ============ Performance ============
    worker_threads: int = Field(default=4, alias="WORKER_THREADS")
    max_connections: int = Field(default=100, alias="MAX_CONNECTIONS")
    connection_timeout: int = Field(default=10, alias="CONNECTION_TIMEOUT")
    
    # ============ File Storage ============
    gcs_bucket: str = Field(default="pater-models", alias="GCS_BUCKET")
    gcs_project_id: str = Field(default="pater-ai", alias="GCS_PROJECT_ID")
    gcs_credentials_path: str = Field(
        default="./credentials.json",
        alias="GCS_CREDENTIALS_PATH"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

# Export commonly used settings
settings = get_settings()

# Environment-specific configurations
def is_production() -> bool:
    """Check if running in production"""
    return settings.environment == "production"

def is_development() -> bool:
    """Check if running in development"""
    return settings.environment == "development"

def is_testing() -> bool:
    """Check if running in testing"""
    return settings.environment == "testing"

# Database URLs
MONGODB_URL = settings.mongodb_url
NEO4J_URL = settings.neo4j_url
REDIS_URL = settings.redis_url

# API Configuration
API_TITLE = settings.api_title
API_VERSION = settings.api_version
DEBUG = settings.debug

# Logging
LOG_LEVEL = settings.log_level
LOG_FORMAT = settings.log_format

# ML Models
MODELS_PATH = settings.models_path
ENABLE_ARIMA = settings.enable_arima
ENABLE_LGBM = settings.enable_lgbm
ENABLE_GNN = settings.enable_gnn

# Feature flags
ENABLE_PREDICTIONS = settings.enable_predictions
ENABLE_WEBSOCKET = settings.enable_websocket
ENABLE_AFFILIATE = settings.enable_affiliate
