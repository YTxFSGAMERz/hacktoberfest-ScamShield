"""Tests for scamshield.llm provider module."""

import pytest
from unittest.mock import patch, MagicMock
import json

from scamshield.llm import (
    _gemini_available,
    _ollama_available,
    _extract_json,
    get_provider,
    LLMError,
)


# ── Provider detection tests ───────────────────────────────────────────────────

def test_gemini_available_with_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSyTestKey123")
    import importlib
    import scamshield.llm as llm_mod
    importlib.reload(llm_mod)
    assert llm_mod._gemini_available()


def test_gemini_not_available_without_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    import importlib
    import scamshield.llm as llm_mod
    importlib.reload(llm_mod)
    assert not llm_mod._gemini_available()


@patch("scamshield.llm.requests.get")
def test_ollama_available_when_running(mock_get):
    mock_get.return_value = MagicMock(
        status_code=200,
        json=lambda: {"models": [{"name": "gemma4:e4b"}]},
    )
    assert _ollama_available()


@patch("scamshield.llm.requests.get")
def test_ollama_not_available_when_down(mock_get):
    mock_get.side_effect = ConnectionError("refused")
    assert not _ollama_available()


@patch("scamshield.llm.requests.get")
def test_ollama_not_available_wrong_model(mock_get):
    mock_get.return_value = MagicMock(
        status_code=200,
        json=lambda: {"models": [{"name": "llama3:8b"}]},  # no gemma4
    )
    assert not _ollama_available()


# ── JSON extraction tests ──────────────────────────────────────────────────────

def test_extract_json_direct():
    """Should parse clean JSON directly."""
    raw = '{"verdict": "SCAM", "risk_score": 90, "confidence": "HIGH", "scam_type": "KYC", "summary": "Bad", "red_flags": ["flag1"], "advice": "Run"}'
    result = _extract_json(raw)
    assert result["verdict"] == "SCAM"
    assert result["risk_score"] == 90


def test_extract_json_from_markdown_fence():
    """Should extract JSON from markdown code blocks."""
    raw = '```json\n{"verdict": "SAFE", "risk_score": 5}\n```'
    result = _extract_json(raw)
    assert result["verdict"] == "SAFE"


def test_extract_json_from_embedded():
    """Should extract bare JSON object from surrounding text."""
    raw = 'Here is my analysis: {"verdict": "SUSPICIOUS", "risk_score": 55} Thank you.'
    result = _extract_json(raw)
    assert result["verdict"] == "SUSPICIOUS"


def test_extract_json_fallback_on_garbage():
    """Should return safe fallback when JSON is completely unparseable."""
    result = _extract_json("This is not JSON at all lol")
    assert result["verdict"] == "SUSPICIOUS"
    assert "red_flags" in result
    assert isinstance(result["red_flags"], list)


# ── Alert tests ────────────────────────────────────────────────────────────────

def test_alert_module_imports():
    """Alert module should import cleanly."""
    from scamshield.alert import send_alert, send_discord_alert, copy_to_clipboard
    assert callable(send_alert)
    assert callable(send_discord_alert)
    assert callable(copy_to_clipboard)


@patch("scamshield.alert.requests.post")
def test_send_discord_alert_success(mock_post, monkeypatch):
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/123/token")
    mock_post.return_value = MagicMock(status_code=204, raise_for_status=lambda: None)
    import importlib
    import scamshield.alert as alert_mod
    importlib.reload(alert_mod)

    result = {
        "verdict": "SCAM",
        "risk_score": 90,
        "confidence": "HIGH",
        "scam_type": "KYC Fraud",
        "summary": "This is a scam.",
        "red_flags": ["OTP requested"],
        "advice": "Don't click.",
    }
    # Should not raise
    alert_mod.send_discord_alert(result, "Test alert")


# ── i18n tests ─────────────────────────────────────────────────────────────────

def test_i18n_english():
    from scamshield.i18n import get_string
    assert "ScamShield" in get_string("en", "app_title")


def test_i18n_hindi():
    from scamshield.i18n import get_string
    result = get_string("hi", "app_title")
    assert len(result) > 0
    # Should contain Devanagari characters
    assert any(ord(c) > 2304 for c in result)


def test_i18n_gujarati():
    from scamshield.i18n import get_string
    result = get_string("gu", "app_title")
    assert len(result) > 0


def test_i18n_fallback_unknown_lang():
    from scamshield.i18n import get_string
    # Unknown language should fall back to English
    result = get_string("zz", "app_title")
    assert "ScamShield" in result


def test_i18n_fallback_unknown_key():
    from scamshield.i18n import get_string
    # Unknown key should return the key itself
    result = get_string("en", "totally_nonexistent_key_xyz")
    assert result == "totally_nonexistent_key_xyz"


# ── Automatic failover tests ───────────────────────────────────────────────────

@patch("scamshield.llm._call_gemini")
@patch("scamshield.llm._call_ollama")
@patch("scamshield.llm._ollama_available")
def test_gemini_failure_auto_switches_to_ollama(mock_ollama_avail, mock_call_ollama, mock_call_gemini, monkeypatch):
    """If Gemini API key fails or errors, it must automatically failover to Ollama."""
    from scamshield.llm import analyze_image

    monkeypatch.setenv("GEMINI_API_KEY", "invalid_or_expired_key")
    monkeypatch.setenv("LLM_PROVIDER", "auto")

    mock_call_gemini.side_effect = Exception("403 Forbidden: API key invalid")
    mock_ollama_avail.return_value = True
    mock_call_ollama.return_value = json.dumps({
        "verdict": "SCAM",
        "risk_score": 90,
        "confidence": "HIGH",
        "scam_type": "UPI Fraud",
        "summary": "Detected fraud via Ollama Cloud fallback",
        "red_flags": ["Fake QR code"],
        "advice": "Do not enter PIN",
    })

    data, provider = analyze_image(b"fake_image_bytes", "Analyze this", "System prompt")
    assert provider == "ollama"
    assert data["verdict"] == "SCAM"
    assert data["risk_score"] == 90
    assert mock_call_gemini.called
    assert mock_call_ollama.called


@patch("scamshield.chat._call_gemini_chat")
@patch("scamshield.chat._call_ollama_chat")
@patch("scamshield.chat._ollama_available")
def test_gemini_chat_failure_auto_switches_to_ollama(mock_ollama_avail, mock_call_ollama_chat, mock_call_gemini_chat, monkeypatch):
    """If Gemini chat fails or errors, it must automatically failover to Ollama."""
    from scamshield.chat import chat_with_scamshield

    monkeypatch.setenv("GEMINI_API_KEY", "invalid_key")
    monkeypatch.setenv("LLM_PROVIDER", "auto")

    mock_call_gemini_chat.side_effect = Exception("429 ResourceExhausted: Quota exceeded")
    mock_ollama_avail.return_value = True
    mock_call_ollama_chat.return_value = "Dial 1930 immediately (Ollama response)."

    reply, provider = chat_with_scamshield([{"role": "user", "content": "Help me"}])
    assert provider == "ollama"
    assert "1930" in reply
    assert mock_call_gemini_chat.called
    assert mock_call_ollama_chat.called


def test_ollama_cloud_headers(monkeypatch):
    """Ollama Cloud should attach Bearer token and detect cloud base URL."""
    from scamshield.llm import _get_ollama_headers, _get_ollama_base_url, _ollama_available

    monkeypatch.setenv("OLLAMA_API_KEY", "test_ollama_cloud_secret_token")
    monkeypatch.setenv("OLLAMA_BASE_URL", "https://ollama.com")

    headers = _get_ollama_headers()
    assert headers["Authorization"] == "Bearer test_ollama_cloud_secret_token"
    assert _get_ollama_base_url() == "https://ollama.com"
    assert _ollama_available() is True
