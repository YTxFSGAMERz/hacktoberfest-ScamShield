"""ScamShield — AI Safety Chat Assistant powered by Gemma 4.

Supports multi-turn interactive conversation in English, Hindi, and Gujarati.
Can take the current screenshot analysis as context for follow-up questions.
"""

from __future__ import annotations

import logging
import os
import requests
from dotenv import load_dotenv

from .llm import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    OLLAMA_MODEL,
    OLLAMA_BASE_URL,
    LLM_PROVIDER,
    _gemini_available,
    _ollama_available,
    LLMError,
)

load_dotenv()
logger = logging.getLogger(__name__)

CHAT_SYSTEM_PROMPT = """You are ScamShield AI, an empathetic and razor-sharp cybersecurity assistant specializing in scam detection, fraud defense, and digital safety for users in India and worldwide.

Your capabilities:
1. Advise users on whether messages, calls, apps, links, or job offers are scams.
2. Explain how specific frauds work (Digital Arrest, KYC block, UPI refund fraud, APK malware, fake trading apps, loan recovery harassment, electricity disconnection threats).
3. Provide step-by-step guidance if someone has already been scammed:
   - Call National Cyber Crime Helpline: 1930 immediately
   - File an official complaint at https://cybercrime.gov.in
   - Contact their bank to freeze accounts / reverse UPI transactions (golden hour rule)
   - Report fraud SMS/numbers to Chakshu portal (Sanchar Saathi)
4. Be clear, calm, practical, and supportive. Use bullet points for action items.
5. If screenshot analysis context is provided, refer to it directly.

Language rule:
- If asked in English: answer in English.
- If asked in Hindi (or lang=hi): answer in clear Hindi (हिंदी).
- If asked in Gujarati (or lang=gu): answer in clear Gujarati (ગુજરાતી).
"""


def _call_gemini_chat(
    contents: list[dict],
    system_instruction: str,
    api_key: str,
    model: str,
) -> str:
    """Call Gemini generateContent with multi-turn contents."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "system_instruction": {
            "parts": [{"text": system_instruction}]
        },
        "contents": contents,
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 2048,
        },
    }

    response = requests.post(url, json=payload, timeout=60)
    response.raise_for_status()

    data = response.json()
    candidates = data.get("candidates", [])
    if not candidates:
        raise LLMError("Gemma 4 returned an empty response.")

    parts = candidates[0].get("content", {}).get("parts", [])
    answer_parts = [p.get("text", "") for p in parts if not p.get("thought", False)]
    if answer_parts:
        return "".join(answer_parts).strip()
    return parts[-1].get("text", "").strip() if parts else ""


def _call_ollama_chat(
    messages: list[dict],
    system_instruction: str,
) -> str:
    """Call local Ollama /api/chat with conversation history."""
    ollama_messages = [{"role": "system", "content": system_instruction}]
    for msg in messages:
        ollama_messages.append({"role": msg["role"], "content": msg["content"]})

    payload = {
        "model": os.getenv("OLLAMA_MODEL", OLLAMA_MODEL),
        "messages": ollama_messages,
        "stream": False,
        "options": {
            "temperature": 0.4,
            "num_predict": 1024,
        },
    }

    response = requests.post(
        f"{os.getenv('OLLAMA_BASE_URL', OLLAMA_BASE_URL)}/api/chat",
        json=payload,
        timeout=90,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("message", {}).get("content", "").strip()


def chat_with_scamshield(
    messages: list[dict],
    current_analysis: dict | None = None,
    lang: str = "en",
) -> tuple[str, str]:
    """Have a conversation with ScamShield AI assistant.

    Args:
        messages: List of {"role": "user"|"assistant", "content": "..."}
        current_analysis: Optional analysis dict from screenshot scan.
        lang: Preferred language code ("en", "hi", "gu").

    Returns:
        (assistant_reply, provider_used)
    """
    if not messages:
        return "", "none"

    lang_hint = {
        "en": "Respond in English.",
        "hi": "कृपया हिंदी में उत्तर दें (Respond in Hindi).",
        "gu": "કૃપા કરીને ગુજરાતીમાં જવાબ આપો (Respond in Gujarati).",
    }.get(lang, "Respond in English.")

    system_instruction = f"{CHAT_SYSTEM_PROMPT}\n\nLanguage Preference: {lang_hint}"

    if current_analysis:
        context_str = (
            f"\n\n[Active Screenshot Analysis Context]:\n"
            f"- Verdict: {current_analysis.get('verdict')}\n"
            f"- Risk Score: {current_analysis.get('risk_score')}/100\n"
            f"- Scam Type: {current_analysis.get('scam_type')}\n"
            f"- Summary: {current_analysis.get('summary')}\n"
            f"- Red Flags: {', '.join(current_analysis.get('red_flags', []))}\n"
            f"- Advice: {current_analysis.get('advice')}\n"
        )
        system_instruction += context_str

    # Format contents for Gemini
    gemini_contents = []
    for msg in messages:
        role = "model" if msg["role"] == "assistant" else "user"
        gemini_contents.append({
            "role": role,
            "parts": [{"text": msg["content"]}]
        })

    api_key = os.getenv("GEMINI_API_KEY", GEMINI_API_KEY)
    model = os.getenv("GEMINI_MODEL", GEMINI_MODEL)

    # Provider routing (auto: try Gemini, fallback Ollama)
    provider_pref = os.getenv("LLM_PROVIDER", LLM_PROVIDER).lower()

    if provider_pref in ("auto", "gemini") and _gemini_available():
        try:
            reply = _call_gemini_chat(gemini_contents, system_instruction, api_key, model)
            return reply, "gemini"
        except Exception as e:
            logger.warning("Gemini chat failed (%s), attempting Ollama...", e)
            if provider_pref == "gemini":
                raise LLMError(f"Gemini chat failed: {e}") from e

    if _ollama_available():
        try:
            reply = _call_ollama_chat(messages, system_instruction)
            return reply, "ollama"
        except Exception as e:
            raise LLMError(f"Ollama chat failed: {e}") from e

    raise LLMError("No AI provider available for chat. Configure GEMINI_API_KEY in .env.")
