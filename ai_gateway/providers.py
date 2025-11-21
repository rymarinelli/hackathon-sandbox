"""
Provider abstractions for generating content through multiple backends.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class ProviderError(RuntimeError):
    """Raised when a provider encounters an error."""


class Provider(ABC):
    """Abstract base class for text generation providers."""

    name: str

    @abstractmethod
    async def generate(self, prompt: str, model: Optional[str] = None, **kwargs: Any) -> str:
        """Generate text from a prompt."""


class HuggingFaceProvider(Provider):
    """Simple text generation provider for HuggingFace Inference API."""

    def __init__(self, api_key: Optional[str] = None, timeout: float = 30.0):
        self.name = "huggingface"
        self._api_key = api_key
        self._timeout = timeout

    async def generate(self, prompt: str, model: Optional[str] = None, **kwargs: Any) -> str:
        url = "https://api-inference.huggingface.co/models/" + (model or "gpt2")
        headers: Dict[str, str] = {"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}
        payload = {"inputs": prompt}
        logger.debug("Sending request to HuggingFace", extra={"model": model})
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
        except Exception as exc:  # noqa: BLE001
            logger.exception("HuggingFace request failed")
            raise ProviderError("HuggingFace generation failed") from exc

        if isinstance(data, list) and data:
            return data[0].get("generated_text", "")
        return data.get("generated_text", "") if isinstance(data, dict) else ""


class OpenAIProvider(Provider):
    """Text generation provider backed by the OpenAI API."""

    def __init__(self, api_key: Optional[str] = None, timeout: float = 30.0):
        self.name = "openai"
        self._api_key = api_key
        self._timeout = timeout

    async def generate(self, prompt: str, model: Optional[str] = None, **kwargs: Any) -> str:
        # Minimal REST call to OpenAI completion endpoint for portability.
        url = "https://api.openai.com/v1/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": model or "gpt-3.5-turbo-instruct",
            "prompt": prompt,
            "max_tokens": kwargs.get("max_tokens", 256),
            "temperature": kwargs.get("temperature", 0.7),
        }
        logger.debug("Sending request to OpenAI", extra={"model": payload["model"]})
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
        except Exception as exc:  # noqa: BLE001
            logger.exception("OpenAI request failed")
            raise ProviderError("OpenAI generation failed") from exc

        choices = data.get("choices", []) if isinstance(data, dict) else []
        if choices:
            return choices[0].get("text", "").strip()
        return ""


class SandboxProvider(Provider):
    """Provider that routes generation through the sandbox runtime service."""

    def __init__(self, client: "SandboxClient"):
        from .sandbox_client import SandboxClient

        if not isinstance(client, SandboxClient):
            raise TypeError("SandboxProvider expects a SandboxClient instance")
        self.name = "sandbox"
        self._client = client

    async def generate(self, prompt: str, model: Optional[str] = None, **kwargs: Any) -> str:
        return await self._client.generate(prompt=prompt, model=model, **kwargs)


class ProviderRegistry:
    """Registry for available providers."""

    def __init__(self):
        self._providers: Dict[str, Provider] = {}

    def register(self, provider: Provider) -> None:
        logger.debug("Registering provider", extra={"provider": provider.name})
        self._providers[provider.name] = provider

    def get(self, name: str) -> Provider:
        try:
            return self._providers[name]
        except KeyError as exc:
            raise ProviderError(f"Unknown provider '{name}'") from exc

    def list(self) -> Dict[str, Provider]:
        return dict(self._providers)


__all__ = [
    "Provider",
    "ProviderError",
    "HuggingFaceProvider",
    "OpenAIProvider",
    "SandboxProvider",
    "ProviderRegistry",
]
