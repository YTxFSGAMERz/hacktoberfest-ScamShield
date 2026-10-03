"""Tests for scamshield.analyzer"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from scamshield.analyzer import analyze_screenshot, validate_image, AnalysisError

SAMPLES_DIR = Path(__file__).parent / "samples"


# ── Image validation tests ─────────────────────────────────────────────────────

def test_validate_image_too_large():
    """Should reject images over 10 MB."""
    big_bytes = b"\xff\xd8\xff" + b"x" * (11 * 1024 * 1024)
    with pytest.raises(AnalysisError, match="too large"):
        validate_image(big_bytes)


def test_validate_image_invalid_format():
    """Should reject non-image files."""
    with pytest.raises(AnalysisError, match="Invalid image"):
        validate_image(b"this is not an image")


def test_validate_image_valid_jpeg():
    """Should accept valid JPEG magic bytes."""
    jpeg_magic = b"\xff\xd8\xff\xe0" + b"\x00" * 100
    validate_image(jpeg_magic)  # Should not raise


def test_validate_image_valid_png():
    """Should accept valid PNG magic bytes."""
    png_magic = b"\x89PNG" + b"\r\n\x1a\n" + b"\x00" * 100
    validate_image(png_magic)  # Should not raise


# ── Analysis tests ─────────────────────────────────────────────────────────────

MOCK_SCAM_RESULT = {
    "verdict": "SCAM",
    "risk_score": 95,
    "confidence": "HIGH",
    "scam_type": "KYC Fraud",
    "summary": "This is a fake KYC verification message. SBI never asks for OTP via SMS.",
    "red_flags": [
        "Urgency: 'Your account will be blocked in 24 hours'",
        "Requesting OTP via link",
        "Suspicious short URL",
    ],
    "advice": "Do not click the link. Call SBI official number 1800-11-2211 to verify.",
}

MOCK_SAFE_RESULT = {
    "verdict": "SAFE",
    "risk_score": 5,
    "confidence": "HIGH",
    "scam_type": "None",
    "summary": "This appears to be a legitimate bank transaction notification.",
    "red_flags": [],
    "advice": "No action needed. This looks like a genuine transaction alert.",
}


def _make_valid_jpeg() -> bytes:
    """Create a minimal valid JPEG for testing."""
    from PIL import Image
    import io
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@patch("scamshield.analyzer.analyze_image", return_value=(MOCK_SCAM_RESULT, "gemini"))
def test_analyze_screenshot_scam(mock_analyze):
    """Should return SCAM verdict for scam image."""
    image_bytes = _make_valid_jpeg()
    result, provider = analyze_screenshot(image_bytes, lang="en")

    assert result["verdict"] == "SCAM"
    assert result["risk_score"] == 95
    assert provider == "gemini"
    assert len(result["red_flags"]) > 0


@patch("scamshield.analyzer.analyze_image", return_value=(MOCK_SAFE_RESULT, "ollama"))
def test_analyze_screenshot_safe(mock_analyze):
    """Should return SAFE verdict for legitimate content."""
    image_bytes = _make_valid_jpeg()
    result, provider = analyze_screenshot(image_bytes, lang="en")

    assert result["verdict"] == "SAFE"
    assert result["risk_score"] < 30
    assert provider == "ollama"
    assert result["red_flags"] == []


@patch("scamshield.analyzer.analyze_image", return_value=(MOCK_SCAM_RESULT, "gemini"))
def test_analyze_screenshot_hindi(mock_analyze):
    """Should work with Hindi language."""
    image_bytes = _make_valid_jpeg()
    result, provider = analyze_screenshot(image_bytes, lang="hi")
    assert result["verdict"] == "SCAM"


@patch("scamshield.analyzer.analyze_image", return_value=(MOCK_SCAM_RESULT, "gemini"))
def test_analyze_screenshot_gujarati(mock_analyze):
    """Should work with Gujarati language."""
    image_bytes = _make_valid_jpeg()
    result, provider = analyze_screenshot(image_bytes, lang="gu")
    assert result["verdict"] == "SCAM"


# ── Normalization tests ────────────────────────────────────────────────────────

@patch("scamshield.analyzer.analyze_image")
def test_normalize_invalid_verdict(mock_analyze):
    """Should normalize invalid verdict to SUSPICIOUS."""
    mock_analyze.return_value = ({
        "verdict": "MAYBE",  # invalid
        "risk_score": 60,
        "confidence": "MEDIUM",
        "scam_type": "Unknown",
        "summary": "Test",
        "red_flags": [],
        "advice": "Be careful",
    }, "gemini")
    image_bytes = _make_valid_jpeg()
    result, _ = analyze_screenshot(image_bytes)
    assert result["verdict"] == "SUSPICIOUS"


@patch("scamshield.analyzer.analyze_image")
def test_normalize_risk_score_bounds(mock_analyze):
    """Should clamp risk_score between 0 and 100."""
    mock_analyze.return_value = ({
        "verdict": "SCAM",
        "risk_score": 150,  # out of bounds
        "confidence": "HIGH",
        "scam_type": "Test",
        "summary": "Test",
        "red_flags": [],
        "advice": "Test",
    }, "gemini")
    image_bytes = _make_valid_jpeg()
    result, _ = analyze_screenshot(image_bytes)
    assert result["risk_score"] == 100


# ── Sample file tests ──────────────────────────────────────────────────────────

@pytest.mark.skipif(
    not SAMPLES_DIR.exists(),
    reason="samples/ directory not found",
)
def test_sample_files_exist():
    """Ensure sample scam screenshots are present."""
    samples = list(SAMPLES_DIR.glob("*.png")) + list(SAMPLES_DIR.glob("*.jpg"))
    assert len(samples) > 0, "No sample images found in tests/samples/"
