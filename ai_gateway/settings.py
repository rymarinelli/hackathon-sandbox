"""
Configuration settings for the AI Gateway service.
"""
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    environment: str = Field("development", description="Deployment environment name")
    log_level: str = Field("INFO", description="Log level for application")

    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    huggingface_api_key: Optional[str] = Field(None, env="HUGGINGFACE_API_KEY")
    sandbox_api_url: str = Field("http://sandbox:8000", env="SANDBOX_API_URL")
    sandbox_api_key: Optional[str] = Field(None, env="SANDBOX_API_KEY")

    models_config_path: Path = Field(Path("config/models.yaml"), env="MODELS_CONFIG_PATH")
    datasets_config_path: Path = Field(Path("config/datasets.yaml"), env="DATASETS_CONFIG_PATH")
    policy_config_path: Path = Field(Path("config/policy.yaml"), env="POLICY_CONFIG_PATH")

    redis_url: Optional[str] = Field(None, env="REDIS_URL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Return a cached instance of :class:`Settings`."""

    return Settings()


__all__ = ["Settings", "get_settings"]
