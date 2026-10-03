"""ScamShield — Internationalization (i18n) strings.

Supported languages: English (en), Hindi (hi), Gujarati (gu)
"""

STRINGS: dict[str, dict[str, str]] = {
    "en": {
        # App metadata
        "app_title": "🛡️ ScamShield",
        "app_subtitle": "AI-powered scam detection — Powered by Gemma 4",
        "app_tagline": "Upload a suspicious screenshot and get an instant risk analysis.",

        # Language selector
        "select_language": "Language / भाषा / ભાષા",

        # Upload section
        "upload_header": "📤 Upload Screenshot",
        "upload_prompt": "Upload a screenshot of a suspicious message, call, website, or payment request.",
        "upload_button_label": "Choose image...",
        "upload_types": "JPG, PNG, WEBP — max 10 MB",

        # Analysis section
        "analyze_button": "🔍 Analyze for Scams",
        "analyzing": "Analyzing with Gemma 4...",
        "analysis_result": "📊 Analysis Result",

        # Verdict labels
        "verdict_safe": "✅ SAFE",
        "verdict_suspicious": "⚠️ SUSPICIOUS",
        "verdict_scam": "🚨 SCAM",

        # Result fields
        "risk_score": "Risk Score",
        "summary": "Summary",
        "red_flags": "Red Flags Detected",
        "advice": "What to Do",
        "scam_type": "Scam Type",
        "confidence": "Confidence",

        # Alert section
        "alert_header": "🚨 Alert Family Members",
        "alert_button": "📢 Send Alert to Family",
        "alert_sent": "✅ Alert sent to Discord!",
        "alert_copied": "📋 Alert copied to clipboard — paste it in your family group!",
        "alert_failed": "❌ Failed to send alert. Alert text copied to clipboard instead.",
        "alert_no_result": "Please analyze an image first before sending an alert.",

        # Provider info
        "provider_gemini": "🌐 Using Gemini API (gemma-4-e4b-it)",
        "provider_ollama": "🖥️ Using Local Ollama (gemma4:e4b)",
        "provider_error": "❌ No AI provider available. Check your .env configuration.",

        # Errors
        "error_no_image": "Please upload an image first.",
        "error_analysis_failed": "Analysis failed. Please try again.",
        "error_image_too_large": "Image is too large. Please upload an image under 10 MB.",
        "error_invalid_image": "Invalid image file. Please upload a JPG, PNG, or WEBP image.",

        # Footer
        "footer": "ScamShield v1.0 • MIT License • Built for Hacktoberfest 2026",
        "disclaimer": "⚠️ This tool is for educational purposes. Always verify with official sources before taking action.",
    },

    "hi": {
        # App metadata
        "app_title": "🛡️ स्कैम शील्ड",
        "app_subtitle": "AI-आधारित स्कैम पहचान — Gemma 4 द्वारा संचालित",
        "app_tagline": "संदिग्ध स्क्रीनशॉट अपलोड करें और तुरंत जोखिम विश्लेषण प्राप्त करें।",

        # Language selector
        "select_language": "Language / भाषा / ભાષા",

        # Upload section
        "upload_header": "📤 स्क्रीनशॉट अपलोड करें",
        "upload_prompt": "किसी संदिग्ध संदेश, कॉल, वेबसाइट या भुगतान अनुरोध का स्क्रीनशॉट अपलोड करें।",
        "upload_button_label": "छवि चुनें...",
        "upload_types": "JPG, PNG, WEBP — अधिकतम 10 MB",

        # Analysis section
        "analyze_button": "🔍 स्कैम के लिए विश्लेषण करें",
        "analyzing": "Gemma 4 से विश्लेषण हो रहा है...",
        "analysis_result": "📊 विश्लेषण परिणाम",

        # Verdict labels
        "verdict_safe": "✅ सुरक्षित",
        "verdict_suspicious": "⚠️ संदिग्ध",
        "verdict_scam": "🚨 स्कैम",

        # Result fields
        "risk_score": "जोखिम स्कोर",
        "summary": "सारांश",
        "red_flags": "पहचाने गए खतरे",
        "advice": "क्या करें",
        "scam_type": "स्कैम का प्रकार",
        "confidence": "विश्वास स्तर",

        # Alert section
        "alert_header": "🚨 परिवार को सचेत करें",
        "alert_button": "📢 परिवार को अलर्ट भेजें",
        "alert_sent": "✅ Discord पर अलर्ट भेज दिया गया!",
        "alert_copied": "📋 अलर्ट क्लिपबोर्ड पर कॉपी हो गया — इसे अपने परिवार के ग्रुप में पेस्ट करें!",
        "alert_failed": "❌ अलर्ट भेजने में विफल। अलर्ट टेक्स्ट क्लिपबोर्ड पर कॉपी किया गया।",
        "alert_no_result": "अलर्ट भेजने से पहले कृपया पहले किसी छवि का विश्लेषण करें।",

        # Provider info
        "provider_gemini": "🌐 Gemini API उपयोग हो रहा है (gemma-4-e4b-it)",
        "provider_ollama": "🖥️ स्थानीय Ollama उपयोग हो रहा है (gemma4:e4b)",
        "provider_error": "❌ कोई AI प्रदाता उपलब्ध नहीं। अपनी .env कॉन्फ़िगरेशन जांचें।",

        # Errors
        "error_no_image": "कृपया पहले एक छवि अपलोड करें।",
        "error_analysis_failed": "विश्लेषण विफल रहा। कृपया पुनः प्रयास करें।",
        "error_image_too_large": "छवि बहुत बड़ी है। कृपया 10 MB से कम की छवि अपलोड करें।",
        "error_invalid_image": "अमान्य छवि फ़ाइल। कृपया JPG, PNG, या WEBP छवि अपलोड करें।",

        # Footer
        "footer": "ScamShield v1.0 • MIT लाइसेंस • Hacktoberfest 2026 के लिए बनाया गया",
        "disclaimer": "⚠️ यह उपकरण शैक्षिक उद्देश्यों के लिए है। कार्रवाई करने से पहले हमेशा आधिकारिक स्रोतों से सत्यापित करें।",
    },

    "gu": {
        # App metadata
        "app_title": "🛡️ સ્કૅમ શીલ્ડ",
        "app_subtitle": "AI-આધારિત સ્કૅમ શોધ — Gemma 4 દ્વારા સંચાલિત",
        "app_tagline": "શંકાસ્પદ સ્ક્રીનશૉટ અપલોડ કરો અને તાત્કાલિક જોખમ વિશ્લેષણ મેળવો.",

        # Language selector
        "select_language": "Language / भाषा / ભાષા",

        # Upload section
        "upload_header": "📤 સ્ક્રીનશૉટ અપલોડ કરો",
        "upload_prompt": "શંકાસ્પદ સંદેશ, કૉલ, વેબસાઇટ અથવા ચૂકવણી વિનંતીનો સ્ક્રીનશૉટ અપલોડ કરો.",
        "upload_button_label": "છબી પસંદ કરો...",
        "upload_types": "JPG, PNG, WEBP — મહત્તમ 10 MB",

        # Analysis section
        "analyze_button": "🔍 સ્કૅમ માટે વિશ્લેષણ કરો",
        "analyzing": "Gemma 4 સાથે વિશ્લેષણ થઈ રહ્યું છે...",
        "analysis_result": "📊 વિશ્લેષણ પરિણામ",

        # Verdict labels
        "verdict_safe": "✅ સુરક્ષિત",
        "verdict_suspicious": "⚠️ શંકાસ્પદ",
        "verdict_scam": "🚨 સ્કૅમ",

        # Result fields
        "risk_score": "જોખમ સ્કોર",
        "summary": "સારાંશ",
        "red_flags": "શોધાયેલ ખતરા",
        "advice": "શું કરવું",
        "scam_type": "સ્કૅમ પ્રકાર",
        "confidence": "વિશ્વસનીયતા",

        # Alert section
        "alert_header": "🚨 પરિવારને સચેત કરો",
        "alert_button": "📢 પરિવારને અલર્ટ મોકલો",
        "alert_sent": "✅ Discord પર અલર્ટ મોકલ્યો!",
        "alert_copied": "📋 અલર્ટ ક્લિપબોર્ડ પર કૉપિ થયો — તમારા કૌટુંબિક જૂથમાં પેસ્ટ કરો!",
        "alert_failed": "❌ અલર્ટ મોકલવામાં નિષ્ફળ. અલર્ટ ટેક્સ્ટ ક્લિપબોર્ડ પર કૉપિ થયો.",
        "alert_no_result": "અલર્ટ મોકલ્યા પહેલા કૃપા કરીને પ્રથમ છબી વિશ્લેષણ કરો.",

        # Provider info
        "provider_gemini": "🌐 Gemini API ઉપયોગ થઈ રહ્યો છે (gemma-4-e4b-it)",
        "provider_ollama": "🖥️ સ્થાનિક Ollama ઉપયોગ થઈ રહ્યો છે (gemma4:e4b)",
        "provider_error": "❌ કોઈ AI પ્રદાતા ઉપલબ્ધ નથી. તમારી .env ગોઠવણી તપાસો.",

        # Errors
        "error_no_image": "કૃપા કરીને પ્રથમ છબી અપલોડ કરો.",
        "error_analysis_failed": "વિશ્લેષણ નિષ્ફળ થયું. કૃપા કરી ફરી પ્રયાસ કરો.",
        "error_image_too_large": "છબી ખૂબ મોટી છે. કૃપા 10 MB થી ઓછી છબી અપલોડ કરો.",
        "error_invalid_image": "અમાન્ય છબી ફાઇલ. કૃપા JPG, PNG, અથવા WEBP છબી અપલોડ કરો.",

        # Footer
        "footer": "ScamShield v1.0 • MIT લાઇસન્સ • Hacktoberfest 2026 માટે બનાવ્યું",
        "disclaimer": "⚠️ આ સાધન શૈક્ષણિક હેતુઓ માટે છે. પગલાં ભરતા પહેલા હંમેશા સત્તાવાર સ્રોતોથી ચકાસો.",
    },
}


def get_string(lang: str, key: str) -> str:
    """Get a localized string for the given language and key.
    Falls back to English if key is not found in the target language.
    """
    lang = lang if lang in STRINGS else "en"
    return STRINGS[lang].get(key) or STRINGS["en"].get(key, key)
