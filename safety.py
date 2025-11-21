import re
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class SafetyFinding:
    flagged: bool
    reasons: List[str] = field(default_factory=list)
    sanitized_text: str = ""
    redacted_text: str = ""
    final_output: str = ""


class SafetyPipeline:
    """A simple multi-stage safety pipeline that applies detection, sanitization,
    redaction, and final output checks based on a provided policy dictionary.
    """

    def __init__(self, policy: Dict):
        self.policy = policy
        safety_policy = policy.get("safety", {})
        self.blocked_terms = [term.lower() for term in safety_policy.get("blocked_terms", [])]
        self.replacements = safety_policy.get("sanitize_replacements", [])
        self.paraphrase_enabled = safety_policy.get("paraphrase_enabled", False)
        self.paraphrase_hint = safety_policy.get("paraphrase_hint", "")
        self.redact_pii = safety_policy.get("redact_pii", True)
        self.redaction_patterns = safety_policy.get("redaction_patterns", {})
        self.max_output_length = safety_policy.get("max_output_length", 500)
        self.allow_html = safety_policy.get("allow_html", False)
        self.allow_blocked_terms_in_output = safety_policy.get(
            "allow_blocked_terms_in_output", False
        )

    def detect_risk(self, text: str) -> List[str]:
        reasons: List[str] = []
        lower_text = text.lower()
        for term in self.blocked_terms:
            if term in lower_text:
                reasons.append(f"Detected blocked term: '{term}'")
        if not self.allow_html and re.search(r"<[^>]+>", text):
            reasons.append("HTML content is not allowed")
        return reasons

    def sanitize_or_paraphrase(self, text: str) -> str:
        sanitized = text
        for replacement in self.replacements:
            pattern = replacement.get("pattern")
            repl = replacement.get("replacement", "[removed]")
            if not pattern:
                continue
            sanitized = re.sub(pattern, repl, sanitized, flags=re.IGNORECASE)
        if self.paraphrase_enabled and self.paraphrase_hint:
            sanitized = f"{sanitized}\n\n{self.paraphrase_hint}"
        return sanitized

    def redact(self, text: str) -> str:
        redacted = text
        if not self.redact_pii:
            return redacted
        email_placeholder = self.redaction_patterns.get("email", "[EMAIL REDACTED]")
        phone_placeholder = self.redaction_patterns.get("phone", "[PHONE REDACTED]")
        redacted = re.sub(r"[\w\.\-]+@[\w\.-]+", email_placeholder, redacted)
        redacted = re.sub(r"\b\+?\d{1,3}[\s.-]?\(?\d{2,3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b", phone_placeholder, redacted)
        return redacted

    def run_output_checks(self, text: str) -> List[str]:
        issues: List[str] = []
        if len(text) > self.max_output_length:
            issues.append(
                f"Output exceeds maximum length of {self.max_output_length} characters"
            )
        if not self.allow_blocked_terms_in_output:
            lower_text = text.lower()
            for term in self.blocked_terms:
                if term in lower_text:
                    issues.append(f"Output still contains blocked term '{term}'")
        return issues

    def run(self, text: str) -> SafetyFinding:
        finding = SafetyFinding(flagged=False)
        detection_reasons = self.detect_risk(text)
        if detection_reasons:
            finding.flagged = True
            finding.reasons.extend(detection_reasons)

        sanitized = self.sanitize_or_paraphrase(text)
        finding.sanitized_text = sanitized

        redacted = self.redact(sanitized)
        finding.redacted_text = redacted

        output_issues = self.run_output_checks(redacted)
        if output_issues:
            finding.flagged = True
            finding.reasons.extend(output_issues)

        finding.final_output = redacted
        return finding
