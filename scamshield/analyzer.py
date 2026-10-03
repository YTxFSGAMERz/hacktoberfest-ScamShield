"""ScamShield — Core analyzer that orchestrates LLM + prompts."""

from __future__ import annotations

import logging

from .llm import analyze_image, get_provider, LLMError
from .prompts import ANALYSIS_SYSTEM_PROMPT, build_analysis_prompt

logger = logging.getLogger(__name__)

MAX_IMAGE_SIZE_MB = 10
MAX_IMAGE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024


class AnalysisError(Exception):
    """Raised when analysis fails."""


def validate_image(image_bytes: bytes) -> None:
    """Validate image size and format.

    Raises:
        AnalysisError: if validation fails.
    """
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise AnalysisError(f"Image too large ({len(image_bytes) // 1024 // 1024} MB). Max is {MAX_IMAGE_SIZE_MB} MB.")

    # Check magic bytes for common image formats
    magic_map = {
        b"\xff\xd8\xff": "JPEG",
        b"\x89PNG": "PNG",
        b"RIFF": "WEBP",  # WEBP starts with RIFF
        b"GIF8": "GIF",
    }
    is_valid = any(image_bytes[:4].startswith(magic) for magic in magic_map)
    if not is_valid:
        raise AnalysisError("Invalid image format. Please upload a JPG, PNG, or WEBP image.")


def analyze_screenshot(image_bytes: bytes, lang: str = "en") -> tuple[dict, str]:
    """Analyze a screenshot for scams.

    Args:
        image_bytes: Raw image bytes from the uploaded file.
        lang: Output language code ("en", "hi", "gu").

    Returns:
        (result_dict, provider_used) where result_dict has keys:
            verdict, risk_score, confidence, scam_type, summary, red_flags, advice

    Raises:
        AnalysisError: If validation or analysis fails.
        LLMError: If no AI provider is available.
    """
    validate_image(image_bytes)

    user_prompt = build_analysis_prompt(lang)
    system_prompt = ANALYSIS_SYSTEM_PROMPT

    try:
        result, provider = analyze_image(
            image_bytes=image_bytes,
            user_prompt=user_prompt,
            system_prompt=system_prompt,
        )
        _normalize_result(result)
        return result, provider
    except LLMError:
        raise
    except Exception as e:
        logger.exception("Unexpected error during analysis")
        raise AnalysisError(f"Analysis failed: {e}") from e


def _normalize_result(result: dict) -> None:
    """Ensure result has all required fields with valid values."""
    # Normalize verdict
    verdict = str(result.get("verdict", "SUSPICIOUS")).upper()
    if verdict not in ("SAFE", "SUSPICIOUS", "SCAM"):
        verdict = "SUSPICIOUS"
    result["verdict"] = verdict

    # Normalize risk score
    try:
        score = int(result.get("risk_score", 50))
        result["risk_score"] = max(0, min(100, score))
    except (TypeError, ValueError):
        result["risk_score"] = 50

    # Normalize confidence
    confidence = str(result.get("confidence", "MEDIUM")).upper()
    if confidence not in ("LOW", "MEDIUM", "HIGH"):
        confidence = "MEDIUM"
    result["confidence"] = confidence

    # Ensure red_flags is a list
    if not isinstance(result.get("red_flags"), list):
        result["red_flags"] = []

    # Ensure required text fields
    for field in ("summary", "advice", "scam_type"):
        if not result.get(field):
            result[field] = "N/A"
