"""ScamShield — LLM provider abstraction.

Supports:
  - Gemini API (primary): gemma-4-e4b-it
  - Ollama (fallback):    gemma4:e4b
  - LLM_PROVIDER=auto:   tries Gemini, falls back to Ollama on error

Usage:
    from scamshield.llm import get_provider, analyze_image

    provider = get_provider()  # returns "gemini", "ollama", or raises
    result = analyze_image(image_bytes, prompt, system_prompt, provider)
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re

import requests
from dotenv import load_dotenv
from PIL import Image
import io

load_dotenv()

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto").lower()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemma-4-26b-a4b-it")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:e4b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")



class LLMError(Exception):
    """Raised when all LLM providers fail."""


# ── Provider detection ─────────────────────────────────────────────────────────

def _gemini_available() -> bool:
    """Check if Gemini API key is configured."""
    return bool(GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here")


def _ollama_available() -> bool:
    """Check if Ollama is running locally."""
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        if r.status_code == 200:
            models = [m["name"] for m in r.json().get("models", [])]
            # Accept gemma4:e4b or any gemma4 variant
            return any("gemma4" in m.lower() or "gemma-4" in m.lower() for m in models)
        return False
    except Exception:
        return False


def get_provider() -> str:
    """Determine which LLM provider to use.

    Returns: "gemini" | "ollama"
    Raises: LLMError if no provider is available.
    """
    if LLM_PROVIDER == "gemini":
        if _gemini_available():
            return "gemini"
        raise LLMError("Gemini API key not configured. Set GEMINI_API_KEY in .env")

    if LLM_PROVIDER == "ollama":
        if _ollama_available():
            return "ollama"
        raise LLMError(
            f"Ollama not available or {OLLAMA_MODEL} not installed. "
            "Run: ollama pull gemma4:e4b"
        )

    # auto mode: try Gemini first, then Ollama
    if _gemini_available():
        return "gemini"
    if _ollama_available():
        logger.warning("Gemini API not configured; falling back to Ollama.")
        return "ollama"

    raise LLMError(
        "No AI provider available. Configure GEMINI_API_KEY in .env "
        "or install Ollama with: ollama pull gemma4:e4b"
    )


def get_provider_status() -> dict:
    """Return dictionary of current provider availability and config."""
    gemini_ok = _gemini_available()
    ollama_ok = _ollama_available()
    try:
        active = get_provider()
    except Exception:
        active = "none"
    return {
        "active_provider": active,
        "gemini_available": gemini_ok,
        "ollama_available": ollama_ok,
        "gemini_model": os.getenv("GEMINI_MODEL", GEMINI_MODEL),
        "ollama_model": os.getenv("OLLAMA_MODEL", OLLAMA_MODEL),
    }


# ── Image preprocessing ────────────────────────────────────────────────────────

def _prepare_image(image_bytes: bytes, max_size: tuple[int, int] = (1024, 1024)) -> bytes:
    """Resize image if too large, convert to JPEG for API efficiency."""
    img = Image.open(io.BytesIO(image_bytes))
    img = img.convert("RGB")
    img.thumbnail(max_size, Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


# ── Gemini API ─────────────────────────────────────────────────────────────────

def _call_gemini(image_bytes: bytes, user_prompt: str, system_prompt: str) -> str:
    """Call Gemini API with vision support using REST."""
    processed = _prepare_image(image_bytes)
    b64_image = base64.b64encode(processed).decode("utf-8")

    payload = {
        "system_instruction": {
            "parts": [{"text": system_prompt}]
        },
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": b64_image,
                        }
                    },
                    {"text": user_prompt},
                ],
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 2048,
        },
    }

    api_key = os.getenv("GEMINI_API_KEY", GEMINI_API_KEY)
    model = os.getenv("GEMINI_MODEL", GEMINI_MODEL)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    response = requests.post(url, json=payload, timeout=60)
    response.raise_for_status()

    data = response.json()
    candidates = data.get("candidates", [])
    if not candidates:
        raise LLMError(f"Gemini returned no candidates: {data}")

    parts = candidates[0].get("content", {}).get("parts", [])
    # Separate thoughts from answer text (Gemma 4 has native thought tokens)
    thought_parts = [p.get("text", "") for p in parts if p.get("thought", False)]
    answer_parts = [p.get("text", "") for p in parts if not p.get("thought", False)]

    text = "".join(answer_parts) if answer_parts else (parts[-1].get("text", "") if parts else "")
    reasoning = "\n\n".join(thought_parts).strip()
    return text, reasoning


# ── Ollama API ─────────────────────────────────────────────────────────────────

def _call_ollama(image_bytes: bytes, user_prompt: str, system_prompt: str) -> str:
    """Call local Ollama API with vision support."""
    processed = _prepare_image(image_bytes)
    b64_image = base64.b64encode(processed).decode("utf-8")

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": user_prompt,
        "system": system_prompt,
        "images": [b64_image],
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 1024,
        },
    }

    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json=payload,
        timeout=120,
    )
    response.raise_for_status()

    data = response.json()
    return data.get("response", "")


# ── JSON extraction ────────────────────────────────────────────────────────────

def _extract_json(text: str) -> dict:
    """Extract and parse JSON from LLM response text."""
    # Try direct parse first
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON block in markdown fences
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass

    # Try to extract bare JSON object
    obj_match = re.search(r"\{.*\}", text, re.DOTALL)
    if obj_match:
        try:
            return json.loads(obj_match.group(0))
        except json.JSONDecodeError:
            pass

    # Return a safe fallback
    logger.warning("Could not parse JSON from LLM response: %s", text[:200])
    return {
        "verdict": "SUSPICIOUS",
        "risk_score": 50,
        "confidence": "LOW",
        "scam_type": "Unknown",
        "summary": "Analysis could not be parsed. Treat with caution.",
        "red_flags": ["AI response parsing error — manual review recommended"],
        "advice": "Show this to someone you trust for a second opinion.",
    }


# ── Main entry point ───────────────────────────────────────────────────────────

def analyze_image(
    image_bytes: bytes,
    user_prompt: str,
    system_prompt: str,
    provider: str | None = None,
) -> tuple[dict, str]:
    """Analyze an image for scams.

    Args:
        image_bytes: Raw image bytes.
        user_prompt: The analysis prompt.
        system_prompt: The system/role prompt.
        provider: "gemini" | "ollama" | None (auto-detect).

    Returns:
        (result_dict, provider_used)

    Raises:
        LLMError: If all providers fail.
    """
    if provider is None:
        provider = get_provider()

    raw_text = ""

    if provider == "gemini":
        try:
            raw_text, reasoning = _call_gemini(image_bytes, user_prompt, system_prompt)
            data = _extract_json(raw_text)
            if reasoning and not data.get("reasoning"):
                data["reasoning"] = reasoning
            return data, "gemini"
        except Exception as e:
            if LLM_PROVIDER == "gemini":
                raise LLMError(f"Gemini failed: {e}") from e
            # In auto mode, try Ollama
            logger.warning("Gemini failed (%s), trying Ollama...", e)
            if _ollama_available():
                raw_text = _call_ollama(image_bytes, user_prompt, system_prompt)
                return _extract_json(raw_text), "ollama"
            raise LLMError(f"Gemini failed and Ollama not available: {e}") from e

    if provider == "ollama":
        try:
            raw_text = _call_ollama(image_bytes, user_prompt, system_prompt)
            return _extract_json(raw_text), "ollama"
        except Exception as e:
            raise LLMError(f"Ollama failed: {e}") from e

    raise LLMError(f"Unknown provider: {provider}")
