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

PUBLIC_DIR = ROOT_DIR / "public"
app = Flask(__name__, static_folder=str(PUBLIC_DIR), static_url_path="")
CORS(app)


@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({
        "error": str(e),
        "traceback": traceback.format_exc()
    }), 500


class VercelPathMiddleware:
    """Restores the original request path when Vercel internal rewrites route to /api/index.py."""
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        qs = environ.get("QUERY_STRING", "")
        subpath = None
        for part in qs.split("&"):
            if part.startswith("path="):
                subpath = part.split("=", 1)[1]
                break

        if subpath:
            environ["PATH_INFO"] = f"/{subpath}"
        else:
            for header in ("HTTP_X_MATCHED_PATH", "HTTP_X_FORWARDED_URI", "HTTP_X_VERCEL_MATCHED_PATH"):
                target = environ.get(header)
                if target and target not in ("/api/index.py", "/api/index"):
                    environ["PATH_INFO"] = target.split("?")[0]
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
    target = PUBLIC_DIR / path
    if target.exists() and target.is_file():
        return send_file(str(target))
    # If not found in public, check if it's an api route or 404
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
        "provider": status,
        "languages": list(SUPPORTED_LANGUAGES.keys()),
        "debug_path": request.path,
        "debug_x_matched_path": request.headers.get("x-matched-path"),
        "debug_x_forwarded_uri": request.headers.get("x-forwarded-uri"),
        "debug_url": request.url,
    })


@app.route("/api/intel", methods=["GET"])
@app.route("/intel", methods=["GET"])
def get_intel():
    return jsonify({
        "emergency_contacts": EMERGENCY_CONTACTS,
        "scam_trends": SCAM_TRENDS,
        "golden_hour_steps": GOLDEN_HOUR_STEPS,
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
