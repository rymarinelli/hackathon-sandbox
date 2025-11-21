"""Mock provider dispatcher for routing model calls."""
from __future__ import annotations

from typing import Iterable, List

from pydantic import BaseModel


class ProviderDispatcher:
    """Dispatches chat calls and enumerates supported assets."""

    def __init__(self) -> None:
        self._models = ["mock-gpt", "mock-llama"]
        self._datasets = ["toxicity", "hallucination"]

    def dispatch_chat(self, model: str, messages: Iterable[BaseModel]) -> str:
        if model not in self._models:
            available = ", ".join(self._models)
            raise ValueError(f"Unknown model '{model}'. Available: {available}")
        compiled = " ".join(message.content for message in messages)
        return f"{model} responded to: {compiled}" if compiled else "No content"

    def list_models(self) -> List[str]:
        return list(self._models)

    def list_datasets(self) -> List[str]:
        return list(self._datasets)

    def run_benchmark(self, model: str, dataset: str) -> dict:
        if model not in self._models:
            raise ValueError(f"Model '{model}' is not supported for benchmarking")
        if dataset not in self._datasets:
            raise ValueError(f"Dataset '{dataset}' is not supported for benchmarking")

        # Placeholder score generation
        return {"model": model, "dataset": dataset, "score": 0.75, "latency_ms": 120}
