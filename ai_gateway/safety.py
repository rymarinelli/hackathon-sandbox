"""
Safety tooling for applying policy checks to generated content.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, List

import yaml
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class SafetyRule(BaseModel):
    """Represents a simple banned keyword rule."""

    description: str
    keywords: List[str]


class SafetyReport(BaseModel):
    """Result of running safety checks."""

    flagged: bool
    triggers: List[str]
    policy_version: str


class SafetyEngine:
    """Evaluates generated content against YAML policy rules."""

    def __init__(self, policy_path: Path):
        self.policy_path = policy_path
        self._rules: List[SafetyRule] = []
        self.policy_version = ""
        self.load_policy()

    def load_policy(self) -> None:
        if not self.policy_path.exists():
            logger.warning("Policy file not found; skipping safety checks", extra={"policy_path": str(self.policy_path)})
            self._rules = []
            self.policy_version = "unavailable"
            return

        with self.policy_path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}

        self.policy_version = str(data.get("version", "unknown"))
        self._rules = [
            SafetyRule(description=rule.get("description", ""), keywords=rule.get("keywords", []))
            for rule in data.get("rules", [])
        ]
        logger.info("Loaded safety policy", extra={"rules": len(self._rules), "version": self.policy_version})

    def evaluate(self, text: str) -> SafetyReport:
        matches: List[str] = []
        lowered = text.lower()
        for rule in self._rules:
            for keyword in rule.keywords:
                if keyword.lower() in lowered:
                    matches.append(rule.description or keyword)
        return SafetyReport(flagged=bool(matches), triggers=matches, policy_version=self.policy_version)

    @staticmethod
    def summarize_reports(reports: Iterable[SafetyReport]) -> SafetyReport:
        triggers: List[str] = []
        version = ""
        for report in reports:
            triggers.extend(report.triggers)
            version = report.policy_version or version
        return SafetyReport(flagged=bool(triggers), triggers=triggers, policy_version=version)


__all__ = ["SafetyEngine", "SafetyReport", "SafetyRule"]
