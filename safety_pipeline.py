"""Minimal safety pipeline placeholder."""
from __future__ import annotations

from typing import Iterable, List

from pydantic import BaseModel


class SafetyPipeline:
    """Executes safety checks on chat messages.

    In a production system this would integrate with an abuse or content
    moderation pipeline. For now it simply ensures messages are present and
    trims whitespace.
    """

    def review_messages(self, messages: Iterable[BaseModel]) -> List[BaseModel]:
        reviewed: List[BaseModel] = []
        for message in messages:
            message.content = message.content.strip()
            reviewed.append(message)
        return reviewed
