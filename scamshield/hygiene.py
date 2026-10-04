"""ScamShield — Digital Security Hygiene Assessment Engine.

Provides 20 actionable security hygiene checkpoints across 5 critical vectors
(UPI Safety, SIM & Telecom, App Security, Net Banking, Device Hardening)
and evaluates user digital defense readiness with personalized recommendations.
"""

from __future__ import annotations

HYGIENE_CHECKS: list[dict] = [
    # ── UPI Safety ────────────────────────────────────────────────────────────
    {
        "id": "upi_pin_private",
        "category": "UPI Safety",
        "weight": 10,
        "title_en": "UPI PIN is never entered to receive money",
        "title_hi": "पैसे प्राप्त करने के लिए कभी UPI PIN दर्ज नहीं करते",
        "desc_en": "You know that entering your UPI PIN only debits money and never credits.",
        "desc_hi": "आपको पता है कि UPI PIN डालने से सिर्फ पैसे कटते हैं, आते नहीं।",
        "tip": "Remember: Receiving cashback, refunds, or payments never asks for PIN.",
    },
    {
        "id": "upi_app_lock",
        "category": "UPI Safety",
        "weight": 5,
        "title_en": "UPI apps locked with biometric / distinct app lock",
        "title_hi": "UPI ऐप्स बायोमेट्रिक या अलग ऐप लॉक से सुरक्षित हैं",
        "desc_en": "PhonePe, GPay, Paytm have distinct app passcode or fingerprint lock enabled.",
        "desc_hi": "PhonePe, GPay, Paytm में फिंगरप्रिंट या अलग पासकोड चालू है।",
        "tip": "Enable app lock in your payment app settings to prevent unauthorized local use.",
    },
    {
        "id": "upi_daily_limit",
        "category": "UPI Safety",
        "weight": 5,
        "title_en": "Set sensible daily UPI transaction limits",
        "title_hi": "दैनिक UPI ट्रांजेक्शन सीमा निर्धारित की हुई है",
        "desc_en": "Reduced daily limit (e.g., ₹10,000 to ₹25,000) configured in bank app to cap fraud loss.",
        "desc_hi": "बैंक ऐप में रोज की सीमा तय है ताकि धोखाधड़ी में बड़ा नुकसान न हो।",
        "tip": "Log into your net banking and lower daily UPI limits from default ₹1,00,000.",
    },

    # ── SIM & Telecom Security ────────────────────────────────────────────────
    {
        "id": "trai_dnd_active",
        "category": "SIM Security",
        "weight": 5,
        "title_en": "TRAI DND (Do Not Disturb) fully activated",
        "title_hi": "TRAI DND (डू नॉट डिस्टर्ब) पूर्ण रूप से सक्रिय है",
        "desc_en": "Registered on National Customer Preference Register (SMS 'START 0' to 1909).",
        "desc_hi": "1909 पर 'START 0' SMS करके अनचाही कॉल्स बंद कराई हुई हैं।",
        "tip": "Send 'START 0' to 1909 to block all commercial telemarketing calls.",
    },
    {
        "id": "sim_pin_lock",
        "category": "SIM Security",
        "weight": 5,
        "title_en": "SIM card protected with a custom SIM PIN",
        "title_hi": "SIM कार्ड पर कस्टम SIM PIN लॉक लगा है",
        "desc_en": "Prevents unauthorized use if your physical SIM is stolen or put in another phone.",
        "desc_hi": "SIM चोरी होने पर दूसरे फोन में बिना PIN के इस्तेमाल नहीं हो सकता।",
        "tip": "Enable SIM PIN Lock in phone Security Settings (change default 0000/1234).",
    },
    {
        "id": "esim_carrier_pin",
        "category": "SIM Security",
        "weight": 5,
        "title_en": "Carrier 2FA enabled against fraudulent SIM swap",
        "title_hi": "SIM स्वैप से बचाव के लिए टेलीकॉम ऑपरेटर पर सुरक्षा सक्रिय है",
        "desc_en": "Account password/security questions set with Jio/Airtel/Vi customer care.",
        "desc_hi": "Jio/Airtel/Vi में सिम पोर्ट या रिप्लेसमेंट के लिए सुरक्षा पासकोड है।",
        "tip": "Never share SIM swap/porting SMS confirmation codes with any caller.",
    },

    # ── App & Download Security ───────────────────────────────────────────────
    {
        "id": "no_remote_apps",
        "category": "App Security",
        "weight": 10,
        "title_en": "No remote screen-sharing apps installed (AnyDesk, TeamViewer)",
        "title_hi": "फोन में कोई रिमोट स्क्रीन शेयरिंग ऐप नहीं है (AnyDesk, TeamViewer)",
        "desc_en": "Unused remote desktop or diagnostic apps are completely uninstalled from phone.",
        "desc_hi": "AnyDesk, RustDesk जैसी ऐप्स फोन से हटा दी गई हैं।",
        "tip": "Uninstall AnyDesk/RustDesk immediately unless actively required for IT work.",
    },
    {
        "id": "no_sideload_apk",
        "category": "App Security",
        "weight": 10,
        "title_en": "Never install .APK files received via WhatsApp / Telegram / SMS",
        "title_hi": "WhatsApp या SMS पर आए .APK कभी इंस्टॉल नहीं करते",
        "desc_en": "'Install unknown apps' toggle disabled in Android developer/security settings.",
        "desc_hi": "अज्ञात स्रोतों से ऐप इंस्टॉल करने की सेटिंग बंद है।",
        "tip": "Always install banking and utility apps strictly from Google Play Store or Apple App Store.",
    },
    {
        "id": "google_play_protect",
        "category": "App Security",
        "weight": 5,
        "title_en": "Google Play Protect / iOS app security verified active",
        "title_hi": "Google Play Protect सक्रिय है और हाल ही में स्कैन हुआ है",
        "desc_en": "Play Protect scans apps for harmful behavior and sideloaded spyware.",
        "desc_hi": "Play Protect चालू है और ऐप्स को हानिकारक कोड के लिए स्कैन करता है।",
        "tip": "Open Play Store > Profile > Play Protect > Scan to ensure clean status.",
    },

    # ── Net Banking & Account Defense ─────────────────────────────────────────
    {
        "id": "unique_passwords",
        "category": "Account Security",
        "weight": 5,
        "title_en": "Unique passwords across banking and email accounts",
        "title_hi": "बैंक और ईमेल के लिए अलग-अलग मजबूत पासवर्ड",
        "desc_en": "Net banking password is not reused for social media, shopping, or food apps.",
        "desc_hi": "नेट बैंकिंग पासवर्ड किसी अन्य वेबसाइट पर दोहराया नहीं गया है।",
        "tip": "Use a trusted password manager (e.g., Bitwarden) for generating 16+ char passwords.",
    },
    {
        "id": "two_factor_auth",
        "category": "Account Security",
        "weight": 10,
        "title_en": "2-Factor Authentication (2FA) active on primary email",
        "title_hi": "मुख्य ईमेल पर 2-फैक्टर ऑथेंटिकेशन (2FA) सक्रिय है",
        "desc_en": "Google/Apple/Microsoft account uses Authenticator app or security keys for login.",
        "desc_hi": "ईमेल पर ऑथेंटिकेटर ऐप या OTP से 2-स्टेप वेरिफिकेशन चालू है।",
        "tip": "Protect your primary Gmail/iCloud account — it receives your bank recovery links.",
    },
    {
        "id": "sms_email_alerts",
        "category": "Account Security",
        "weight": 5,
        "title_en": "Instant SMS & Email transaction alerts subscribed with bank",
        "title_hi": "बैंक के साथ तुरंत SMS और ईमेल अलर्ट सक्रिय हैं",
        "desc_en": "Notified instantly for every debit of even ₹1 to detect unauthorized transactions early.",
        "desc_hi": "₹1 के भी लेनदेन पर तुरंत मैसेज और ईमेल आता है।",
        "tip": "Check your net banking profile to ensure both mobile and email are updated.",
    },
    {
        "id": "card_international_disabled",
        "category": "Account Security",
        "weight": 5,
        "title_en": "International and online card transactions disabled when not in use",
        "title_hi": "क्रेडिट/डेबिट कार्ड पर अंतर्राष्ट्रीय व ऑनलाइन सीमा नियंत्रित है",
        "desc_en": "E-commerce and international POS usage switched off via bank app card controls.",
        "desc_hi": "बैंक ऐप से जरूरत न होने पर इंटरनेशनल और ऑनलाइन पेमेंट बंद रखी है।",
        "tip": "Turn off international usage on debit/credit cards in your bank app to block dark-web leaks.",
    },

    # ── Device & OS Hardening ─────────────────────────────────────────────────
    {
        "id": "os_updated",
        "category": "Device Security",
        "weight": 5,
        "title_en": "Operating system and security patches up to date",
        "title_hi": "फोन का ऑपरेटिंग सिस्टम और सुरक्षा पैच अपडेटेड हैं",
        "desc_en": "Phone is running recent Android/iOS security patch without pending updates.",
        "desc_hi": "फोन में नवीनतम सॉफ्टवेयर अपडेट इंस्टॉल है।",
        "tip": "Go to Settings > System Update and install latest security fixes.",
    },
    {
        "id": "screen_lock_short",
        "category": "Device Security",
        "weight": 5,
        "title_en": "Auto-lock timeout set to 1 minute or less",
        "title_hi": "ऑटो-स्क्रीन लॉक 1 मिनट या उससे कम पर सेट है",
        "desc_en": "Device locks quickly when unattended to prevent unauthorized physical access.",
        "desc_hi": "फोन छूट जाने पर तुरंत लॉक हो जाता है।",
        "tip": "Set display sleep to 30s or 1 min in Settings > Display.",
    },
    {
        "id": "hide_lockscreen_otps",
        "category": "Device Security",
        "weight": 5,
        "title_en": "Lock screen hides sensitive notification / OTP contents",
        "title_hi": "लॉक स्क्रीन पर OTP और बैंक मैसेज का कंटेंट छिपा हुआ है",
        "desc_en": "Notifications show sender only, hiding the OTP code on locked screen.",
        "desc_hi": "फोन लॉक होने पर OTP कोड स्क्रीन पर नहीं दिखता।",
        "tip": "Settings > Notifications > 'Hide sensitive content on lock screen'.",
    },

    # ── Behavioral Vigilance ──────────────────────────────────────────────────
    {
        "id": "family_safe_word",
        "category": "Vigilance",
        "weight": 5,
        "title_en": "Established a family safe-word for emergency calls",
        "title_hi": "परिवार में आपातकालीन कॉल के लिए एक सीक्रेट कोड वर्ड तय है",
        "desc_en": "Agreed secret phrase to verify calls against AI voice clones / digital arrest traps.",
        "desc_hi": "वॉयस क्लोनिंग कॉल से बचने के लिए परिवार में गुप्त कोड वर्ड तय है।",
        "tip": "Agree on a random phrase with parents/children to test any distress call claiming arrest.",
    },
    {
        "id": "callback_rule_used",
        "category": "Vigilance",
        "weight": 5,
        "title_en": "Follow the 'Hang Up and Call Back' rule on authority calls",
        "title_hi": "अधिकारी बनकर आई कॉल पर फोन काटकर वापस करने का नियम अपनाते हैं",
        "desc_en": "Never stay on calls from claimed police/CBI/courier; hang up and call official number.",
        "desc_hi": "CBI/पुलिस के नाम पर आई कॉल काटकर आधिकारिक नंबर पर खुद कॉल करते हैं।",
        "tip": "Hang up immediately on any WhatsApp video call claiming legal arrest.",
    },
    {
        "id": "helpline_saved",
        "category": "Vigilance",
        "weight": 5,
        "title_en": "1930 Cyber Helpline and Bank Fraud Number saved in contacts",
        "title_hi": "1930 साइबर हेल्पलाइन और बैंक नंबर कॉन्टैक्ट्स में सेव है",
        "desc_en": "Quick access during golden hour panic saves crucial minutes.",
        "desc_hi": "आपात स्थिति में बिना समय गंवाए तुरंत कॉल करने के लिए नंबर सेव है।",
        "tip": "Save 1930 as '🚨 Cyber Cell Emergency' in your phone right now.",
    },
]


def calculate_hygiene_score(checked_ids: list[str]) -> dict:
    """Calculate overall security hygiene rating and identify weak spots."""
    checked_set = set(checked_ids or [])
    total_possible = sum(c["weight"] for c in HYGIENE_CHECKS)
    earned = sum(c["weight"] for c in HYGIENE_CHECKS if c["id"] in checked_set)

    percentage = round((earned / total_possible) * 100) if total_possible else 0

    if percentage >= 90:
        grade = "A+"
        title = "Cyber Fortress"
        color = "#10b981"
        summary = "Exceptional digital security! You follow best-in-class defense practices."
    elif percentage >= 75:
        grade = "A"
        title = "Hardened Defense"
        color = "#00ff88"
        summary = "Strong security posture with only minor optimizations needed."
    elif percentage >= 60:
        grade = "B"
        title = "Moderate Vigilance"
        color = "#38bdf8"
        summary = "Decent protection, but key vulnerabilities could be targeted by scammers."
    elif percentage >= 40:
        grade = "C"
        title = "Vulnerable Target"
        color = "#f59e0b"
        summary = "Critical gaps detected in your defense. Follow high-priority tips below."
    else:
        grade = "F"
        title = "High Risk Exposure"
        color = "#ef4444"
        summary = "Immediate action needed! Multiple high-risk vectors leave you exposed to fraud."

    # Identify missing items
    missing = [c for c in HYGIENE_CHECKS if c["id"] not in checked_set]
    missing.sort(key=lambda x: x["weight"], reverse=True)

    recommendations = [
        {
            "id": m["id"],
            "category": m["category"],
            "title": m["title_en"],
            "tip": m["tip"],
            "weight": m["weight"],
        }
        for m in missing[:5]
    ]

    return {
        "score": percentage,
        "grade": grade,
        "title": title,
        "color": color,
        "summary": summary,
        "checked_count": len(checked_set),
        "total_checks": len(HYGIENE_CHECKS),
        "recommendations": recommendations,
    }
