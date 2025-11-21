from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    app_name: str = Field("gateway", description="Service name exposed on health endpoints.")
    app_host: str = Field("0.0.0.0", description="Hostname for the HTTP server.")
    app_port: int = Field(8000, description="Port for the HTTP server.")
    log_level: str = Field("INFO", description="Python logging level for the service.")

    redis_url: Optional[str] = Field(None, description="Redis connection string, e.g. redis://redis:6379/0")
    ready_requires_redis: bool = Field(
        False,
        description="When true, the readiness probe fails if Redis is unreachable.",
        alias="READY_REDIS_CHECK",
    )
    request_timeout_s: float = Field(5.0, description="Maximum time in seconds for readiness dependency checks.")

    otel_service_name: str = Field("gateway", description="OpenTelemetry service.name resource attribute.")
    otlp_endpoint: Optional[str] = Field(None, description="OTLP gRPC endpoint for exported traces.")
    otlp_insecure: bool = Field(True, description="Whether to disable TLS when exporting OTLP traces.")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()
