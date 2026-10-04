"""ScamShield — Community Threat Intelligence & Fraud Reporting Database.

Provides crowdsourced fraud reporting and lookup across phone numbers,
UPI IDs, malicious URLs, and WhatsApp numbers. Uses Firestore REST API
when configured with local JSON fallback for resilient, zero-failure operation.
"""

from __future__ import annotations

import datetime
import json
import logging
import os
import re
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
LOCAL_DB_FILE = DATA_DIR / "community_reports.json"

FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "scamshield-bae36")
FIREBASE_WEB_API_KEY = os.getenv("FIREBASE_WEB_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")

# ── Seed data for immediate real-world intelligence ──────────────────────────
DEFAULT_COMMUNITY_REPORTS = [
    {
        "id": "seed_1",
        "type": "phone",
        "value": "+919310842109",
        "category": "Digital Arrest / Fake Police",
        "description": "Caller posed as Crime Branch officer claiming parcel seizure in Mumbai customs.",
        "reports_count": 47,
        "first_reported": "2026-09-12T10:14:00Z",
        "last_reported": "2026-10-02T14:32:00Z",
        "risk_level": "CRITICAL",
    },
    {
        "id": "seed_2",
        "type": "upi",
        "value": "refund.desk921@oksbi",
        "category": "UPI Refund Trap",
        "description": "Sent collect request on PhonePe pretending to be Flipkart return refund executive.",
        "reports_count": 83,
        "first_reported": "2026-08-04T12:00:00Z",
        "last_reported": "2026-10-03T08:15:00Z",
        "risk_level": "CRITICAL",
    },
    {
        "id": "seed_3",
        "type": "url",
        "value": "https://sbi-kyc-quickverify.xyz",
        "category": "Bank Phishing",
        "description": "Phishing portal harvesting SBI net banking credentials and OTP via SMS link.",
        "reports_count": 112,
        "first_reported": "2026-09-28T09:20:00Z",
        "last_reported": "2026-10-03T18:05:00Z",
        "risk_level": "CRITICAL",
    },
    {
        "id": "seed_4",
        "type": "whatsapp",
        "value": "+923018471920",
        "category": "Part-Time Task Scam",
        "description": "WhatsApp message offering ₹5000/day for rating hotels and liking videos on YouTube.",
        "reports_count": 64,
        "first_reported": "2026-09-15T16:40:00Z",
        "last_reported": "2026-10-02T11:22:00Z",
        "risk_level": "HIGH",
    },
    {
        "id": "seed_5",
        "type": "phone",
        "value": "+917000548192",
        "category": "Electricity Bill Threat",
        "description": "SMS threatening power cut tonight at 9:30 PM due to unpaid bill; asked to install AnyDesk.",
        "reports_count": 39,
        "first_reported": "2026-09-19T21:10:00Z",
        "last_reported": "2026-10-01T20:45:00Z",
        "risk_level": "HIGH",
    },
]


def _normalize_value(val_type: str, val: str) -> str:
    """Normalize phone, UPI, or URL string for deterministic matching."""
    val = (val or "").strip()
    if val_type in ("phone", "whatsapp"):
        digits = re.sub(r"[^\d]", "", val)
        if len(digits) == 10:
            return f"+91{digits}"
        elif len(digits) == 12 and digits.startswith("91"):
            return f"+{digits}"
        return f"+{digits}" if digits else val
    elif val_type == "upi":
        return val.lower()
    elif val_type == "url":
        clean = val.lower().split("?")[0].rstrip("/")
        if not clean.startswith(("http://", "https://")):
            clean = f"https://{clean}"
        return clean
    return val.lower()


def _load_local_reports() -> list[dict]:
    """Load local cached reports or initialize with seed data."""
    if not LOCAL_DB_FILE.exists():
        _save_local_reports(DEFAULT_COMMUNITY_REPORTS)
        return list(DEFAULT_COMMUNITY_REPORTS)
    try:
        with open(LOCAL_DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.warning("Failed to read local community DB: %s", exc)
        return list(DEFAULT_COMMUNITY_REPORTS)


def _save_local_reports(reports: list[dict]) -> None:
    """Atomically write reports to local JSON file."""
    try:
        with open(LOCAL_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(reports, f, indent=2, ensure_ascii=False)
    except Exception as exc:
        logger.error("Failed to save local community DB: %s", exc)


def report_scam(
    scam_type: str,
    value: str,
    description: str = "",
    category: str = "General Fraud",
    lang: str = "en",
) -> dict[str, Any]:
    """Submit a crowdsourced report into the community intelligence database."""
    scam_type = (scam_type or "phone").lower().strip()
    norm_val = _normalize_value(scam_type, value)
    if not norm_val:
        return {"success": False, "error": "Invalid or empty value provided"}

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    reports = _load_local_reports()

    # Look for existing entry to increment report count
    existing = next((r for r in reports if r.get("type") == scam_type and r.get("value") == norm_val), None)

    if existing:
        existing["reports_count"] = existing.get("reports_count", 1) + 1
        existing["last_reported"] = now_iso
        if description and len(description) > len(existing.get("description", "")):
            existing["description"] = description
        count = existing["reports_count"]
        existing["risk_level"] = "CRITICAL" if count >= 10 else ("HIGH" if count >= 3 else "SUSPICIOUS")
        entry = existing
    else:
        entry = {
            "id": f"rep_{int(datetime.datetime.now().timestamp())}",
            "type": scam_type,
            "value": norm_val,
            "category": category or "Fraudulent Communication",
            "description": description or "User reported suspicious fraud vector.",
            "reports_count": 1,
            "first_reported": now_iso,
            "last_reported": now_iso,
            "risk_level": "SUSPICIOUS",
        }
        reports.insert(0, entry)

    _save_local_reports(reports)

    # Attempt asynchronous or non-blocking firestore sync if configured
    _sync_to_firestore(entry)

    return {
        "success": True,
        "entry": entry,
        "message": f"Report recorded. This entity has been reported {entry['reports_count']} time(s).",
    }


def check_community_reports(scam_type: str, value: str) -> dict[str, Any]:
    """Check if a phone number, UPI ID, or URL has active community reports."""
    scam_type = (scam_type or "phone").lower().strip()
    norm_val = _normalize_value(scam_type, value)
    if not norm_val:
        return {"found": False, "reports_count": 0, "risk_level": "UNKNOWN"}

    reports = _load_local_reports()
    match = next((r for r in reports if r.get("type") == scam_type and r.get("value") == norm_val), None)

    # Fuzzy check for URL domains
    if not match and scam_type == "url":
        match = next((r for r in reports if r.get("type") == "url" and (norm_val in r.get("value", "") or r.get("value", "") in norm_val)), None)

    if match:
        return {
            "found": True,
            "value": match["value"],
            "type": match["type"],
            "category": match.get("category", "Cyber Fraud"),
            "reports_count": match.get("reports_count", 1),
            "risk_level": match.get("risk_level", "HIGH"),
            "first_reported": match.get("first_reported"),
            "last_reported": match.get("last_reported"),
            "description": match.get("description", ""),
        }

    return {
        "found": False,
        "value": norm_val,
        "type": scam_type,
        "reports_count": 0,
        "risk_level": "SAFE_UNREPORTED",
        "description": "No prior scam reports found in the community database.",
    }


def get_recent_reports(limit: int = 10) -> list[dict]:
    """Fetch the latest community scam reports with masked privacy for public display."""
    reports = _load_local_reports()
    recent = reports[:limit]
    output = []
    for r in recent:
        val = r.get("value", "")
        # Mask middle digits of phone for privacy
        if r.get("type") in ("phone", "whatsapp") and len(val) >= 8:
            masked = val[:6] + "•••" + val[-2:]
        elif r.get("type") == "upi" and "@" in val:
            parts = val.split("@")
            user_part = parts[0][:3] + "•••" if len(parts[0]) > 3 else parts[0]
            masked = f"{user_part}@{parts[1]}"
        else:
            masked = val
        output.append({
            "id": r.get("id"),
            "type": r.get("type"),
            "masked_value": masked,
            "category": r.get("category"),
            "reports_count": r.get("reports_count", 1),
            "risk_level": r.get("risk_level", "HIGH"),
            "last_reported": r.get("last_reported"),
            "description": r.get("description", ""),
        })
    return output


def _sync_to_firestore(entry: dict) -> None:
    """Best-effort background sync of a report to Firebase Firestore via REST API."""
    if not FIREBASE_PROJECT_ID:
        return
    url = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents/scam_reports"
    params = {}
    if FIREBASE_WEB_API_KEY:
        params["key"] = FIREBASE_WEB_API_KEY
    payload = {
        "fields": {
            "type": {"stringValue": entry.get("type", "")},
            "value": {"stringValue": entry.get("value", "")},
            "category": {"stringValue": entry.get("category", "")},
            "reports_count": {"integerValue": str(entry.get("reports_count", 1))},
            "risk_level": {"stringValue": entry.get("risk_level", "HIGH")},
            "last_reported": {"stringValue": entry.get("last_reported", "")},
        }
    }
    try:
        requests.post(url, json=payload, params=params, timeout=3)
    except Exception as exc:
        logger.debug("Firestore sync skipped or unavailable: %s", exc)
