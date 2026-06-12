"""Configuration module."""

import os
from typing import Optional


class Config:
    """Base configuration."""

    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    WORKER_THREADS = int(os.getenv("WORKER_THREADS", "4"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    LOG_LEVEL = "DEBUG"


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    LOG_LEVEL = "WARNING"


def get_config(env: Optional[str] = None) -> Config:
    """Get configuration for environment.

    Args:
        env: Environment name (dev, prod, test)

    Returns:
        Configuration object
    """
    if env is None:
        env = os.getenv("ENV", "dev")

    if env == "prod":
        return ProductionConfig()
    return DevelopmentConfig()
