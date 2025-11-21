"""Shared Pydantic schemas for the API."""
from __future__ import annotations

from typing import List

from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str
    messages: List[Message]


class ChatResponse(BaseModel):
    model: str
    messages: List[Message]
    response: str


class BenchmarkRequest(BaseModel):
    model: str
    dataset: str


class BenchmarkResult(BaseModel):
    model: str
    dataset: str
    metrics: dict
