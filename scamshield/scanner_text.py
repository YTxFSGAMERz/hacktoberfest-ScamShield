"""ScamShield — SMS / WhatsApp text-message scam analyzer.

Analyzes raw text (pasted SMS, WhatsApp messages, emails) for scam patterns
using Gemma 4 text mode (no vision) via the Gemini REST API.

Usage:
    from scamshield.scanner_text import analyze_text

    result, provider = analyze_text("Dear customer your KYC is expired...", lang="hi")
"""

from __future__ import annotations

import json
import logging
import os
import re

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemma-4-26b-a4b-it")

# ── Detailed system prompt for text-based scam detection ─────────────────────

TEXT_SCAM_SYSTEM_PROMPT = """You are ScamShield's Text Fraud Analyst — an expert AI trained exclusively on Indian cyber-crime patterns, RBI advisories, I4C bulletins, and South Asian financial fraud typologies.

Your task is to meticulously analyze a pasted SMS, WhatsApp message, email, or chat snippet and determine if it is a SCAM, SUSPICIOUS, or SAFE communication.

## YOUR ANALYSIS FRAMEWORK

### Step 1 — Identity & Attribution
- Who is the claimed sender? (bank, government, courier, employer, family)
- Is the sender ID or number format consistent with legitimate organizations?
- Indian banks use 6-character alphanumeric DLT sender IDs (e.g., VM-HDFCBK, AD-SBIPHO). A genuine bank never sends from a personal 10-digit mobile number.
- Government bodies (IT Dept, CBI, ED, TRAI, Customs) NEVER communicate financial/legal demands via WhatsApp or SMS.

### Step 2 — Urgency & Psychological Pressure Analysis
Watch for these high-signal urgency triggers:
- "आज रात" / "tonight" / "2 hours" / "immediately" / "अभी"
- "अकाउंट ब्लॉक" / "account blocked" / "suspended" / "frozen"
- "arrest" / "FIR" / "legal action" / "cyber police" / "ED raid"
- "last chance" / "final warning" / "don't ignore"
- "verify now" / "click link" / "call immediately"

### Step 3 — Financial Hook Identification
- UPI PIN requests: "Enter PIN to receive" → ALWAYS A SCAM. You never enter PIN to receive money.
- Advance fee: "Pay ₹500 processing fee to claim ₹10 lakh prize"
- Investment bait: "Guaranteed 5% daily return" / "crypto multiplier"
- Collect request: "Click link to get refund/cashback"
- OTP fishing: "Share the OTP received on your number with us"

### Step 4 — Link & Domain Analysis
- Suspicious TLDs: .xyz, .tk, .ml, .ga, .cf, .click, .top
- Homoglyph attacks: sb1-kyc.com (digit 1 vs letter l), hdfc-upI.com (capital I vs l)
- URL shorteners in financial messages: bit.ly, tinyurl, cutt.ly, is.gd → never used by real banks
- Legitimate domains: sbi.co.in, hdfcbank.com, icicibank.com, npci.org.in, incometax.gov.in

### Step 5 — Known Indian Scam Taxonomy
Match against these high-prevalence scam patterns:
1. **KYC / Account Verification Scam** — "Your KYC is expired, account will be blocked"
2. **Digital Arrest / Police Impersonation** — "CBI/ED ke naam par video call"
3. **Electricity Bill Disconnection** — "Aaj raat bijli kategi, call karein"
4. **Lottery / Lucky Draw** — "You won ₹X lakh in BPCL/KBC lottery"
5. **Part-Time Job / Task Fraud** — "Like YouTube videos, earn ₹5,000/day"
6. **UPI Collect Request Fraud** — "Click link to receive cashback"
7. **FedEx / Courier Narcotics Parcel** — "Your parcel contains drugs, press 1"
8. **Instant Loan APK Malware** — "Get ₹50,000 loan in 10 minutes, download this app"
9. **Fake Insurance / Policy** — "Your policy will lapse, pay now to continue"
10. **Investment / Trading Scam** — "Join our Telegram for guaranteed stock tips"
11. **SIM Swap Fraud** — "Your SIM will expire, update immediately"
12. **Romance / Honeytrap** — Emotional manipulation leading to money requests
13. **OLX / Marketplace Scam** — Fake buyer/seller requesting advance payment
14. **Bank Impersonation** — Fake customer care number, "verify your account"
15. **QR Code Trap** — "Scan this QR code to receive payment" (scanning deducts)
16. **Deepfake / Video KYC Scam** — AI-generated video calls impersonating officials

### Step 6 — Language-Aware Red Flags (Hindi/Hinglish/Regional)
These Hindi/Hinglish phrases are HIGH-RISK indicators:
- "PIN daalkar paisa prapt karein" (Enter PIN to receive money — IMPOSSIBLE)
- "Aapka account band ho jayega" (Your account will be blocked)
- "Ghar baithe kamayein" (Earn from home)
- "Guaranteed return" / "Paisa double"
- "OTP share karein" (Share OTP — NEVER do this)
- "APK download karein" (Download APK — from WhatsApp, NEVER)
- "Digital arrest" / "Online FIR"

## SAFE INDICATORS (reduce suspicion)
- TRAI-registered 6-char sender ID (VM-, AD-, BZ-, JK- prefixes)
- Bank transaction alert with masked account (XXXXXXX1234)
- OTP message with "Do not share this OTP" clause
- Delivery tracking from official domain
- No link or only official domain link
- Standard bank debit/credit alerts with merchant name

## OUTPUT FORMAT
You MUST respond with ONLY a valid JSON object. No markdown, no explanation, no preamble.

{
  "verdict": "SCAM" | "SUSPICIOUS" | "SAFE",
  "risk_score": <integer 0-100>,
  "confidence": "LOW" | "MEDIUM" | "HIGH",
  "scam_type": "<specific scam category or 'Legitimate Communication'>",
  "summary": "<2-3 sentence explanation in the requested language>",
  "red_flags": ["<flag 1>", "<flag 2>", ...],
  "advice": "<clear, actionable advice in the requested language>"
}

Risk score guide:
- 0-20: SAFE (genuine communication)
- 21-49: SUSPICIOUS (proceed with caution)
- 50-79: SCAM (high probability)
- 80-100: SCAM (near-certain fraud)

Be decisive. A false negative (missing a scam) is more dangerous than a false positive.
"""

# ── Language code to name mapping ────────────────────────────────────────────

LANGUAGE_NAMES = {
    "en": "English", "hi": "हिंदी (Hindi)", "gu": "ગુજરાતી (Gujarati)",
    "bn": "বাংলা (Bengali)", "ta": "தமிழ் (Tamil)", "te": "తెలుగు (Telugu)",
    "mr": "मराठी (Marathi)", "kn": "ಕನ್ನಡ (Kannada)", "ml": "മലയാളം (Malayalam)",
    "pa": "ਪੰਜਾਬੀ (Punjabi)", "or": "ଓଡ଼ିଆ (Odia)", "as": "অসমীয়া (Assamese)",
    "ur": "اردو (Urdu)", "sd": "سنڌي (Sindhi)", "ne": "नेपाली (Nepali)",
    "si": "සිංහල (Sinhala)", "my": "မြန်မာဘာသာ (Burmese)",
    "th": "ภาษาไทย (Thai)", "vi": "Tiếng Việt (Vietnamese)",
    "id": "Bahasa Indonesia", "ms": "Bahasa Melayu (Malay)",
    "tl": "Filipino (Tagalog)", "zh": "中文 (Chinese)", "ja": "日本語 (Japanese)",
    "ko": "한국어 (Korean)", "ar": "العربية (Arabic)", "fa": "فارسی (Persian)",
    "tr": "Türkçe (Turkish)", "ru": "Русский (Russian)", "de": "Deutsch (German)",
    "fr": "Français (French)", "es": "Español (Spanish)", "pt": "Português (Portuguese)",
    "it": "Italiano (Italian)", "nl": "Nederlands (Dutch)", "pl": "Polski (Polish)",
    "sv": "Svenska (Swedish)", "da": "Dansk (Danish)", "fi": "Suomi (Finnish)",
    "no": "Norsk (Norwegian)", "cs": "Čeština (Czech)", "sk": "Slovenčina (Slovak)",
    "hu": "Magyar (Hungarian)", "ro": "Română (Romanian)", "bg": "Български (Bulgarian)",
    "hr": "Hrvatski (Croatian)", "sr": "Српски (Serbian)", "uk": "Українська (Ukrainian)",
    "el": "Ελληνικά (Greek)", "he": "עברית (Hebrew)", "lt": "Lietuvių (Lithuanian)",
    "lv": "Latviešu (Latvian)", "et": "Eesti (Estonian)", "sl": "Slovenščina (Slovenian)",
    "ga": "Gaeilge (Irish)", "cy": "Cymraeg (Welsh)", "eu": "Euskara (Basque)",
    "ca": "Català (Catalan)", "gl": "Galego (Galician)", "lb": "Lëtzebuergesch (Luxembourgish)",
    "mt": "Malti (Maltese)", "is": "Íslenska (Icelandic)", "mk": "Македонски (Macedonian)",
    "sq": "Shqip (Albanian)", "hy": "Հայերեն (Armenian)", "ka": "ქართული (Georgian)",
    "az": "Azərbaycan (Azerbaijani)", "kk": "Қазақша (Kazakh)", "uz": "Oʻzbekcha (Uzbek)",
    "tk": "Türkmençe (Turkmen)", "ky": "Кыргызча (Kyrgyz)", "tg": "Тоҷикӣ (Tajik)",
    "mn": "Монгол (Mongolian)", "lo": "ລາວ (Lao)", "km": "ខ្មែរ (Khmer)",
    "sw": "Kiswahili (Swahili)", "am": "አማርኛ (Amharic)", "ha": "Hausa",
    "yo": "Yorùbá", "ig": "Igbo", "zu": "isiZulu", "xh": "isiXhosa",
    "af": "Afrikaans", "so": "Soomaali (Somali)",
}

# ── Pre-filter: urgency/scam keyword patterns ────────────────────────────────

_URGENCY_PATTERNS = [
    # English
    r"\b(urgent|immediately|verify now|otp|pin|suspend|block|arrest|lottery|prize|won|click here|download apk|earn from home|guaranteed return|refund|cashback|kyc expired)\b",
    # Hindi/Hinglish
    r"(pin|पिन|ओटीपी|otp|तुरंत|अभी|खाता बंद|account band|bijli kategi|बिजली|kyc|केवाईसी|गिरफ्तार|digital arrest|लॉटरी|पुरस्कार|डाउनलोड|apk|कमाएं|guaranteed)",
    # Gujarati
    r"(પિન|ઓટીપી|તાત્કાલ|ખાતું|KYC|લોટરી|ઇનામ|APK|ડાઉનલોડ|ગેરન્ટી)",
    # Generic financial scam signals
    r"(bit\.ly|tinyurl|is\.gd|cutt\.ly|t\.co|shorturl|\.xyz|\.tk|\.ml|\.ga|\.cf)",
    r"(anydesk|teamviewer|rustdesk|quicksupport|remote)",
    r"(9[0-9]{9}|8[0-9]{9}|7[0-9]{9}|6[0-9]{9})",  # Indian mobile numbers
]

_URGENCY_RE = [re.compile(p, re.IGNORECASE) for p in _URGENCY_PATTERNS]


def _pre_filter(text: str) -> dict:
    """Quick pattern-based pre-scan before calling the AI.

    Returns a dict with matched_patterns list and a base risk adjustment.
    """
    matched: list[str] = []
    for pattern in _URGENCY_RE:
        found = pattern.findall(text)
        if found:
            matched.extend([str(f) if not isinstance(f, str) else f for f in found[:3]])

    # Specific high-confidence scam signals
    high_risk_signals = []

    # UPI PIN to receive (extremely high signal)
    if re.search(r"(pin|पिन).{0,30}(receive|prapt|pane|मिलेगा|paisa)", text, re.IGNORECASE):
        high_risk_signals.append("UPI PIN requested to receive money — definite scam signal")

    # OTP sharing request
    if re.search(r"(share|batao|बताएं|send).{0,20}(otp|ओटीपी)", text, re.IGNORECASE):
        high_risk_signals.append("OTP sharing request — banking credential theft attempt")

    # Fake lottery/prize with call-to-action
    if re.search(r"(won|जीता|मिला|prize|lottery|लॉटरी).{0,50}(call|click|contact|संपर्क)", text, re.IGNORECASE):
        high_risk_signals.append("Lottery prize with contact request — advance fee scam")

    # APK download link
    if re.search(r"(download|डाउनलोड).{0,30}(\.apk|app|application)", text, re.IGNORECASE):
        high_risk_signals.append("APK download request — likely malware/loan app")

    # Digital arrest keywords
    if re.search(r"(digital arrest|online arrest|video call.{0,20}(police|cbi|ed)|skype.{0,20}(police|cbi))", text, re.IGNORECASE):
        high_risk_signals.append("Digital arrest threat — known police impersonation scam")

    # Electricity disconnection
    if re.search(r"(electricity|bijli|बिजली|power).{0,30}(cut|disconnect|band|बंद)", text, re.IGNORECASE):
        high_risk_signals.append("Electricity disconnection threat — utility impersonation scam")

    return {
        "matched_keywords": list(set(str(m).lower() for m in matched))[:10],
        "high_risk_signals": high_risk_signals,
        "pre_risk_score": min(len(matched) * 5 + len(high_risk_signals) * 15, 90),
    }


# ── Gemini text-only call ────────────────────────────────────────────────────

def _call_gemini_text(text: str, user_prompt: str) -> tuple[str, str]:
    """Call Gemini REST API in text-only mode (no vision).

    Returns:
        (raw_response_text, reasoning_text)
    """
    api_key = os.getenv("GEMINI_API_KEY", GEMINI_API_KEY)
    model = os.getenv("GEMINI_MODEL", GEMINI_MODEL)
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )

    payload = {
        "system_instruction": {
            "parts": [{"text": TEXT_SCAM_SYSTEM_PROMPT}]
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user_prompt}],
            }
        ],
        "generationConfig": {
            "temperature": 0.05,
            "maxOutputTokens": 1024,
        },
    }

    response = requests.post(url, json=payload, timeout=60)
    response.raise_for_status()

    data = response.json()
    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError(f"Gemini returned no candidates: {data}")

    parts = candidates[0].get("content", {}).get("parts", [])
    thought_parts = [p.get("text", "") for p in parts if p.get("thought", False)]
    answer_parts = [p.get("text", "") for p in parts if not p.get("thought", False)]

    answer = "".join(answer_parts) if answer_parts else (parts[-1].get("text", "") if parts else "")
    reasoning = "\n\n".join(thought_parts).strip()
    return answer, reasoning


# ── JSON extraction (mirrors llm.py pattern) ────────────────────────────────

def _extract_json(text: str) -> dict:
    """Extract JSON from LLM response text."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass

    obj_match = re.search(r"\{.*\}", text, re.DOTALL)
    if obj_match:
        try:
            return json.loads(obj_match.group(0))
        except json.JSONDecodeError:
            pass

    logger.warning("Could not parse JSON from text analysis response: %s", text[:200])
    return {
        "verdict": "SUSPICIOUS",
        "risk_score": 50,
        "confidence": "LOW",
        "scam_type": "Unknown",
        "summary": "Analysis could not be parsed. Treat this message with caution.",
        "red_flags": ["AI response parsing error — manual review recommended"],
        "advice": "Do not click any links or share any personal information until verified.",
    }


# ── Result normalizer ────────────────────────────────────────────────────────

def _normalize_result(result: dict) -> None:
    """Ensure all required fields are present and valid."""
    verdict = str(result.get("verdict", "SUSPICIOUS")).upper()
    if verdict not in ("SAFE", "SUSPICIOUS", "SCAM"):
        verdict = "SUSPICIOUS"
    result["verdict"] = verdict

    try:
        score = int(result.get("risk_score", 50))
        result["risk_score"] = max(0, min(100, score))
    except (TypeError, ValueError):
        result["risk_score"] = 50

    confidence = str(result.get("confidence", "MEDIUM")).upper()
    if confidence not in ("LOW", "MEDIUM", "HIGH"):
        confidence = "MEDIUM"
    result["confidence"] = confidence

    if not isinstance(result.get("red_flags"), list):
        result["red_flags"] = []

    for field in ("summary", "advice", "scam_type"):
        if not result.get(field):
            result[field] = "N/A"


# ── Public API ───────────────────────────────────────────────────────────────

def analyze_text(text: str, lang: str = "en", sender_id: str | None = None) -> tuple[dict, str]:
    """Analyze a text message (SMS/WhatsApp/email) for scam patterns.

    Args:
        text: The raw message text to analyze.
        lang: BCP-47 language code for the desired output language.
        sender_id: Optional SMS sender header (e.g. VK-AMZNOT).

    Returns:
        (result_dict, provider_used)
        result_dict keys: verdict, risk_score, confidence, scam_type,
                          summary, red_flags, advice, pre_filter

    Raises:
        ValueError: If text is empty.
        RuntimeError: If Gemini API call fails.
    """
    if not text or not text.strip():
        raise ValueError("Text cannot be empty.")

    text = text.strip()

    # Step 1: Pre-filter pattern matching
    pre = _pre_filter(text)
    logger.debug("Pre-filter result: %s", pre)

    # Step 2: Build user prompt with language context
    lang_name = LANGUAGE_NAMES.get(lang, "English")
    user_prompt = f"""Analyze the following message for scam/fraud indicators.

IMPORTANT: Respond entirely in {lang_name} (language code: {lang}), except for the JSON keys which must remain in English.

Message to analyze:
---
{text}
---

Pre-screening hints (from automated pattern matching):
- Matched keywords: {', '.join(pre['matched_keywords']) if pre['matched_keywords'] else 'none'}
- High-risk signals detected: {'; '.join(pre['high_risk_signals']) if pre['high_risk_signals'] else 'none'}
- Pattern-based risk score: {pre['pre_risk_score']}/100

Use the pre-screening hints to inform but not blindly determine your verdict. Respond with ONLY a valid JSON object."""

    # Step 3: Call Gemini text API
    api_key = os.getenv("GEMINI_API_KEY", GEMINI_API_KEY)
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not configured.")

    try:
        raw_text, reasoning = _call_gemini_text(text, user_prompt)
        result = _extract_json(raw_text)
        _normalize_result(result)

        # Attach pre-filter and reasoning metadata
        result["pre_filter"] = pre
        if reasoning and not result.get("reasoning"):
            result["reasoning"] = reasoning

        return result, "gemini"
    except Exception as e:
        logger.exception("Gemini text analysis failed")
        raise RuntimeError(f"Text analysis failed: {e}") from e
