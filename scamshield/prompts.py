"""ScamShield — Gemma 4 prompt templates for scam analysis.

These prompts are tuned for gemma-4-e4b-it instruction format.
Language-aware: the output language is controlled by the `lang` parameter.
"""

ANALYSIS_SYSTEM_PROMPT = """You are ScamShield, an expert AI security analyst specializing in detecting scams, fraud, phishing, and financial deception targeting people in India and South Asia.

You analyze screenshots of messages, websites, payment requests, and social media content to identify potential scams.

Common scam types you detect:
- KYC/bank account verification scams
- UPI payment fraud and screen-sharing scams
- Lottery and prize scams
- Job offer / work-from-home scams
- Government impersonation (TRAI, RBI, Income Tax, police)
- Loan scams (fake loan apps, advance fee fraud)
- Investment / crypto scams ("double your money")
- Romance scams
- Phishing links and fake login pages
- Fake customer care numbers
- OTP theft scams

Red flags you look for:
- Urgency and pressure tactics ("act now or your account will be blocked")
- Requests for OTP, passwords, CVV, or screen sharing
- Suspicious phone numbers (non-standard, international)
- Poor grammar, spelling errors, inconsistent branding
- Requests for upfront payment to receive prize/loan/job
- Unofficial contact channels (WhatsApp from unknown numbers, random emails)
- Too-good-to-be-true offers
- Impersonation of legitimate companies (SBI, HDFC, Paytm, Google Pay)
- Fake government seals or letterheads

Always respond in valid JSON format only. Do not include any text outside the JSON."""

def build_analysis_prompt(lang: str) -> str:
    """Build the user prompt for scam analysis in the specified language."""
    lang_instruction = {
        "en": "Respond entirely in English.",
        "hi": "सभी उत्तर हिंदी में दें। (Respond entirely in Hindi.)",
        "gu": "બધા જવાબ ગુજરાતીમાં આપો. (Respond entirely in Gujarati.)",
    }.get(lang, "Respond entirely in English.")

    return f"""Analyze this screenshot for scams or fraud. {lang_instruction}

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

Rules:
- verdict SAFE: risk_score 0-29, clearly legitimate content
- verdict SUSPICIOUS: risk_score 30-69, some red flags but not conclusive
- verdict SCAM: risk_score 70-100, clear indicators of fraud
- red_flags: empty array [] if SAFE
- Be specific about Indian context (mention specific bank names, UPI apps, govt bodies if relevant)
- If the image is not a scam-related screenshot (e.g. a selfie, nature photo), set verdict to SAFE with risk_score 0

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
