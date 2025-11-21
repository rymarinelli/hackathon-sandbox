"""
Client for interacting with the sandbox runtime service.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class SandboxClient:
    """Thin wrapper around the sandbox HTTP API."""

    def __init__(self, base_url: str, api_key: Optional[str] = None, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    @property
    def _headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def generate(self, prompt: str, model: Optional[str] = None, **kwargs: Any) -> str:
        payload: Dict[str, Any] = {"prompt": prompt}
        if model:
            payload["model"] = model
        payload.update({k: v for k, v in kwargs.items() if v is not None})

        url = f"{self.base_url}/generate"
        logger.debug("Sending request to sandbox service", extra={"url": url})
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=self._headers, json=payload)
                response.raise_for_status()
                data = response.json()
        except Exception as exc:  # noqa: BLE001
            logger.exception("Sandbox service request failed")
            raise

        return data.get("content", "") if isinstance(data, dict) else ""


__all__ = ["SandboxClient"]
