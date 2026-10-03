"""Tests for scamshield.chat and scamshield.intel modules."""

import pytest
from unittest.mock import patch, MagicMock

from scamshield.intel import EMERGENCY_CONTACTS, SCAM_TRENDS, GOLDEN_HOUR_STEPS
from scamshield.chat import chat_with_scamshield, CHAT_SYSTEM_PROMPT


# ── Intel module tests ─────────────────────────────────────────────────────────

def test_emergency_contacts_integrity():
    assert len(EMERGENCY_CONTACTS) >= 3
    for contact in EMERGENCY_CONTACTS:
        assert "name" in contact
        assert "name_hi" in contact
        assert "name_gu" in contact
        assert "number" in contact
        assert "url" in contact


def test_scam_trends_integrity():
    assert len(SCAM_TRENDS) >= 5
    for item in SCAM_TRENDS:
        assert "id" in item
        assert "title" in item
        assert "title_hi" in item
        assert "title_gu" in item
        assert "pattern" in item
        assert "reality_check" in item
        assert item["severity"] in ("CRITICAL", "HIGH", "MEDIUM")


def test_golden_hour_steps_integrity():
    assert len(GOLDEN_HOUR_STEPS) == 4
    for step in GOLDEN_HOUR_STEPS:
        assert "step" in step
        assert "step_hi" in step
        assert "step_gu" in step
        assert "detail" in step


# ── Chat module tests ──────────────────────────────────────────────────────────

def test_chat_empty_messages():
    reply, provider = chat_with_scamshield([])
    assert reply == ""
    assert provider == "none"


@patch("scamshield.chat._call_gemini_chat", return_value="Never share your OTP with anyone.")
@patch("scamshield.chat._gemini_available", return_value=True)
def test_chat_gemini_success(mock_gemini_avail, mock_gemini_call):
    messages = [{"role": "user", "content": "Someone asked for my OTP. Should I give it?"}]
    reply, provider = chat_with_scamshield(messages, lang="en")

    assert "OTP" in reply
    assert provider == "gemini"
    assert mock_gemini_call.called


@patch("scamshield.chat._call_gemini_chat", return_value="अपने बैंक से तुरंत संपर्क करें।")
@patch("scamshield.chat._gemini_available", return_value=True)
def test_chat_hindi_context(mock_gemini_avail, mock_gemini_call):
    messages = [{"role": "user", "content": "क्या यह सुरक्षित है?"}]
    analysis = {
        "verdict": "SCAM",
        "risk_score": 90,
        "scam_type": "KYC Fraud",
        "summary": "Fake bank message",
        "red_flags": ["OTP asked"],
        "advice": "Do not click",
    }
    reply, provider = chat_with_scamshield(messages, current_analysis=analysis, lang="hi")
    assert provider == "gemini"
    # Verify context was passed
    args, kwargs = mock_gemini_call.call_args
    sys_instruction = args[1]
    assert "SCAM" in sys_instruction
    assert "KYC Fraud" in sys_instruction


@patch("scamshield.chat._call_ollama_chat", return_value="1930 પર કૉલ કરો.")
@patch("scamshield.chat._gemini_available", return_value=False)
@patch("scamshield.chat._ollama_available", return_value=True)
def test_chat_ollama_fallback(mock_ollama_avail, mock_gemini_avail, mock_ollama_call):
    messages = [{"role": "user", "content": "હું શું કરું?"}]
    reply, provider = chat_with_scamshield(messages, lang="gu")
    assert provider == "ollama"
    assert "1930" in reply
