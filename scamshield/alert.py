"""ScamShield — Family alert via Discord webhook with clipboard fallback."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")


class AlertError(Exception):
    """Raised when the Discord alert fails."""


def _build_discord_payload(alert_text: str, result: dict) -> dict:
    """Build a Discord webhook embed payload."""
    verdict = result.get("verdict", "SUSPICIOUS")
    risk_score = result.get("risk_score", 0)

    color_map = {
        "SAFE": 0x00C851,        # green
        "SUSPICIOUS": 0xFF8800,  # orange
        "SCAM": 0xFF4444,        # red
    }
    color = color_map.get(verdict, 0xFF8800)

    red_flags = result.get("red_flags", [])
    flags_str = "\n".join(f"• {f}" for f in red_flags) if red_flags else "None"

    embed = {
        "title": f"🛡️ ScamShield Alert — {verdict}",
        "description": result.get("summary", ""),
        "color": color,
        "fields": [
            {"name": "Risk Score", "value": f"{risk_score}/100", "inline": True},
            {"name": "Confidence", "value": result.get("confidence", "?"), "inline": True},
            {"name": "Scam Type", "value": result.get("scam_type", "Unknown"), "inline": True},
            {"name": "🚩 Red Flags", "value": flags_str, "inline": False},
            {"name": "✅ What to Do", "value": result.get("advice", ""), "inline": False},
        ],
        "footer": {
            "text": f"ScamShield AI • {datetime.now().strftime('%Y-%m-%d %H:%M')} IST"
        },
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
    }

    return {
        "content": "@here ⚠️ Possible scam detected by ScamShield!",
        "embeds": [embed],
        "username": "ScamShield Bot",
        "avatar_url": "https://raw.githubusercontent.com/YTxFSGAMERz/hacktoberfest-ScamShield/main/assets/shield.png",
    }


def send_discord_alert(result: dict, alert_text: str) -> bool:
    """Send a scam alert to the configured Discord webhook.

    Args:
        result: The analysis result dict.
        alert_text: Plain-text fallback message (also used as content).

    Returns:
        True if sent successfully, False otherwise.

    Raises:
        AlertError: If DISCORD_WEBHOOK_URL is not configured.
    """
    webhook_url = DISCORD_WEBHOOK_URL
    if not webhook_url or webhook_url == "https://discord.com/api/webhooks/your_webhook_id/your_webhook_token":
        raise AlertError("Discord webhook URL not configured. Set DISCORD_WEBHOOK_URL in .env")

    payload = _build_discord_payload(alert_text, result)

    try:
        response = requests.post(webhook_url, json=payload, timeout=15)
        response.raise_for_status()
        logger.info("Discord alert sent successfully.")
        return True
    except requests.HTTPError as e:
        logger.error("Discord webhook HTTP error: %s — %s", e, response.text)
        raise AlertError(f"Discord returned {response.status_code}: {response.text}") from e
    except requests.RequestException as e:
        logger.error("Discord webhook request failed: %s", e)
        raise AlertError(f"Network error sending Discord alert: {e}") from e


def copy_to_clipboard(text: str) -> bool:
    """Copy text to system clipboard as fallback.

    Returns True if successful, False if pyperclip is unavailable.
    """
    try:
        import pyperclip
        pyperclip.copy(text)
        logger.info("Alert text copied to clipboard.")
        return True
    except ImportError:
        logger.warning("pyperclip not installed — clipboard fallback unavailable.")
        return False
    except Exception as e:
        logger.warning("Clipboard copy failed: %s", e)
        return False


def send_alert(result: dict, alert_text: str) -> tuple[str, bool]:
    """Send alert via Discord, falling back to clipboard.

    Returns:
        (method, success) where method is "discord" | "clipboard" | "failed"
    """
    # Try Discord first
    try:
        success = send_discord_alert(result, alert_text)
        if success:
            return "discord", True
    except AlertError as e:
        logger.warning("Discord not available: %s — trying clipboard.", e)

    # Fall back to clipboard
    if copy_to_clipboard(alert_text):
        return "clipboard", True

    return "failed", False
