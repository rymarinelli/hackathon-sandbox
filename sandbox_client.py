"""Client helpers for forwarding chat traffic to a sandbox deployment."""
from __future__ import annotations

import json
import os
from typing import Any, Dict
from urllib import request

from schemas import ChatRequest


def inspect_k8s_sandbox() -> str:
    """Return the sandbox chat endpoint discovered from environment variables.

    In a real deployment this would query the Kubernetes API for sandbox pods
    and expose load-balanced routing details. Here we rely on environment
    variables to keep the sandbox configurable.
    """

    host = os.getenv("SANDBOX_HOST", "localhost")
    port = os.getenv("SANDBOX_PORT", "8001")
    path = os.getenv("SANDBOX_CHAT_PATH", "/v1/chat")
    return f"http://{host}:{port}{path}"


def forward_chat_to_sandbox(request_payload: ChatRequest) -> Dict[str, Any]:
    endpoint = inspect_k8s_sandbox()
    payload = json.dumps(request_payload.dict()).encode()
    http_request = request.Request(
        endpoint, data=payload, headers={"Content-Type": "application/json"}
    )
    with request.urlopen(http_request) as response:
        return json.loads(response.read().decode())
