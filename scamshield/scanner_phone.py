"""ScamShield — Phone number intelligence analyzer.

Multi-layer phone number analysis:
1. TrueCaller RapidAPI — caller identity and spam score
2. NumVerify API — carrier, line type, country validation
3. PhoneInfoga — OSINT deep scan (subprocess)
4. Pattern analysis — VoIP, known scam prefixes, Indian number patterns
5. Fake CBI/ED scam number prefix detection

Usage:
    from scamshield.scanner_phone import analyze_phone

    result = analyze_phone("+91 9876543210")
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import tempfile
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────

TRUECALLER_API_KEY = os.getenv("TRUECALLER_API_KEY", "bd34b3cbdamsh39d55d1d4627c16p10ff1djsn6791bc035576")
TRUECALLER_API_HOST = "truecaller-api12.p.rapidapi.com"
NUMVERIFY_API_KEY = os.getenv("NUMVERIFY_API_KEY", "ae4355c5455a7fca3d7db07a564551eb")
PHONEINFOGA_PATH = os.getenv(
    "PHONEINFOGA_PATH",
    r"C:\Users\Admin\Downloads\phoneinfoga_Windows_x86_64",
)

# ── Known scam prefixes used by fake CBI/ED/Police ───────────────────────────

# Indian mobile number prefixes frequently reported as scam/fake-authority calls
SCAM_PREFIXES = {
    # Virtual/cloud telephony often abused for scams
    "7000", "7001", "7002", "7003", "7004", "7005",
    "6000", "6001", "6002", "6003",
    # Frequently reported fake CBI / ED patterns in news
    "9310", "9311", "9312", "9313", "9314",  # Delhi-routed spoofed
}

# VoIP service provider prefixes in India (higher scam risk)
VOIP_PREFIXES = {
    "7400", "7401", "7402", "7403", "7404", "7405",
    "7406", "7407", "7408", "7409",
    "9600", "9601", "9602", "9603",
}

# Indian landline city codes (STD codes) that get spoofed
SPOOFED_STD_CODES = {
    "011": "Delhi", "022": "Mumbai", "033": "Kolkata", "044": "Chennai",
    "080": "Bangalore", "040": "Hyderabad", "079": "Ahmedabad",
}

# Premium / International format scam signals
INTERNATIONAL_SCAM_CODES = {
    "+92": "Pakistan (often spoofed for scam calls)",
    "+1": "USA/Canada (used for OTP bypass and tech support scams)",
    "+44": "UK (often spoofed for lottery/prize scams)",
    "+256": "Uganda (common in lottery scams)",
    "+254": "Kenya (common in lottery scams)",
}


# ── Phone number normalization ────────────────────────────────────────────────

def _normalize_phone(phone: str) -> tuple[str, str, str]:
    """Normalize Indian phone number to multiple formats.

    Args:
        phone: Raw phone string in any format.

    Returns:
        (e164, national, digits_only)
        e164: +91XXXXXXXXXX
        national: 0XXXXXXXXXX
        digits_only: 10-digit number
    """
    # Strip all non-digit characters except leading +
    cleaned = re.sub(r"[^\d+]", "", phone.strip())

    # Handle + prefix
    if cleaned.startswith("+91"):
        digits = cleaned[3:]
    elif cleaned.startswith("91") and len(cleaned) == 12:
        digits = cleaned[2:]
    elif cleaned.startswith("0") and len(cleaned) == 11:
        digits = cleaned[1:]
    elif len(cleaned) == 10 and cleaned[0] in "6789":
        digits = cleaned
    else:
        # Return as-is for non-Indian numbers
        digits = cleaned.lstrip("+91").lstrip("0")

    # Validate 10-digit Indian mobile
    if len(digits) == 10 and digits[0] in "6789":
        return f"+91{digits}", f"0{digits}", digits

    # For non-standard lengths, best-effort
    return f"+{cleaned.lstrip('+')}", cleaned, cleaned


# ── Check 1: TrueCaller RapidAPI ─────────────────────────────────────────────

def _check_truecaller(phone_e164: str) -> dict:
    """Query TrueCaller API via RapidAPI.

    Returns:
        {checked, name, spam_score, is_spam, tags, error}
    """
    api_key = os.getenv("TRUECALLER_API_KEY", TRUECALLER_API_KEY)
    if not api_key:
        return {"checked": False, "name": None, "spam_score": 0, "is_spam": False, "tags": [], "error": "No TrueCaller API key"}

    try:
        headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": TRUECALLER_API_HOST,
        }
        params = {"phone": phone_e164}
        resp = requests.get(
            f"https://{TRUECALLER_API_HOST}/api/v1/getDetails",
            headers=headers,
            params=params,
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()

        # TrueCaller API response parsing
        # The response structure varies by version; handle both formats
        if isinstance(data, dict):
            name = (
                data.get("name")
                or data.get("displayName")
                or data.get("data", {}).get("name")
                or None
            )
            spam_score = int(
                data.get("spamScore")
                or data.get("spam_score")
                or data.get("data", {}).get("spamScore")
                or 0
            )
            is_spam = bool(
                data.get("isSpam")
                or data.get("is_spam")
                or data.get("data", {}).get("isSpam")
                or spam_score > 50
            )
            tags = data.get("tags") or data.get("data", {}).get("tags") or []
            return {
                "checked": True,
                "name": name,
                "spam_score": spam_score,
                "is_spam": is_spam,
                "tags": tags if isinstance(tags, list) else [],
                "error": None,
            }
        return {"checked": False, "name": None, "spam_score": 0, "is_spam": False, "tags": [], "error": "Unexpected response format"}
    except Exception as e:
        logger.warning("TrueCaller API failed for %s: %s", phone_e164, e)
        return {"checked": False, "name": None, "spam_score": 0, "is_spam": False, "tags": [], "error": str(e)}


# ── Check 2: NumVerify API ────────────────────────────────────────────────────

def _check_numverify(phone_digits: str, country_code: str = "IN") -> dict:
    """Validate phone number via NumVerify API.

    Returns:
        {checked, valid, carrier, line_type, country_name, is_voip, formatted, error}
    """
    api_key = os.getenv("NUMVERIFY_API_KEY", NUMVERIFY_API_KEY)
    if not api_key:
        return {"checked": False, "valid": None, "carrier": None, "line_type": None,
                "country_name": None, "is_voip": False, "formatted": None, "error": "No NumVerify API key"}

    try:
        resp = requests.get(
            "http://apilayer.net/api/validate",
            params={
                "access_key": api_key,
                "number": phone_digits,
                "country_code": country_code,
            },
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()

        if not data.get("valid", True) and data.get("error"):
            return {
                "checked": False, "valid": False, "carrier": None, "line_type": None,
                "country_name": None, "is_voip": False, "formatted": None,
                "error": data.get("error", {}).get("info", "NumVerify error"),
            }

        line_type = data.get("line_type", "")
        is_voip = line_type.lower() in ("voip", "virtual", "pager") if line_type else False

        return {
            "checked": True,
            "valid": data.get("valid", False),
            "carrier": data.get("carrier"),
            "line_type": line_type,
            "country_name": data.get("country_name"),
            "is_voip": is_voip,
            "formatted": data.get("international_format"),
            "error": None,
        }
    except Exception as e:
        logger.warning("NumVerify API failed for %s: %s", phone_digits, e)
        return {"checked": False, "valid": None, "carrier": None, "line_type": None,
                "country_name": None, "is_voip": False, "formatted": None, "error": str(e)}


# ── Check 3: PhoneInfoga ──────────────────────────────────────────────────────

def _check_phoneinfoga(phone_e164: str) -> dict:
    """Run PhoneInfoga OSINT scan as subprocess.

    Returns:
        {checked, osint_data: dict, error: str|None}
    """
    binary = Path(os.getenv("PHONEINFOGA_PATH", PHONEINFOGA_PATH))
    if not binary.exists():
        return {"checked": False, "osint_data": {}, "error": f"PhoneInfoga binary not found at {binary}"}

    try:
        result = subprocess.run(
            [str(binary), "scan", "-n", phone_e164, "--output", "json"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        stdout = result.stdout.strip()
        if not stdout:
            return {"checked": True, "osint_data": {}, "error": result.stderr[:200] if result.stderr else None}

        # Try to parse JSON output
        try:
            data = json.loads(stdout)
        except json.JSONDecodeError:
            # PhoneInfoga may output multiple JSON objects or mixed text
            json_matches = re.findall(r"\{[^{}]+\}", stdout, re.DOTALL)
            data = {}
            for match in json_matches:
                try:
                    data.update(json.loads(match))
                except json.JSONDecodeError:
                    pass

        return {"checked": True, "osint_data": data, "error": None}
    except subprocess.TimeoutExpired:
        return {"checked": False, "osint_data": {}, "error": "PhoneInfoga scan timed out after 30s"}
    except Exception as e:
        logger.warning("PhoneInfoga scan failed for %s: %s", phone_e164, e)
        return {"checked": False, "osint_data": {}, "error": str(e)}


# ── Check 4 & 5: Pattern analysis ────────────────────────────────────────────

def _check_patterns(phone_digits: str, phone_e164: str) -> dict:
    """Analyze phone number patterns for known scam indicators.

    Returns:
        {is_suspicious, flags, prefix_type, intl_warning}
    """
    flags: list[str] = []
    is_suspicious = False
    prefix_type = "standard"
    intl_warning = None

    if len(phone_digits) == 10:
        prefix_4 = phone_digits[:4]
        prefix_2 = phone_digits[:2]

        # Check scam prefixes
        if prefix_4 in SCAM_PREFIXES:
            is_suspicious = True
            flags.append(f"Number prefix '{prefix_4}' is associated with reported scam calls")

        # Check VoIP prefixes
        if prefix_4 in VOIP_PREFIXES:
            is_suspicious = True
            prefix_type = "voip"
            flags.append(f"Number appears to use VoIP service (prefix {prefix_4}) — commonly used for spoofed scam calls")

        # Fake government authority numbers often have sequential patterns
        if len(set(phone_digits)) <= 3:
            flags.append("Number has very low digit diversity (possible test/fake number)")

        # Repeated digit patterns (fake numbers)
        if re.match(r"(.)\1{4,}", phone_digits):
            is_suspicious = True
            flags.append("Number contains long repeated digit sequences — likely fake")

        # Numbers starting with 1 or 2 are not valid Indian mobile numbers
        if phone_digits[0] in "012345":
            flags.append(f"Indian mobile numbers must start with 6-9, not '{phone_digits[0]}'")
            is_suspicious = True

    # International number checks
    for country_code, description in INTERNATIONAL_SCAM_CODES.items():
        if phone_e164.startswith(country_code) and country_code != "+91":
            intl_warning = description
            flags.append(f"International number ({country_code}) — {description}")

    # Spoofed landline check (+91 followed by 2-digit city code)
    if phone_e164.startswith("+91") and len(phone_e164) >= 5:
        potential_std = phone_e164[3:6]
        for code, city in SPOOFED_STD_CODES.items():
            if potential_std.startswith(code[:2]):
                flags.append(f"Number may be routing via {city} landline exchange — verify caller identity")

    return {
        "is_suspicious": is_suspicious,
        "flags": flags,
        "prefix_type": prefix_type,
        "intl_warning": intl_warning,
    }


# ── Risk score aggregation ────────────────────────────────────────────────────

def _calculate_risk(
    tc: dict,
    nv: dict,
    patterns: dict,
) -> tuple[int, str]:
    """Aggregate check results into a final risk score."""
    score = 0

    # TrueCaller spam score (0-100 scale)
    if tc.get("checked"):
        spam_score = tc.get("spam_score", 0)
        if tc.get("is_spam"):
            score += max(40, spam_score // 2)
        elif spam_score > 0:
            score += spam_score // 4

    # VoIP line type adds moderate risk
    if nv.get("is_voip"):
        score += 25

    # Pattern flags
    if patterns.get("is_suspicious"):
        score += 30

    # Each flag adds a bit
    score += min(len(patterns.get("flags", [])) * 5, 20)

    score = min(score, 100)

    if score >= 65:
        verdict = "SCAM"
    elif score >= 30:
        verdict = "SUSPICIOUS"
    else:
        verdict = "SAFE"

    return score, verdict


# ── Public API ────────────────────────────────────────────────────────────────

def analyze_phone(phone: str) -> dict:
    """Analyze a phone number for spam, scam, and intelligence data.

    Args:
        phone: Phone number in any format (e.g., "+91 98765 43210", "9876543210", "09876543210").

    Returns:
        dict with keys:
            verdict, risk_score, phone, formatted, carrier, country,
            is_voip, spam_reports, spam_score, truecaller_name, is_suspicious,
            red_flags, checks_performed
    """
    if not phone or not phone.strip():
        raise ValueError("Phone number cannot be empty.")

    phone = phone.strip()
    e164, national, digits = _normalize_phone(phone)

    # Determine country code for NumVerify
    if e164.startswith("+91"):
        country_code = "IN"
    else:
        country_code = ""

    checks_performed: list[str] = ["normalization"]

    # Check 1: TrueCaller
    tc = _check_truecaller(e164)
    if tc.get("checked"):
        checks_performed.append("truecaller")

    # Check 2: NumVerify
    nv = _check_numverify(digits if country_code == "IN" else e164.lstrip("+"), country_code)
    if nv.get("checked"):
        checks_performed.append("numverify")

    # Check 3: PhoneInfoga
    pif = _check_phoneinfoga(e164)
    if pif.get("checked"):
        checks_performed.append("phoneinfoga")

    # Checks 4 & 5: Pattern analysis
    patterns = _check_patterns(digits, e164)
    checks_performed.append("pattern_analysis")

    # Combine is_voip from numverify
    is_voip = nv.get("is_voip", False) or patterns.get("prefix_type") == "voip"

    # Risk calculation
    risk_score, verdict = _calculate_risk(tc, nv, patterns)

    # Compile red flags
    red_flags: list[str] = list(patterns.get("flags", []))
    if tc.get("is_spam"):
        red_flags.insert(0, f"TrueCaller identified this number as SPAM (score: {tc.get('spam_score', 0)})")
    if is_voip:
        red_flags.append("VoIP/virtual number — can be easily spoofed or reassigned")
    if not nv.get("valid") and nv.get("checked"):
        red_flags.append("NumVerify: number is invalid or unallocated")

    return {
        "verdict": verdict,
        "risk_score": risk_score,
        "phone": phone,
        "formatted": e164,
        "national": national,
        "carrier": nv.get("carrier"),
        "country": nv.get("country_name") or ("India" if e164.startswith("+91") else None),
        "is_voip": is_voip,
        "spam_score": tc.get("spam_score", 0),
        "spam_reports": tc.get("is_spam", False),
        "truecaller_name": tc.get("name"),
        "truecaller_tags": tc.get("tags", []),
        "is_suspicious": patterns.get("is_suspicious", False) or tc.get("is_spam", False),
        "red_flags": red_flags,
        "checks_performed": checks_performed,
        "truecaller": {
            "checked": tc.get("checked", False),
            "name": tc.get("name"),
            "spam_score": tc.get("spam_score", 0),
            "is_spam": tc.get("is_spam", False),
        },
        "numverify": {
            "checked": nv.get("checked", False),
            "valid": nv.get("valid"),
            "carrier": nv.get("carrier"),
            "line_type": nv.get("line_type"),
        },
        "phoneinfoga": {
            "checked": pif.get("checked", False),
            "osint_summary": pif.get("osint_data", {}),
        },
        "pattern_analysis": {
            "prefix_type": patterns.get("prefix_type", "standard"),
            "intl_warning": patterns.get("intl_warning"),
        },
    }
