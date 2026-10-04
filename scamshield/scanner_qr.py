"""ScamShield — QR code decoder and analyzer.

Decodes QR codes from images using pyzbar and routes the decoded value
through the appropriate scanner (URL, phone, or UPI analysis).

Usage:
    from scamshield.scanner_qr import analyze_qr

    with open("qr.png", "rb") as f:
        result = analyze_qr(f.read())
"""

from __future__ import annotations

import io
import logging
import re
from urllib.parse import parse_qs, urlparse

logger = logging.getLogger(__name__)

# ── Optional imports ──────────────────────────────────────────────────────────

try:
    from pyzbar.pyzbar import decode as pyzbar_decode  # type: ignore
    PYZBAR_AVAILABLE = True
except ImportError:
    PYZBAR_AVAILABLE = False
    logger.warning("pyzbar not installed — QR decoding disabled. Install with: pip install pyzbar")

try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    logger.warning("Pillow not installed — QR decoding disabled. Install with: pip install Pillow")


# ── Known fake merchant UPI patterns ─────────────────────────────────────────

FAKE_MERCHANT_PATTERNS = re.compile(
    r"(pm[0-9]{5,}@|paytm[0-9]{4,}@|cashback@|refund@|lottery@|prize@|"
    r"govt@|cbi@|income.?tax@|trai@|uidai@|rbi@|police@|customs@|"
    r"doublemoney@|multiplier@|invest@|earn@|profit@|kyc@|verify@|"
    r"support@|helpdesk@|customer.?care@|claim@|winning@)",
    re.IGNORECASE,
)

# Valid UPI VPAs follow pattern: [identifier]@[bank/provider]
VALID_UPI_PROVIDERS = {
    "upi", "oksbi", "okaxis", "okicici", "okhdfcbank", "ybl", "ibl",
    "axl", "sbi", "hdfcbank", "icici", "axis", "kotak", "paytm",
    "paytmbank", "freecharge", "airtelpaymentsbank", "juspay", "razorpay",
    "googl", "gpay", "phonepe", "bhim", "apl", "allbank", "aubank",
    "barodampay", "cbi", "centralbank", "dbs", "dlb", "equitas",
    "esaf", "federal", "fincare", "idbi", "idfc", "idfcbank", "indus",
    "iob", "jkb", "karb", "lvb", "mahb", "nsdl", "payzapp", "pnb",
    "psb", "rbl", "saraswat", "sib", "syndbank", "tjsb", "ubi",
    "unionbank", "utbi", "vijb", "yesbank",
}


# ── UPI payment string parser ────────────────────────────────────────────────

def _parse_upi(upi_str: str) -> dict:
    """Parse a UPI payment URL or VPA string.

    Handles:
    - upi://pay?pa=merchant@bank&pn=Name&am=100&tn=Reason
    - merchant@bank (bare VPA)

    Returns:
        {vpa, name, amount, transaction_note, provider, is_personal_number_vpa}
    """
    vpa = None
    name = None
    amount = None
    note = None
    provider = None

    if upi_str.lower().startswith("upi://"):
        parsed = urlparse(upi_str)
        params = parse_qs(parsed.query)
        vpa = (params.get("pa") or params.get("PA") or [None])[0]
        name = (params.get("pn") or params.get("PN") or [None])[0]
        amount = (params.get("am") or params.get("AM") or [None])[0]
        note = (params.get("tn") or params.get("TN") or [None])[0]
    else:
        vpa = upi_str.strip()

    # Extract provider from VPA
    if vpa and "@" in vpa:
        parts = vpa.split("@", 1)
        identifier = parts[0]
        provider = parts[1].lower() if len(parts) > 1 else None

        # Detect personal number VPA (9XXXXXXXXX@upi) — very suspicious in QR
        is_personal_number_vpa = bool(
            re.match(r"^[6-9]\d{9}$", identifier)
        )
    else:
        identifier = vpa or ""
        is_personal_number_vpa = False

    return {
        "vpa": vpa,
        "name": name,
        "amount": amount,
        "transaction_note": note,
        "provider": provider,
        "identifier": identifier,
        "is_personal_number_vpa": is_personal_number_vpa,
    }


def _analyze_upi(upi_str: str) -> dict:
    """Analyze a UPI payment string for scam indicators.

    Returns:
        {upi_info, verdict, risk_score, red_flags, summary}
    """
    upi_info = _parse_upi(upi_str)
    red_flags: list[str] = []
    risk_score = 0

    vpa = upi_info.get("vpa", "") or ""
    provider = upi_info.get("provider", "") or ""
    is_personal = upi_info.get("is_personal_number_vpa", False)

    # Personal mobile number as VPA (9876543210@upi) in QR context is always suspicious
    # Legitimate businesses have merchant VPAs like businessname@hdfcbank
    if is_personal:
        risk_score += 50
        red_flags.append(
            "QR code points to a personal mobile number UPI VPA — "
            "scanning QR codes to RECEIVE money is a known scam tactic. "
            "You NEVER need to scan a QR code to receive payment."
        )

    # Fake/suspicious merchant VPA patterns
    if FAKE_MERCHANT_PATTERNS.search(vpa):
        risk_score += 40
        red_flags.append(f"UPI VPA '{vpa}' matches known fake/suspicious merchant patterns")

    # Unknown or suspicious UPI provider
    if provider and provider not in VALID_UPI_PROVIDERS:
        risk_score += 20
        red_flags.append(f"UPI provider '@{provider}' is not a recognized Indian bank/payment app")

    # QR codes for receiving payment — fundamental scam rule
    red_flags.append(
        "GOLDEN RULE: Scan QR codes ONLY to MAKE payments. "
        "If someone says 'scan this QR to RECEIVE money', it is a SCAM — "
        "scanning always deducts from YOUR account."
    )

    # Large amount in QR
    if upi_info.get("amount"):
        try:
            amount_val = float(upi_info["amount"])
            if amount_val > 50000:
                risk_score += 20
                red_flags.append(f"QR encodes a high payment amount (₹{amount_val:,.2f}) — verify before scanning")
        except (ValueError, TypeError):
            pass

    # Zero amount could be collect scam
    if upi_info.get("amount") == "0" or upi_info.get("amount") == "0.0":
        risk_score += 15
        red_flags.append("QR code has ₹0 amount — could be used to authorize future debits")

    risk_score = min(risk_score, 100)

    if risk_score >= 65:
        verdict = "SCAM"
    elif risk_score >= 30:
        verdict = "SUSPICIOUS"
    else:
        verdict = "SAFE"

    return {
        "upi_info": upi_info,
        "verdict": verdict,
        "risk_score": risk_score,
        "red_flags": red_flags,
        "summary": (
            f"UPI payment to '{vpa}'" +
            (f" (Amount: ₹{upi_info['amount']})" if upi_info.get("amount") else "") +
            (f" by {upi_info['name']}" if upi_info.get("name") else "")
        ),
    }


# ── QR type detection ─────────────────────────────────────────────────────────

def _detect_qr_type(decoded_value: str) -> str:
    """Detect the type of QR code content.

    Returns:
        One of: 'upi', 'url', 'phone', 'text', 'email', 'wifi', 'contact'
    """
    v = decoded_value.strip()

    if v.lower().startswith("upi://") or re.match(r"^[a-zA-Z0-9._+-]+@[a-zA-Z0-9]+$", v):
        return "upi"

    if re.match(r"^https?://", v, re.IGNORECASE):
        return "url"

    if re.match(r"^(tel:|callto:)", v, re.IGNORECASE):
        return "phone"

    if re.match(r"^(mailto:)", v, re.IGNORECASE):
        return "email"

    if re.match(r"^wifi:", v, re.IGNORECASE):
        return "wifi"

    if re.match(r"^begin:vcard", v, re.IGNORECASE):
        return "contact"

    if re.match(r"^\+?[0-9\s\-()]{8,15}$", v):
        return "phone"

    return "text"


# ── Main decoder ──────────────────────────────────────────────────────────────

def _decode_qr(image_bytes: bytes) -> list[str]:
    """Decode all QR codes from image bytes.

    Returns:
        List of decoded string values.
    """
    if not PYZBAR_AVAILABLE:
        raise RuntimeError("pyzbar is not installed. Install with: pip install pyzbar")
    if not PILLOW_AVAILABLE:
        raise RuntimeError("Pillow is not installed. Install with: pip install Pillow")

    img = Image.open(io.BytesIO(image_bytes))
    # Convert to RGB for consistent processing
    if img.mode not in ("RGB", "L", "RGBA"):
        img = img.convert("RGB")

    decoded_objects = pyzbar_decode(img)
    results = []
    for obj in decoded_objects:
        try:
            data = obj.data.decode("utf-8")
            results.append(data)
        except UnicodeDecodeError:
            try:
                data = obj.data.decode("latin-1")
                results.append(data)
            except Exception:
                pass

    return results


# ── Public API ────────────────────────────────────────────────────────────────

def analyze_qr(image_bytes: bytes) -> dict:
    """Decode and analyze a QR code image for scam content.

    Args:
        image_bytes: Raw bytes of an image file containing a QR code.

    Returns:
        dict with keys:
            decoded_type, decoded_value, verdict, risk_score,
            url_scan, upi_scan, phone_scan, summary, red_flags
    """
    if not image_bytes:
        raise ValueError("Image bytes cannot be empty.")

    # Attempt QR decode
    if not PYZBAR_AVAILABLE or not PILLOW_AVAILABLE:
        return {
            "decoded_type": None,
            "decoded_value": None,
            "verdict": "SUSPICIOUS",
            "risk_score": 0,
            "url_scan": None,
            "upi_scan": None,
            "phone_scan": None,
            "summary": "QR decoding libraries (pyzbar/Pillow) are not installed on the server.",
            "red_flags": ["QR scanning unavailable — install pyzbar and Pillow"],
            "error": "pyzbar or Pillow not installed",
        }

    try:
        decoded_values = _decode_qr(image_bytes)
    except Exception as e:
        return {
            "decoded_type": None,
            "decoded_value": None,
            "verdict": "SUSPICIOUS",
            "risk_score": 0,
            "url_scan": None,
            "upi_scan": None,
            "phone_scan": None,
            "summary": f"Could not decode QR code: {e}",
            "red_flags": [f"QR decode error: {e}"],
        }

    if not decoded_values:
        return {
            "decoded_type": None,
            "decoded_value": None,
            "verdict": "SUSPICIOUS",
            "risk_score": 0,
            "url_scan": None,
            "upi_scan": None,
            "phone_scan": None,
            "summary": "No QR code found in the image.",
            "red_flags": ["No QR code detected in the provided image"],
        }

    # Analyze the first QR code found (primary)
    decoded_value = decoded_values[0]
    qr_type = _detect_qr_type(decoded_value)

    url_scan = None
    upi_scan = None
    phone_scan = None
    verdict = "SAFE"
    risk_score = 0
    red_flags: list[str] = []
    summary = f"QR code decoded: {qr_type.upper()} — {decoded_value[:100]}"

    if qr_type == "upi":
        upi_result = _analyze_upi(decoded_value)
        upi_scan = upi_result
        verdict = upi_result["verdict"]
        risk_score = upi_result["risk_score"]
        red_flags = upi_result["red_flags"]
        summary = upi_result["summary"]

    elif qr_type == "url":
        try:
            from .scanner_url import analyze_url
            url_result = analyze_url(decoded_value)
            url_scan = url_result
            verdict = url_result.get("verdict", "SUSPICIOUS")
            risk_score = url_result.get("risk_score", 50)
            red_flags = url_result.get("red_flags", [])
            summary = f"QR code links to URL: {decoded_value[:80]}"
            red_flags.append("QR code contains a URL — verify the destination before visiting")
        except Exception as e:
            logger.warning("URL scan from QR failed: %s", e)
            verdict = "SUSPICIOUS"
            risk_score = 40
            red_flags = [f"QR URL analysis failed: {e}", "Verify URL manually before visiting"]
            summary = f"QR code links to URL: {decoded_value[:80]}"

    elif qr_type == "phone":
        phone_str = re.sub(r"^(tel:|callto:)", "", decoded_value, flags=re.IGNORECASE)
        try:
            from .scanner_phone import analyze_phone
            phone_result = analyze_phone(phone_str)
            phone_scan = phone_result
            verdict = phone_result.get("verdict", "SUSPICIOUS")
            risk_score = phone_result.get("risk_score", 0)
            red_flags = phone_result.get("red_flags", [])
            summary = f"QR code encodes phone number: {phone_str}"
        except Exception as e:
            logger.warning("Phone scan from QR failed: %s", e)
            verdict = "SUSPICIOUS"
            risk_score = 30
            red_flags = [f"Phone analysis failed: {e}"]
            summary = f"QR code contains phone number: {phone_str}"

    elif qr_type == "wifi":
        # WiFi QR codes can be used for MITM attacks
        verdict = "SUSPICIOUS"
        risk_score = 25
        red_flags = [
            "QR code connects to a WiFi network — verify this is a trusted network before connecting",
            "Connecting to unknown WiFi can expose your traffic to man-in-the-middle attacks",
        ]
        summary = f"QR code contains WiFi credentials: {decoded_value[:60]}"

    else:
        # Plain text QR
        verdict = "SAFE"
        risk_score = 5
        summary = f"QR code contains text: {decoded_value[:100]}"

    # Check for multiple QR codes
    if len(decoded_values) > 1:
        red_flags.append(f"Image contains {len(decoded_values)} QR codes — analyzed primary only")

    return {
        "decoded_type": qr_type,
        "decoded_value": decoded_value,
        "all_decoded": decoded_values,
        "verdict": verdict,
        "risk_score": risk_score,
        "url_scan": url_scan,
        "upi_scan": upi_scan,
        "phone_scan": phone_scan,
        "summary": summary,
        "red_flags": red_flags,
    }
