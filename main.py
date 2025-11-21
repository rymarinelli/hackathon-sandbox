"""Entrypoint for the sandbox FastAPI service."""
from __future__ import annotations

import json
from urllib.error import URLError

from fastapi import FastAPI, HTTPException

from provider_dispatcher import ProviderDispatcher
from safety_pipeline import SafetyPipeline
from sandbox_client import forward_chat_to_sandbox
from schemas import (
    BenchmarkRequest,
    BenchmarkResult,
    ChatRequest,
    ChatResponse,
    Message,
)


app = FastAPI(title="Hackathon Sandbox API")
safety_pipeline = SafetyPipeline()
provider_dispatcher = ProviderDispatcher()


@app.post("/v1/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    reviewed_messages = safety_pipeline.review_messages(request.messages)
    try:
        dispatched_response = provider_dispatcher.dispatch_chat(
            request.model, reviewed_messages
        )
    except ValueError as exc:  # pragma: no cover - surfaced via FastAPI
        raise HTTPException(status_code=400, detail=str(exc))
    return ChatResponse(
        model=request.model, messages=reviewed_messages, response=dispatched_response
    )


@app.post("/v1/sandbox/chat", response_model=ChatResponse)
def sandbox_chat(request: ChatRequest) -> ChatResponse:
    try:
        forwarded = forward_chat_to_sandbox(request)
    except URLError as exc:  # pragma: no cover - passthrough to HTTP error
        raise HTTPException(status_code=502, detail=str(exc))

    # align response payload with ChatResponse contract
    return ChatResponse(
        model=forwarded.get("model", request.model),
        messages=[Message(**msg) for msg in forwarded.get("messages", [])]
        if forwarded.get("messages")
        else request.messages,
        response=forwarded.get("response", json.dumps(forwarded)),
    )


@app.get("/v1/models")
def list_models() -> dict:
    return {"models": provider_dispatcher.list_models()}


@app.get("/v1/datasets")
def list_datasets() -> dict:
    return {"datasets": provider_dispatcher.list_datasets()}


@app.post("/v1/benchmark", response_model=BenchmarkResult)
def benchmark(request: BenchmarkRequest) -> BenchmarkResult:
    try:
        metrics = provider_dispatcher.run_benchmark(request.model, request.dataset)
    except ValueError as exc:  # pragma: no cover - surfaced via FastAPI
        raise HTTPException(status_code=400, detail=str(exc))
    return BenchmarkResult(model=request.model, dataset=request.dataset, metrics=metrics)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
