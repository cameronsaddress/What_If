"""
Input validation, sanitization, and content safety for the What If simulator.
"""

import re
import html
from typing import Optional, Tuple


class InputValidator:
    """Validate and sanitize user inputs."""

    @staticmethod
    def sanitize_decision(decision: str) -> str:
        """Sanitize user decision input: escape HTML, enforce length, collapse whitespace."""
        decision = html.escape(decision)

        max_length = 500
        if len(decision) > max_length:
            decision = decision[:max_length] + "..."

        decision = " ".join(decision.split())
        return decision

    @staticmethod
    def validate_mode(mode: str) -> str:
        valid = ["realistic", "50/50", "random"]
        return mode if mode in valid else "realistic"


class ContentFilter:
    """Light content-safety gate for simulation inputs."""

    @staticmethod
    def check_content_safety(text: str) -> Tuple[bool, Optional[str]]:
        """Return (is_safe, reason_if_not). Only blocks genuinely harmful prompts."""
        checks = [
            (r"\b(suicide|self[- ]?harm)\b", "self-harm content"),
        ]
        for pattern, reason in checks:
            if re.search(pattern, text, re.IGNORECASE):
                return False, reason
        return True, None

    @staticmethod
    def sanitize_output(text: str) -> str:
        """Strip potential injection vectors from LLM output."""
        text = re.sub(r"<script.*?>.*?</script>", "", text, flags=re.DOTALL)
        text = re.sub(r"javascript:", "", text, flags=re.IGNORECASE)
        text = html.escape(text)
        return text


# Module-level singletons
input_validator = InputValidator()
content_filter = ContentFilter()
