import os
from typing import Optional
from pydantic import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration settings"""
    
    # Server settings
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False
    reload: bool = False
    
    # Security settings
    secret_key: str = "your-secret-key-here"  # Change in production
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Database settings
    database_path: str = "./_database"
    
    # Trading settings
    enable_live_trading: bool = False
    enable_paper_trading: bool = True
    max_concurrent_orders: int = 100
    
    # WebSocket settings
    websocket_heartbeat_interval: int = 30
    max_websocket_connections: int = 1000
    
    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # External API settings
    kiwoom_enabled: bool = False
    upbit_enabled: bool = False
    binance_enabled: bool = False
    
    # Rate limiting
    rate_limit_requests: int = 1000
    rate_limit_window: int = 3600  # 1 hour
    
    # File paths
    static_files_path: str = "web_app/static"
    templates_path: str = "web_app/templates"
    
    # Process management
    max_background_processes: int = 10
    process_restart_delay: int = 5
    
    # Data retention
    max_log_days: int = 30
    max_chart_data_days: int = 90
    
    class Config:
        env_file = ".env"
        env_prefix = "STOM_"


@lru_cache()
def get_settings() -> Settings:
    """Get application settings (cached)"""
    return Settings()


# Environment-specific configurations
class DevelopmentSettings(Settings):
    debug: bool = True
    reload: bool = True
    log_level: str = "DEBUG"


class ProductionSettings(Settings):
    debug: bool = False
    reload: bool = False
    log_level: str = "WARNING"
    enable_live_trading: bool = True
    enable_paper_trading: bool = False


class TestingSettings(Settings):
    debug: bool = True
    database_path: str = "./_database_test"
    enable_live_trading: bool = False
    enable_paper_trading: bool = True


def get_environment_settings() -> Settings:
    """Get settings based on environment"""
    env = os.getenv("STOM_ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()