"""ScamShield — URL phishing and malicious domain detector.

Performs multi-layer URL analysis:
1. Expand shortened URLs (bit.ly, tinyurl, t.co, etc.)
2. Google Safe Browsing API v4 threat check
3. VirusTotal URL scan
4. python-whois domain age check
5. Suspicious pattern matching (homoglyphs, scam TLDs, fake banking domains)
6. Known Indian scam domain pattern check

Usage:
    from scamshield.scanner_url import analyze_url

    result = analyze_url("https://sbi-kyc-update.xyz/verify?acc=1234")
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import re
import time
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GOOGLE_SAFE_BROWSING_KEY = os.getenv("GOOGLE_SAFE_BROWSING_KEY", "") or GEMINI_API_KEY
VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY", "")

# ── Known URL shortener domains ───────────────────────────────────────────────

SHORTENER_DOMAINS = {
    "bit.ly", "bitly.com", "tinyurl.com", "t.co", "ow.ly", "is.gd",
    "buff.ly", "short.io", "rb.gy", "cutt.ly", "shorturl.at", "tiny.cc",
    "v.gd", "clck.ru", "yourls.org", "goo.gl", "gg.gg", "qr.ae",
}

# ── Suspicious TLDs commonly used in phishing ────────────────────────────────

SUSPICIOUS_TLDS = {
    ".xyz", ".tk", ".ml", ".ga", ".cf", ".gq", ".click", ".top",
    ".work", ".party", ".faith", ".accountant", ".loan", ".download",
    ".stream", ".science", ".racing", ".bid", ".trade", ".date", ".review",
    ".kim", ".men", ".webcam", ".win", ".ninja", ".space",
}

# ── Homoglyph character patterns ─────────────────────────────────────────────

HOMOGLYPH_SUSPICIOUS = re.compile(
    r"(sb[1iI]|[1iI]cici|hdf[cС]|ax[1iI]s|pay[tтТ]m|paph?one|phonep[eЕ]|"
    r"go{2,}gle|fac[eЕ]b[oо]{2}k|[аa]mazo[nн]|m[iI][cс]rosoft|app[1iI]e)",
    re.IGNORECASE,
)

# ── Known Indian scam domain patterns ────────────────────────────────────────

INDIAN_SCAM_PATTERNS = re.compile(
    r"(sbi.{0,5}(kyc|update|verify|block|card|login|secure)|"
    r"hdfc.{0,5}(kyc|update|verify|block|alert|secure)|"
    r"icici.{0,5}(kyc|verify|update|secure|net)|"
    r"axis.{0,5}(kyc|verify|update|bank)|"
    r"paytm.{0,5}(kyc|verify|update|wallet|cash)|"
    r"npci.{0,5}(upi|verify|kyc)|"
    r"(kyc|verify|update).{0,10}(sbi|hdfc|icici|axis|bank|upi|paytm)|"
    r"(income.?tax|it.?dept|trai|uidai|govt).{0,10}(verify|update|notice|alert)|"
    r"rbi.{0,5}(sachet|verify|license|nbfc)|"
    r"(pm.?kisan|pmay|jandhan|mudra).{0,10}(apply|verify|loan|scheme)|"
    r"lucky.?draw|lottery.?india|prize.?claim|"
    r"earn.{0,10}(daily|per.?day|lakh|crore)|"
    r"(job|work).{0,5}(home|ghar|abroad).{0,10}(apply|register)|"
    r"crypto.{0,5}(invest|multiply|double|return|profit))",
    re.IGNORECASE,
)

# ── Safe Browsing threat types ────────────────────────────────────────────────

GSB_THREAT_TYPES = [
    "MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE",
    "POTENTIALLY_HARMFUL_APPLICATION", "THREAT_TYPE_UNSPECIFIED",
]


# ── Step 1: Expand shortened URL ──────────────────────────────────────────────

def _expand_url(url: str) -> tuple[str, bool]:
    """Follow redirects to expand shortened URLs.

    Returns:
        (final_url, was_shortened)
    """
    parsed = urlparse(url)
    domain = parsed.netloc.lower().lstrip("www.")
    was_shortened = domain in SHORTENER_DOMAINS

    try:
        resp = requests.head(
            url,
            allow_redirects=True,
            timeout=10,
            headers={"User-Agent": "ScamShield-URLScanner/1.0"},
        )
        final_url = resp.url
        # Also count as shortened if there were redirects
        if final_url != url:
            was_shortened = was_shortened or domain in SHORTENER_DOMAINS
        return final_url, was_shortened
    except Exception as e:
        logger.debug("URL expansion failed for %s: %s", url, e)
        return url, was_shortened


# ── Step 2: Google Safe Browsing ─────────────────────────────────────────────

def _check_google_safe_browsing(url: str) -> dict:
    """Check URL against Google Safe Browsing API v4.

    Returns:
        {checked: bool, threats: list, error: str|None}
    """
    key = os.getenv("GOOGLE_SAFE_BROWSING_KEY", GOOGLE_SAFE_BROWSING_KEY)
    if not key:
        return {"checked": False, "threats": [], "error": "No Safe Browsing API key"}

    endpoint = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={key}"
    payload = {
        "client": {"clientId": "scamshield", "clientVersion": "1.0.0"},
        "threatInfo": {
            "threatTypes": GSB_THREAT_TYPES,
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}],
        },
    }

    try:
        resp = requests.post(endpoint, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        matches = data.get("matches", [])
        threats = [m.get("threatType", "UNKNOWN") for m in matches]
        return {"checked": True, "threats": threats, "error": None}
    except Exception as e:
        logger.warning("Google Safe Browsing check failed: %s", e)
        return {"checked": False, "threats": [], "error": str(e)}


# ── Step 3: VirusTotal ────────────────────────────────────────────────────────

def _check_virustotal(url: str) -> dict:
    """Submit URL to VirusTotal and retrieve scan results.

    Returns:
        {checked: bool, malicious: int, suspicious: int, total: int, error: str|None}
    """
    vt_key = os.getenv("VIRUSTOTAL_API_KEY", VIRUSTOTAL_API_KEY)
    if not vt_key:
        return {"checked": False, "malicious": 0, "suspicious": 0, "total": 0, "error": "No VirusTotal API key"}

    headers = {"x-apikey": vt_key}

    try:
        # Encode URL for VirusTotal ID
        url_id = base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")

        # First try to GET existing analysis
        get_resp = requests.get(
            f"https://www.virustotal.com/api/v3/urls/{url_id}",
            headers=headers,
            timeout=15,
        )

        if get_resp.status_code == 200:
            data = get_resp.json()
        else:
            # Submit for scanning
            post_resp = requests.post(
                "https://www.virustotal.com/api/v3/urls",
                headers=headers,
                data={"url": url},
                timeout=15,
            )
            post_resp.raise_for_status()
            scan_id = post_resp.json().get("data", {}).get("id", "")

            if not scan_id:
                return {"checked": False, "malicious": 0, "suspicious": 0, "total": 0, "error": "No scan ID from VT"}

            # Wait briefly for analysis
            time.sleep(3)
            analysis_resp = requests.get(
                f"https://www.virustotal.com/api/v3/analyses/{scan_id}",
                headers=headers,
                timeout=15,
            )
            analysis_resp.raise_for_status()
            data = analysis_resp.json()

        stats = (
            data.get("data", {})
            .get("attributes", {})
            .get("last_analysis_stats", {})
        )
        return {
            "checked": True,
            "malicious": stats.get("malicious", 0),
            "suspicious": stats.get("suspicious", 0),
            "total": sum(stats.values()) if stats else 0,
            "error": None,
        }
    except Exception as e:
        logger.warning("VirusTotal check failed: %s", e)
        return {"checked": False, "malicious": 0, "suspicious": 0, "total": 0, "error": str(e)}


# ── Step 4: WHOIS domain age ──────────────────────────────────────────────────

def _check_whois(domain: str) -> dict:
    """Check domain registration age via python-whois.

    Returns:
        {checked: bool, creation_date: str|None, age_days: int|None, is_new: bool, error: str|None}
    """
    try:
        import whois  # type: ignore
        w = whois.whois(domain)
        creation_date = w.creation_date
        if isinstance(creation_date, list):
            creation_date = creation_date[0]

        if creation_date is None:
            return {"checked": True, "creation_date": None, "age_days": None, "is_new": False, "error": None}

        import datetime
        now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        if hasattr(creation_date, "replace"):
            creation_date = creation_date.replace(tzinfo=None)
        age_days = (now - creation_date).days
        is_new = age_days < 90  # Domains younger than 90 days are suspicious

        return {
            "checked": True,
            "creation_date": str(creation_date)[:10],
            "age_days": age_days,
            "is_new": is_new,
            "error": None,
        }
    except ImportError:
        return {"checked": False, "creation_date": None, "age_days": None, "is_new": False, "error": "python-whois not installed"}
    except Exception as e:
        logger.debug("WHOIS lookup failed for %s: %s", domain, e)
        return {"checked": False, "creation_date": None, "age_days": None, "is_new": False, "error": str(e)}


# ── Step 5 & 6: Pattern analysis ─────────────────────────────────────────────

def _check_patterns(url: str, domain: str) -> dict:
    """Analyze URL for suspicious patterns, homoglyphs, scam domains.

    Returns:
        {suspicious_tld: bool, homoglyph_detected: bool, indian_scam_pattern: bool,
         flags: list[str]}
    """
    flags: list[str] = []
    tld = "." + domain.rsplit(".", 1)[-1].lower() if "." in domain else ""

    suspicious_tld = tld in SUSPICIOUS_TLDS
    if suspicious_tld:
        flags.append(f"Suspicious TLD '{tld}' — commonly used in phishing campaigns")

    homoglyph_detected = bool(HOMOGLYPH_SUSPICIOUS.search(domain))
    if homoglyph_detected:
        flags.append(f"Homoglyph/lookalike domain detected in '{domain}' — possible brand impersonation")

    indian_scam_pattern = bool(INDIAN_SCAM_PATTERNS.search(url))
    if indian_scam_pattern:
        flags.append(f"URL matches known Indian scam domain patterns (fake banking/KYC/lottery)")

    # IP address as URL host (never legitimate for banks/govt)
    if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", domain):
        flags.append("URL uses raw IP address instead of domain name — extremely suspicious")

    # Excessive subdomains
    parts = domain.split(".")
    if len(parts) > 4:
        flags.append(f"Excessive subdomain depth ({len(parts)} levels) — common in phishing")

    # Domain-in-path trick (e.g., http://scam.com/sbi.co.in/login)
    parsed = urlparse(url)
    if any(legit in parsed.path.lower() for legit in ["sbi.co.in", "hdfcbank.com", "icicibank.com", "npci.org.in"]):
        flags.append("Legitimate domain name appears only in URL path — redirect/spoofing technique")

    # HTTP (not HTTPS) for financial domains
    if parsed.scheme == "http" and indian_scam_pattern:
        flags.append("Unencrypted HTTP connection on a financial-looking domain")

    return {
        "suspicious_tld": suspicious_tld,
        "homoglyph_detected": homoglyph_detected,
        "indian_scam_pattern": indian_scam_pattern,
        "flags": flags,
    }


# ── UPI detection ─────────────────────────────────────────────────────────────

def _is_upi_url(url: str) -> bool:
    return url.startswith("upi://") or "pa=" in url.lower()


# ── Risk score aggregation ────────────────────────────────────────────────────

def _calculate_risk(
    gsb: dict,
    vt: dict,
    whois_info: dict,
    patterns: dict,
    is_shortened: bool,
) -> tuple[int, str, list[str]]:
    """Aggregate all check results into a final risk score.

    Returns:
        (risk_score 0-100, verdict, threat_list)
    """
    score = 0
    threats: list[str] = []
    red_flags: list[str] = list(patterns.get("flags", []))

    # Google Safe Browsing (very high weight)
    if gsb.get("threats"):
        score += 70
        for t in gsb["threats"]:
            threats.append(f"Google Safe Browsing: {t}")
            red_flags.append(f"Google Safe Browsing flagged as {t}")

    # VirusTotal
    if vt.get("checked"):
        malicious = vt.get("malicious", 0)
        suspicious = vt.get("suspicious", 0)
        if malicious > 0:
            score += min(malicious * 10, 50)
            threats.append(f"VirusTotal: {malicious} engines flagged malicious")
            red_flags.append(f"{malicious} VirusTotal engines detected threats")
        elif suspicious > 0:
            score += min(suspicious * 5, 20)
            red_flags.append(f"{suspicious} VirusTotal engines marked suspicious")

    # Pattern flags
    if patterns.get("indian_scam_pattern"):
        score += 35
    if patterns.get("homoglyph_detected"):
        score += 30
    if patterns.get("suspicious_tld"):
        score += 20

    # New domain (< 90 days)
    if whois_info.get("is_new"):
        score += 25
        age = whois_info.get("age_days", 0)
        red_flags.append(f"Very new domain — only {age} days old (registered within 90 days)")

    # URL shortened → adds moderate risk
    if is_shortened:
        score += 10
        red_flags.append("URL was expanded from a shortener — original destination was hidden")

    score = min(score, 100)

    if score >= 70:
        verdict = "SCAM"
    elif score >= 35:
        verdict = "SUSPICIOUS"
    else:
        verdict = "SAFE"

    return score, verdict, threats


# ── Public API ────────────────────────────────────────────────────────────────

def analyze_url(url: str) -> dict:
    """Analyze a URL for phishing, malware, and scam indicators.

    Args:
        url: The URL string to analyze (http/https/upi scheme).

    Returns:
        dict with keys:
            verdict, risk_score, url, domain, threats, whois_info,
            is_shortened, redirect_url, red_flags, checks_performed
    """
    if not url or not url.strip():
        raise ValueError("URL cannot be empty.")

    url = url.strip()

    # Add scheme if missing
    if not re.match(r"^https?://", url, re.IGNORECASE) and not url.startswith("upi://"):
        url = "https://" + url

    # Parse domain
    parsed = urlparse(url)
    domain = parsed.netloc.lower().lstrip("www.")
    if not domain:
        return {
            "verdict": "SUSPICIOUS",
            "risk_score": 40,
            "url": url,
            "domain": "",
            "threats": [],
            "whois_info": {},
            "is_shortened": False,
            "redirect_url": None,
            "red_flags": ["Could not parse domain from URL"],
            "checks_performed": [],
        }

    # Step 1: Expand shortened URLs
    redirect_url = None
    final_url = url
    is_shortened = False
    try:
        final_url, is_shortened = _expand_url(url)
        if final_url != url:
            redirect_url = final_url
            # Re-parse domain from final URL
            domain = urlparse(final_url).netloc.lower().lstrip("www.") or domain
    except Exception as e:
        logger.debug("URL expansion error: %s", e)

    checks_performed: list[str] = ["url_expansion"]

    # Step 2: Google Safe Browsing
    gsb = _check_google_safe_browsing(final_url)
    if gsb.get("checked"):
        checks_performed.append("google_safe_browsing")

    # Step 3: VirusTotal
    vt = _check_virustotal(final_url)
    if vt.get("checked"):
        checks_performed.append("virustotal")

    # Step 4: WHOIS
    whois_info = _check_whois(domain)
    if whois_info.get("checked"):
        checks_performed.append("whois")

    # Steps 5 & 6: Pattern analysis
    patterns = _check_patterns(final_url, domain)
    checks_performed.append("pattern_analysis")

    # Aggregate
    risk_score, verdict, threats = _calculate_risk(gsb, vt, whois_info, patterns, is_shortened)

    return {
        "verdict": verdict,
        "risk_score": risk_score,
        "url": url,
        "final_url": final_url,
        "domain": domain,
        "threats": threats,
        "whois_info": {
            "creation_date": whois_info.get("creation_date"),
            "age_days": whois_info.get("age_days"),
            "is_new_domain": whois_info.get("is_new", False),
        },
        "is_shortened": is_shortened,
        "redirect_url": redirect_url,
        "red_flags": patterns.get("flags", []) + [f for f in threats],
        "checks_performed": checks_performed,
        "safe_browsing": gsb,
        "virustotal": {
            "checked": vt.get("checked", False),
            "malicious": vt.get("malicious", 0),
            "suspicious": vt.get("suspicious", 0),
            "total_engines": vt.get("total", 0),
        },
    }
