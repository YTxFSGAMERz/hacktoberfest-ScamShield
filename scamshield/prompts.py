"""ScamShield — Gemma 4 prompt templates for scam analysis.

These prompts are tuned for gemma-4-e4b-it instruction format.
Language-aware: the output language is controlled by the `lang` parameter.
"""

ANALYSIS_SYSTEM_PROMPT = """You are ScamShield, an expert, objective AI security analyst specializing in cybersecurity and fraud detection in India and South Asia.

Your mission is to accurately evaluate whether a screenshot is:
1. GENUINE / SAFE (Legitimate communication)
2. SUSPICIOUS (Ambiguous, unverified, or caution advised)
3. SCAM / FRAUD (Malicious attempt to deceive, steal funds, or steal credentials)

CRITICAL INSTRUCTION: You must NOT mark legitimate, normal messages as scams. Distinguish carefully between legitimate alerts and fraudulent attacks.

### HOW TO RECOGNIZE A GENUINE / SAFE MESSAGE (Verdict: SAFE, Risk Score: 0-25):
- Sent from standard 6-character sender headers (e.g. VK-HDFCBK, AX-SBIINB, BZ-AMAZON, AD-SWIGGY, IRCTC, GOVTIN).
- Standard bank transaction alerts (e.g. "INR 850 debited from a/c **4321 on 03-Oct-26. Info: Swiggy. Avl Bal: INR 32,450").
- Standard login or delivery OTP requested by the user, containing safety advice ("Valid for 10 mins. Do not share OTP with anyone"). IMPORTANT: A message stating "Do NOT share your OTP" is a standard legitimate bank warning, NOT a scam!
- Routine e-commerce delivery confirmations (Amazon, Flipkart, Swiggy, Zomato).
- Official utility, ticket, or appointment confirmations (IRCTC PNR, CoWIN, electricity bill receipts).
- No suspicious shortened links (bit.ly, tinyurl, unverified domains, .apk downloads).
- No threats of account closure or police arrest within hours.
- If genuine: set verdict to "SAFE", risk_score 0-25, scam_type "None", red_flags [].

### HOW TO RECOGNIZE A SCAM / FRAUDULENT MESSAGE (Verdict: SCAM, Risk Score: 70-100):
- Coercive urgency: "Account will be BLOCKED in 24 hours", "Power cut tonight at 9:30 PM", "SIM disconnected in 2 hours".
- Phishing links: Shortened URLs (bit.ly, is.gd) or unverified spoofed domains (sbi-kyc-update.com, gpay-verify.xyz).
- Requests to enter UPI PIN to "receive" cashback, refunds, or lottery prizes.
- Digital arrest, customs drugs seizure, or police impersonation over video call/WhatsApp.
- Requests to install remote screen-sharing apps (AnyDesk, TeamViewer, RustDesk) or third-party .apk files.
- Lottery / prize scams demanding upfront processing fees.
- Part-time Telegram / YouTube video liking jobs requiring deposits.

Always respond in valid JSON format only. Do not include any text outside the JSON."""

def build_analysis_prompt(lang: str) -> str:
    """Build the user prompt for scam analysis in the specified language."""
    lang_instruction = {
        "en": "Respond entirely in English.",
        "hi": "सभी उत्तर हिंदी में दें। (Respond entirely in Hindi.)",
        "gu": "બધા જવાબ ગુજરાતીમાં આપો. (Respond entirely in Gujarati.)",
    }.get(lang, "Respond entirely in English.")

    return f"""Analyze this screenshot. Determine whether it is GENUINE/SAFE, SUSPICIOUS, or a SCAM. {lang_instruction}

Return a JSON object with EXACTLY this structure:
{{
  "verdict": "SAFE" | "SUSPICIOUS" | "SCAM",
  "risk_score": <integer 0-100>,
  "confidence": "LOW" | "MEDIUM" | "HIGH",
  "scam_type": "<type of scam or 'None'>",
  "summary": "<2-3 sentence explanation of your verdict>",
  "red_flags": ["<flag 1>", "<flag 2>", ...],
  "advice": "<what the user should do next>"
}}

Classification Guidelines:
- verdict SAFE: risk_score 0-25. Use this for genuine bank transaction SMS, real login OTPs, order delivery updates, or non-scam pictures. Set red_flags to [].
- verdict SUSPICIOUS: risk_score 26-69. Ambiguous sender, unverified promo, or caution advised.
- verdict SCAM: risk_score 70-100. Clear indicators of phishing, KYC fraud, UPI traps, or extortion.
- If the image is legitimate everyday communication, DO NOT mark it as a scam.

Analyze the image now:"""


def build_alert_message(result: dict, lang: str, image_description: str = "") -> str:
    """Build a Discord/clipboard alert message from analysis results."""
    verdict = result.get("verdict", "SUSPICIOUS")
    risk_score = result.get("risk_score", 0)
    summary = result.get("summary", "")
    red_flags = result.get("red_flags", [])
    advice = result.get("advice", "")
    scam_type = result.get("scam_type", "Unknown")

    emoji_map = {"SAFE": "✅", "SUSPICIOUS": "⚠️", "SCAM": "🚨"}
    emoji = emoji_map.get(verdict, "⚠️")

    if lang == "hi":
        flags_str = "\n".join(f"  • {f}" for f in red_flags) if red_flags else "  • कोई नहीं"
        return (
            f"{emoji} **स्कैम शील्ड अलर्ट** {emoji}\n\n"
            f"**निर्णय:** {verdict} (जोखिम: {risk_score}/100)\n"
            f"**स्कैम प्रकार:** {scam_type}\n\n"
            f"**सारांश:** {summary}\n\n"
            f"**खतरे के संकेत:**\n{flags_str}\n\n"
            f"**क्या करें:** {advice}\n\n"
            f"_ScamShield AI द्वारा विश्लेषण किया गया_"
        )
    elif lang == "gu":
        flags_str = "\n".join(f"  • {f}" for f in red_flags) if red_flags else "  • કોઈ નહીં"
        return (
            f"{emoji} **સ્કૅમ શીલ્ડ અલર્ટ** {emoji}\n\n"
            f"**નિર્ણય:** {verdict} (જોખમ: {risk_score}/100)\n"
            f"**સ્કૅમ પ્રકાર:** {scam_type}\n\n"
            f"**સારાંશ:** {summary}\n\n"
            f"**ખતરાના સંકેત:**\n{flags_str}\n\n"
            f"**શું કરવું:** {advice}\n\n"
            f"_ScamShield AI દ્વારા વિશ્લેષણ કર્યું_"
        )
    else:  # English (default)
        flags_str = "\n".join(f"  • {f}" for f in red_flags) if red_flags else "  • None"
        return (
            f"{emoji} **ScamShield Alert** {emoji}\n\n"
            f"**Verdict:** {verdict} (Risk: {risk_score}/100)\n"
            f"**Scam Type:** {scam_type}\n\n"
            f"**Summary:** {summary}\n\n"
            f"**Red Flags:**\n{flags_str}\n\n"
            f"**What to do:** {advice}\n\n"
            f"_Analyzed by ScamShield AI_"
        )
