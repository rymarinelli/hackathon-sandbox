"""
FastAPI entrypoint for the AI Gateway service.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Dict, Optional

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from .providers import (
    HuggingFaceProvider,
    OpenAIProvider,
    Provider,
    ProviderError,
    ProviderRegistry,
    SandboxProvider,
)
from .sandbox_client import SandboxClient
from .safety import SafetyEngine, SafetyReport
from .settings import Settings, get_settings

logger = logging.getLogger(__name__)


class GenerateRequest(BaseModel):
    provider: str = Field(..., description="Provider name: huggingface, openai, sandbox")
    prompt: str = Field(..., description="Prompt to send to the provider")
    model: Optional[str] = Field(None, description="Optional model identifier")
    max_tokens: Optional[int] = Field(256, description="Maximum tokens to request")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")


class GenerateResponse(BaseModel):
    provider: str
    model: Optional[str]
    content: str
    safety: SafetyReport


def configure_logging(log_level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )


def build_registry(settings: Settings) -> ProviderRegistry:
    registry = ProviderRegistry()
    registry.register(OpenAIProvider(api_key=settings.openai_api_key))
    registry.register(HuggingFaceProvider(api_key=settings.huggingface_api_key))
    sandbox_client = SandboxClient(base_url=settings.sandbox_api_url, api_key=settings.sandbox_api_key)
    registry.register(SandboxProvider(client=sandbox_client))
    return registry


@lru_cache()
def get_registry(settings: Settings = Depends(get_settings)) -> ProviderRegistry:
    return build_registry(settings)


@lru_cache()
def get_safety_engine(settings: Settings = Depends(get_settings)) -> SafetyEngine:
    return SafetyEngine(policy_path=settings.policy_config_path)


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    app = FastAPI(title="AI Gateway", version="0.1.0")

    @app.get("/health")
    async def health() -> Dict[str, str]:
        return {"status": "ok", "environment": settings.environment}

    @app.post("/generate", response_model=GenerateResponse)
    async def generate(
        request: GenerateRequest,
        registry: ProviderRegistry = Depends(get_registry),
        safety_engine: SafetyEngine = Depends(get_safety_engine),
    ) -> GenerateResponse:
        provider = _get_provider_or_404(registry, request.provider)
        try:
            content = await provider.generate(
                prompt=request.prompt,
                model=request.model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
            )
        except ProviderError as exc:
            logger.error("Generation failed", exc_info=exc)
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        safety_report = safety_engine.evaluate(content)
        return GenerateResponse(
            provider=request.provider, model=request.model, content=content, safety=safety_report
        )

    return app


def _get_provider_or_404(registry: ProviderRegistry, name: str) -> Provider:
    try:
        return registry.get(name)
    except ProviderError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


app = create_app()

__all__ = ["app", "create_app", "GenerateRequest", "GenerateResponse"]
