"""Generate synthetic genuine & scam screenshot samples for testing.

Run: python tests/generate_samples.py
"""

from PIL import Image, ImageDraw
from pathlib import Path

SAMPLES_DIR = Path(__file__).parent / "samples"
SAMPLES_DIR.mkdir(exist_ok=True)


def make_sms_screenshot(
    filename: str,
    sender: str,
    message: str,
    bg_color: tuple = (255, 255, 255),
    header_color: tuple = (0, 122, 255),
    width: int = 400,
) -> Path:
    """Generate a realistic SMS screenshot."""
    height = max(300, 80 + len(message) // 35 * 22 + 80)
    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Header bar
    draw.rectangle([(0, 0), (width, 56)], fill=header_color)
    draw.text((16, 16), f"< {sender}", fill="white")

    # Timestamp
    draw.text((width - 80, 64), "10:35 AM", fill="#999")

    # Message bubble
    bubble_padding = 12
    bubble_x1, bubble_y1 = 12, 80
    bubble_x2 = width - 12
    text_start_y = bubble_y1 + bubble_padding

    draw.rounded_rectangle(
        [(bubble_x1, bubble_y1), (bubble_x2, height - 40)],
        radius=12,
        fill="#F0F0F0",
    )

    # Message text (wrap manually)
    words = message.split()
    lines = []
    current_line = ""
    max_chars = 45
    for word in words:
        if len(current_line) + len(word) + 1 <= max_chars:
            current_line += (" " if current_line else "") + word
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)

    y = text_start_y + 4
    for line in lines:
        draw.text((bubble_x1 + bubble_padding, y), line, fill="#000")
        y += 20

    # Save
    output_path = SAMPLES_DIR / filename
    img.save(str(output_path), "PNG")
    print(f"  Created: {output_path.name}")
    return output_path


def generate_all_samples():
    print(f"Generating realistic test samples in {SAMPLES_DIR}...")

    # ── GENUINE / SAFE SAMPLES ────────────────────────────────────────────────

    # 1. Genuine Bank Debit Alert (Standard TRAI header format)
    make_sms_screenshot(
        "safe_bank_alert.png",
        sender="VK-HDFCBK",
        message=(
            "Rs. 450.00 debited from HDFC Bank A/C **4092 on 03-Oct-26 at Swiggy. "
            "Avl Bal: Rs. 24,150.70. Not you? Call 18002586161. "
            "Never share OTP or UPI PIN with anyone."
        ),
        bg_color=(245, 255, 245),
        header_color=(0, 75, 140),
    )

    # 2. Genuine Amazon Login OTP
    make_sms_screenshot(
        "safe_login_otp.png",
        sender="BZ-AMAZON",
        message=(
            "849201 is your Amazon verification OTP. Valid for 10 minutes. "
            "For security reasons, do not share this OTP with anyone, "
            "including Amazon customer service."
        ),
        bg_color=(245, 250, 255),
        header_color=(25, 35, 55),
    )

    # 3. Genuine Food Delivery Order Update
    make_sms_screenshot(
        "safe_swiggy_delivery.png",
        sender="AD-SWIGGY",
        message=(
            "Your Swiggy order #982341 has been picked up by delivery partner Suresh. "
            "Delivery OTP is 4192. Please share OTP only at your doorstep on delivery."
        ),
        bg_color=(255, 250, 245),
        header_color=(252, 128, 25),
    )

    # 4. Genuine IRCTC Train Ticket Confirmation
    make_sms_screenshot(
        "safe_irctc_ticket.png",
        sender="IRCTC",
        message=(
            "PNR: 8421098432, Train: 12952 / Rajdhani Exp, Date: 05-Oct-26, "
            "Class: 3A, Coach: B3 Berth: 24 (Confirmed). "
            "Happy Journey from IRCTC. Visit www.irctc.co.in"
        ),
        bg_color=(245, 248, 255),
        header_color=(180, 40, 40),
    )

    # ── SCAM / FRAUD SAMPLES ──────────────────────────────────────────────────

    # 5. Fake SBI KYC Scam
    make_sms_screenshot(
        "kyc_scam.png",
        sender="SBI-ALERT",
        message=(
            "URGENT: Your SBI account will be BLOCKED in 24 hours due to incomplete KYC. "
            "Update NOW to avoid suspension: bit.ly/sbi-kyc-update "
            "Enter OTP to verify. Helpline: 9876543210"
        ),
        header_color=(0, 100, 0),
    )

    # 6. Lottery Scam
    make_sms_screenshot(
        "lottery_scam.png",
        sender="+44 7911 123456",
        message=(
            "CONGRATULATIONS! You have won Rs 50,00,000 in the Google Lucky Draw! "
            "To claim your prize, pay Rs 5,000 processing fee to: "
            "UPI: lottery@paytm | Reference: GWIN2026 | Call: 9123456789"
        ),
        header_color=(255, 140, 0),
    )

    # 7. UPI Phishing
    make_sms_screenshot(
        "upi_phishing.png",
        sender="GP-ALERT",
        message=(
            "Your Google Pay account shows suspicious activity. "
            "Verify identity immediately or account gets blocked. "
            "Click: gpay-verify-india.com/secure Login with your UPI PIN."
        ),
        header_color=(66, 133, 244),
    )

    # 8. Job Scam
    make_sms_screenshot(
        "job_scam.png",
        sender="HR-HIRING",
        message=(
            "Work from Home! Earn Rs 50,000/month. No experience needed. "
            "Just like/share social media posts 2 hrs/day. "
            "Registration fee Rs 999 only. WhatsApp: 8765432109"
        ),
        header_color=(75, 0, 130),
    )

    # 9. Government Impersonation
    make_sms_screenshot(
        "govt_impersonation.png",
        sender="TRAI-INDIA",
        message=(
            "TRAI NOTICE: Your mobile number +91-XXXXXXXXXX will be disconnected "
            "in 2 hours due to illegal activity. Press 9 to connect with "
            "Cyber Crime Officer. Case No: CC/2026/8823"
        ),
        header_color=(0, 0, 139),
    )

    print(f"\nDone! {len(list(SAMPLES_DIR.glob('*.png')))} samples generated.")


if __name__ == "__main__":
    generate_all_samples()
