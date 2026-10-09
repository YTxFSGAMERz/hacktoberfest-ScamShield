import base64
import io
import os
import sys
from pathlib import Path

# Add project root to sys.path so scamshield package is discovered on Vercel
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS

from scamshield.alert import send_discord_alert
from scamshield.analyzer import analyze_screenshot, validate_image
from scamshield.chat import chat_with_scamshield
from scamshield.scanner_text import analyze_text
from scamshield.scanner_url import analyze_url
from scamshield.scanner_phone import analyze_phone
from scamshield.scanner_qr import analyze_qr
from scamshield.quiz_data import QUIZ_QUESTIONS, QUIZ_BADGES, CATEGORY_COLORS
from scamshield.victim_recovery import BANK_NUMBERS, get_golden_hour_status
from scamshield.hygiene import HYGIENE_CHECKS, calculate_hygiene_score
from scamshield.community import report_scam, check_community_reports, get_recent_reports

try:
    from scamshield.i18n import SUPPORTED_LANGUAGES, t
except (ImportError, AttributeError):
    SUPPORTED_LANGUAGES = {
        "en": "English",
        "hi": "हिंदी (Hindi)",
        "gu": "ગુજરાતી (Gujarati)",
    }
    def t(lang, key):
        return key

from scamshield.intel import EMERGENCY_CONTACTS, GOLDEN_HOUR_STEPS, SCAM_TRENDS
import traceback
from scamshield.llm import get_provider_status

# Initialize Flask-Limiter for API protection
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["300 per hour", "60 per minute"],
        storage_uri="memory://",
    )
    HAS_LIMITER = True
except Exception:
    HAS_LIMITER = False
    limiter = None

PUBLIC_DIR = ROOT_DIR / "public"
app = Flask(__name__, static_folder=str(PUBLIC_DIR), static_url_path="")
CORS(app)

if HAS_LIMITER and limiter:
    limiter.init_app(app)


@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({
        "error": str(e),
        "traceback": traceback.format_exc()
    }), 500


import urllib.parse


class VercelPathMiddleware:
    """Restores the original request path when Vercel internal rewrites route to /api/index.py."""
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        qs = environ.get("QUERY_STRING", "")
        subpath = None
        for part in qs.split("&"):
            if part.startswith("path="):
                subpath = urllib.parse.unquote(part.split("=", 1)[1])
                break

        if subpath:
            clean_sub = subpath.lstrip("/")
            if not clean_sub.startswith("api/"):
                environ["PATH_INFO"] = f"/api/{clean_sub}"
            else:
                environ["PATH_INFO"] = f"/{clean_sub}"
        else:
            for header in ("HTTP_X_MATCHED_PATH", "HTTP_X_FORWARDED_URI", "HTTP_X_VERCEL_MATCHED_PATH"):
                target = environ.get(header)
                if target and target not in ("/api/index.py", "/api/index"):
                    environ["PATH_INFO"] = urllib.parse.unquote(target.split("?")[0])
                    break
        return self.wsgi_app(environ, start_response)


app.wsgi_app = VercelPathMiddleware(app.wsgi_app)


@app.route("/", methods=["GET"])
def index():
    index_file = PUBLIC_DIR / "index.html"
    if index_file.exists():
        return send_file(str(index_file))
    return health_check()


@app.route("/<path:path>", methods=["GET"])
def static_proxy(path: str):
    if path.startswith("api/") or path.startswith("scan/") or path in (
        "analyze", "chat", "alert", "intel", "samples", "sample",
        "languages", "quiz", "hygiene", "victim", "community", "health"
    ):
        return jsonify({"error": f"Endpoint /{path} not found or method not allowed"}), 404
    target = PUBLIC_DIR / path
    if target.exists() and target.is_file():
        return send_file(str(target))
    return jsonify({"error": f"File '{path}' not found"}), 404


@app.route("/api", methods=["GET"])
@app.route("/api/index.py", methods=["GET"])
@app.route("/api/health", methods=["GET"])
@app.route("/health", methods=["GET"])
def health_check():
    status = get_provider_status()
    return jsonify({
        "status": "healthy",
        "service": "ScamShield",
        "version": "2.0.0-ultimate",
        "provider": status,
        "languages": SUPPORTED_LANGUAGES,
        "features": [
            "screenshot_vision_scanner",
            "text_sms_analyzer",
            "url_phishing_scanner",
            "phone_intelligence_lookup",
            "qr_code_decoder",
            "scam_awareness_quiz",
            "crowdsourced_community_db",
            "victim_recovery_assistant",
            "security_hygiene_checker",
            "family_alert_center",
        ],
    })


@app.route("/api/languages", methods=["GET"])
@app.route("/languages", methods=["GET"])
def get_languages():
    return jsonify({"success": True, "languages": SUPPORTED_LANGUAGES})


@app.route("/api/intel", methods=["GET"])
@app.route("/intel", methods=["GET"])
def get_intel():
    return jsonify({
        "emergency_contacts": EMERGENCY_CONTACTS,
        "scam_trends": SCAM_TRENDS,
        "golden_hour_steps": GOLDEN_HOUR_STEPS,
        "quiz_badges": QUIZ_BADGES,
        "quiz_total_questions": len(QUIZ_QUESTIONS),
        "hygiene_total_checks": len(HYGIENE_CHECKS),
    })


@app.route("/api/samples", methods=["GET"])
@app.route("/samples", methods=["GET"])
def get_samples():
    samples = [
        {"id": "genuine_otp", "name": "Amazon OTP", "file": "safe_login_otp.png", "type": "genuine", "desc": "Official 6-char TRAI sender with standard OTP clause"},
        {"id": "genuine_debit", "name": "HDFC Bank Debit", "file": "safe_bank_alert.png", "type": "genuine", "desc": "Routine transaction debit notification with masked A/C"},
        {"id": "genuine_delivery", "name": "Swiggy Delivery", "file": "safe_swiggy_delivery.png", "type": "genuine", "desc": "Standard food delivery driver arrival update"},
        {"id": "genuine_ticket", "name": "IRCTC Ticket", "file": "safe_irctc_ticket.png", "type": "genuine", "desc": "Official Indian Railways train booking confirmation"},
        {"id": "scam_kyc", "name": "SBI KYC Block", "file": "kyc_scam.png", "type": "scam", "desc": "Urgent account block threat with fake bit.ly link"},
        {"id": "scam_lottery", "name": "Lucky Draw / Prize", "file": "lottery_scam.png", "type": "scam", "desc": "Fake ₹25,00,000 lottery demand with advance processing fee"},
        {"id": "scam_upi", "name": "UPI Refund Phishing", "file": "upi_phishing.png", "type": "scam", "desc": "Deceptive QR code asking for PIN to 'receive' money"},
        {"id": "scam_job", "name": "Telegram Job Fraud", "file": "job_scam.png", "type": "scam", "desc": "Part-time YouTube like scheme leading to crypto investment trap"},
        {"id": "scam_govt", "name": "TRAI Threat Notice", "file": "govt_impersonation.png", "type": "scam", "desc": "Digital arrest intimidation pretending to be telecom authority"},
    ]
    return jsonify({"samples": samples})


@app.route("/api/sample/<filename>", methods=["GET"])
@app.route("/sample/<filename>", methods=["GET"])
def get_sample_image(filename: str):
    safe_name = os.path.basename(filename)
    candidates = [
        ROOT_DIR / "api" / "samples" / safe_name,
        ROOT_DIR / "public" / "samples" / safe_name,
        ROOT_DIR / "tests" / "samples" / safe_name,
        Path(__file__).resolve().parent / "samples" / safe_name,
    ]
    for p in candidates:
        if p.exists():
            return send_file(str(p), mimetype="image/png")
    return jsonify({"error": "Sample image not found"}), 404


# ── SCANNER 1: Screenshot Vision Analyzer ────────────────────────────────────
@app.route("/api/analyze", methods=["POST"])
@app.route("/analyze", methods=["POST"])
def analyze():
    image_bytes = None
    language = "en"
    sender_id = None

    if request.is_json:
        data = request.get_json(silent=True) or {}
        language = data.get("language", "en")
        sender_id = data.get("sender_id") or None
        b64 = data.get("image_base64", "")
        if b64:
            if "," in b64:
                b64 = b64.split(",", 1)[1]
            try:
                image_bytes = base64.b64decode(b64)
            except Exception:
                return jsonify({"error": "Invalid base64 payload"}), 400
    elif request.files and "file" in request.files:
        uploaded_file = request.files["file"]
        image_bytes = uploaded_file.read()
        language = request.form.get("language", "en")
        sender_id = request.form.get("sender_id") or None

    if not image_bytes:
        return jsonify({"error": "No image provided. Upload a file or provide image_base64."}), 400

    try:
        result, provider = analyze_screenshot(image_bytes, lang=language)
        result["provider"] = provider
        return jsonify({"success": True, "data": result})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ── SCANNER 2: Text / SMS Message Analyzer ───────────────────────────────────
@app.route("/api/scan/text", methods=["POST"])
@app.route("/scan/text", methods=["POST"])
def scan_text():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    language = data.get("language", "en")
    sender_id = data.get("sender_id")

    if not text:
        return jsonify({"error": "No message text provided."}), 400

    try:
        result, provider = analyze_text(text, lang=language, sender_id=sender_id)
        result["provider"] = provider
        return jsonify({"success": True, "data": result})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ── SCANNER 3: URL Phishing Detector ──────────────────────────────────────────
@app.route("/api/scan/url", methods=["POST"])
@app.route("/scan/url", methods=["POST"])
def scan_url():
    data = request.get_json(silent=True) or {}
    url = data.get("url", "").strip()

    if not url:
        return jsonify({"error": "No URL provided."}), 400

    try:
        result = analyze_url(url)
        return jsonify({"success": True, "data": result})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ── SCANNER 4: Phone Number Intelligence ──────────────────────────────────────
@app.route("/api/scan/phone", methods=["POST"])
@app.route("/scan/phone", methods=["POST"])
def scan_phone():
    data = request.get_json(silent=True) or {}
    phone = data.get("phone", "").strip()

    if not phone:
        return jsonify({"error": "No phone number provided."}), 400

    try:
        result = analyze_phone(phone)
        return jsonify({"success": True, "data": result})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ── SCANNER 5: QR Code Decoder & Analyzer ─────────────────────────────────────
@app.route("/api/scan/qr", methods=["POST"])
@app.route("/scan/qr", methods=["POST"])
def scan_qr():
    image_bytes = None
    if request.is_json:
        data = request.get_json(silent=True) or {}
        b64 = data.get("image_base64", "")
        if b64:
            if "," in b64:
                b64 = b64.split(",", 1)[1]
            try:
                image_bytes = base64.b64decode(b64)
            except Exception:
                return jsonify({"error": "Invalid base64 payload"}), 400
    elif request.files and "file" in request.files:
        image_bytes = request.files["file"].read()

    if not image_bytes:
        return jsonify({"error": "No QR image provided."}), 400

    try:
        result = analyze_qr(image_bytes)
        return jsonify({"success": True, "data": result})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ── SCAM AWARENESS QUIZ ───────────────────────────────────────────────────────
@app.route("/api/quiz", methods=["GET"])
@app.route("/quiz", methods=["GET"])
def get_quiz():
    diff = request.args.get("difficulty", "all").lower()
    limit = request.args.get("limit", type=int) or 15

    if diff in ("beginner", "intermediate", "expert"):
        filtered = [q for q in QUIZ_QUESTIONS if q.get("difficulty") == diff]
    else:
        filtered = list(QUIZ_QUESTIONS)

    import random
    sample_pool = list(filtered)
    random.shuffle(sample_pool)
    selected = sample_pool[:limit]

    return jsonify({
        "success": True,
        "difficulty": diff,
        "total_available": len(filtered),
        "count": len(selected),
        "questions": selected,
        "badges": QUIZ_BADGES,
        "category_colors": CATEGORY_COLORS,
    })


# ── CROWDSOURCED COMMUNITY DATABASE ──────────────────────────────────────────
@app.route("/api/community/report", methods=["POST"])
@app.route("/community/report", methods=["POST"])
def community_report():
    data = request.get_json(silent=True) or {}
    scam_type = data.get("scam_type", "phone")
    value = data.get("value", "").strip()
    category = data.get("category", "General Fraud")
    description = data.get("description", "").strip()
    lang = data.get("language", "en")

    if not value:
        return jsonify({"error": "Entity value (phone/UPI/URL) is required."}), 400

    res = report_scam(
        scam_type=scam_type,
        value=value,
        description=description,
        category=category,
        lang=lang,
    )
    return jsonify(res)


@app.route("/api/community/check", methods=["GET"])
@app.route("/community/check", methods=["GET"])
def community_check():
    scam_type = request.args.get("type", "phone").lower()
    value = request.args.get("value", "").strip()

    if not value:
        return jsonify({"error": "Value parameter is required"}), 400

    res = check_community_reports(scam_type=scam_type, value=value)
    return jsonify({"success": True, "data": res})


@app.route("/api/community/recent", methods=["GET"])
@app.route("/community/recent", methods=["GET"])
def community_recent():
    limit = request.args.get("limit", default=10, type=int)
    reports = get_recent_reports(limit=min(limit, 50))
    return jsonify({"success": True, "reports": reports})


# ── SECURITY HYGIENE ASSESSMENT ───────────────────────────────────────────────
@app.route("/api/hygiene/checks", methods=["GET"])
@app.route("/hygiene/checks", methods=["GET"])
def hygiene_checks():
    return jsonify({
        "success": True,
        "checks": HYGIENE_CHECKS,
        "total": len(HYGIENE_CHECKS),
    })


@app.route("/api/hygiene/score", methods=["POST"])
@app.route("/hygiene/score", methods=["POST"])
def hygiene_score():
    data = request.get_json(silent=True) or {}
    checked_ids = data.get("checked_ids", [])
    result = calculate_hygiene_score(checked_ids)
    return jsonify({"success": True, "data": result})


# ── VICTIM RECOVERY ASSISTANT ─────────────────────────────────────────────────
@app.route("/api/victim/banks", methods=["GET"])
@app.route("/victim/banks", methods=["GET"])
def victim_banks():
    return jsonify({"success": True, "banks": BANK_NUMBERS})


@app.route("/api/victim/status", methods=["POST"])
@app.route("/victim/status", methods=["POST"])
def victim_status():
    data = request.get_json(silent=True) or {}
    minutes = data.get("minutes_elapsed", 30)
    try:
        minutes = int(minutes)
    except (ValueError, TypeError):
        minutes = 30
    status = get_golden_hour_status(minutes)
    return jsonify({"success": True, "data": status})


# ── AI CHAT ASSISTANT ─────────────────────────────────────────────────────────
@app.route("/api/chat", methods=["POST"])
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    messages = data.get("messages", [])
    language = data.get("language", "en")
    scan_context = data.get("scan_context")

    if not messages:
        return jsonify({"error": "Messages list cannot be empty"}), 400

    try:
        reply, provider = chat_with_scamshield(
            messages=messages,
            current_analysis=scan_context if isinstance(scan_context, dict) else None,
            lang=language,
        )
        return jsonify({"success": True, "reply": reply, "provider": provider})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ── ALERT DISPATCH ────────────────────────────────────────────────────────────
@app.route("/api/alert", methods=["POST"])
@app.route("/alert", methods=["POST"])
def alert():
    data = request.get_json() or {}
    result = {
        "verdict": data.get("verdict", "SCAM"),
        "risk_score": data.get("risk_score", 80),
        "summary": data.get("summary", ""),
        "red_flags": data.get("red_flags", []),
        "action_items": data.get("action_items", []),
    }
    webhook_url = data.get("webhook_url")
    language = data.get("language", "en")

    try:
        success, message, alert_text = send_discord_alert(
            result=result,
            webhook_url=webhook_url,
            language=language,
        )
        return jsonify({
            "success": success,
            "message": message,
            "alert_text": alert_text,
        })
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# For local testing
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
