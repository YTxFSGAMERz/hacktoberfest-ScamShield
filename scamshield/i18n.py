"""ScamShield — Internationalization (i18n) strings.

Supported languages: English (en), Hindi (hi), Gujarati (gu)
"""

from __future__ import annotations

SUPPORTED_LANGUAGES: dict[str, str] = {
    "en": "English",
    "hi": "हिंदी (Hindi)",
    "gu": "ગુજરાતી (Gujarati)",
    "ta": "தமிழ் (Tamil)",
    "te": "తెలుగు (Telugu)",
    "bn": "বাংলা (Bengali)",
    "mr": "मराठी (Marathi)",
    "kn": "ಕನ್ನಡ (Kannada)",
    "ml": "മലയാളം (Malayalam)",
    "pa": "ਪੰਜਾਬੀ (Punjabi)",
    "ur": "اردو (Urdu)",
    "or": "ଓଡ଼ିଆ (Odia)",
    "as": "অসমীয়া (Assamese)",
    "es": "Español (Spanish)",
    "fr": "Français (French)",
    "de": "Deutsch (German)",
    "ar": "العربية (Arabic)",
    "pt": "Português (Portuguese)",
    "ru": "Русский (Russian)",
    "ja": "日本語 (Japanese)",
    "ko": "한국어 (Korean)",
    "zh": "中文 (Chinese)",
    "id": "Bahasa Indonesia",
    "tr": "Türkçe (Turkish)",
    "vi": "Tiếng Việt (Vietnamese)",
}

STRINGS: dict[str, dict[str, str]] = {
    "en": {
        # App metadata
        "app_title": "🛡️ ScamShield AI",
        "app_subtitle": "Cyber-Fraud Intelligence & Scam Detection — Powered by Gemma 4",
        "app_tagline": "Upload suspicious screenshots, chat with AI, inspect fraud trends, and protect your family.",

        # Navigation Tabs
        "tab_scanner": "📸 Screenshot Scanner",
        "tab_chat": "💬 AI Safety Chat",
        "tab_intel": "📊 Threat Intelligence",
        "tab_helpline": "🆘 Emergency Helplines",
        "tab_alerts": "🚨 Family Alert Center",

        # Language selector
        "select_language": "Language / भाषा / ભાષા",

        # Quick sample test buttons
        "genuine_samples_title": "✅ Genuine / Legitimate Messages (Test False-Positive Defense):",
        "scam_samples_title": "🚨 Fraudulent / Scam Messages (Test Threat Detection):",
        "sample_safe_bank": "🏦 HDFC Bank Debit Alert",
        "sample_safe_otp": "🔑 Amazon Verification OTP",
        "sample_safe_delivery": "🍔 Swiggy Delivery Status",
        "sample_safe_ticket": "🚆 IRCTC Train Ticket",
        "sample_kyc": "⚠️ Fake SBI KYC SMS",
        "sample_lottery": "🎁 Google Lucky Draw",
        "sample_upi": "💳 UPI PIN Trap",
        "sample_job": "💼 Telegram Job Fraud",
        "sample_govt": "🏛️ TRAI SIM Disconnect",

        # Upload section
        "upload_header": "📤 Upload Suspicious Screenshot",
        "upload_prompt": "Drop an image of an SMS, WhatsApp chat, fake UPI screen, payment request, or APK prompt.",
        "upload_button_label": "Choose image...",
        "upload_types": "JPG, PNG, WEBP — max 10 MB",

        # Analysis section
        "analyze_button": "🔍 Analyze with Gemma 4",
        "analyzing": "Gemma 4 is inspecting signals, OCR text, and fraud patterns...",
        "analysis_result": "📊 ScamShield Risk Verdict",

        # Verdict labels
        "verdict_safe": "✅ SAFE — NO SCAM DETECTED",
        "verdict_suspicious": "⚠️ SUSPICIOUS — PROCEED WITH CAUTION",
        "verdict_scam": "🚨 CRITICAL SCAM DETECTED",

        # Result fields
        "risk_score": "Risk Score",
        "summary": "AI Summary",
        "red_flags": "Identified Fraud Signals",
        "advice": "Recommended Protective Actions",
        "scam_type": "Scam Category",
        "confidence": "AI Confidence",
        "reasoning_expander": "🧠 View Gemma 4 Chain-of-Thought Reasoning",

        # Chat section
        "chat_header": "💬 Chat with ScamShield Assistant",
        "chat_caption": "Ask questions, paste suspicious texts, or inquire about emergency recovery steps.",
        "chat_welcome": "Hello! I am ScamShield AI powered by Gemma 4. Paste any suspicious message, describe a suspicious phone call, or ask how to handle a potential scam.",
        "chat_placeholder": "Type your question or paste a suspicious message here...",
        "chat_send": "Send",
        "chat_clear": "Clear Chat",
        "chat_context_active": "💡 Active Screenshot Context Loaded into Chat",

        # Threat Intel section
        "intel_header": "📊 Current Cyber-Threat Trends (India & South Asia)",
        "intel_caption": "Real-time threat signatures identified by cyber-crime cells and banking fraud units.",
        "golden_hour_header": "⏳ Golden Hour Recovery Protocol (First 60 Minutes)",
        "golden_hour_caption": "If you or someone in your family has transferred money, act immediately:",

        # Alert section
        "alert_header": "🚨 Broadcast Alert to Family Group",
        "alert_button": "📢 Send Alert to Discord Webhook",
        "alert_copy_button": "📋 Copy Formatted Alert to Clipboard",
        "alert_sent": "✅ Family alert successfully dispatched to Discord!",
        "alert_copied": "📋 Formatted alert copied to clipboard! Paste it into your family WhatsApp/Telegram group.",
        "alert_failed": "❌ Discord dispatch failed. Copied to clipboard instead.",
        "alert_no_result": "Please analyze a screenshot first before dispatching an alert.",
        "alert_preview": "Alert Preview (WhatsApp / Discord formatted):",

        # Provider info
        "provider_gemini": "🌐 Primary: Google Gemini Cloud (gemma-4-26b-a4b-it)",
        "provider_ollama": "🖥️ Local Fallback: Ollama (gemma4:e4b)",
        "provider_error": "❌ No AI provider available. Check your .env configuration.",

        # Emergency Banner
        "emergency_banner": "🚨 Scammed? Immediately dial 1930 (Cyber Crime Helpline) or register at cybercrime.gov.in",

        # Errors
        "error_no_image": "Please upload an image first.",
        "error_analysis_failed": "Analysis failed. Please try again.",
        "error_image_too_large": "Image is too large. Please upload an image under 10 MB.",
        "error_invalid_image": "Invalid image file. Please upload a JPG, PNG, or WEBP image.",

        # Footer
        "footer": "ScamShield v1.1 • MIT License • Built for Hacktoberfest 2026",
        "disclaimer": "⚠️ ScamShield provides AI risk assessment for cyber awareness. Always confirm with official bank and government authorities.",
    },

    "hi": {
        # App metadata
        "app_title": "🛡️ स्कैमशील्ड AI",
        "app_subtitle": "साइबर फ्रॉड इंटेलिजेंस एवं स्कैम डिटेक्शन — Gemma 4 द्वारा संचालित",
        "app_tagline": "संदिग्ध स्क्रीनशॉट अपलोड करें, AI से चैट करें, नए फ्रॉड ट्रेंड्स देखें और परिवार की सुरक्षा करें।",

        # Navigation Tabs
        "tab_scanner": "📸 स्क्रीनशॉट स्कैनर",
        "tab_chat": "💬 AI सुरक्षा चैट",
        "tab_intel": "📊 साइबर खतरे और ट्रेंड्स",
        "tab_helpline": "🆘 आपातकालीन हेल्पलाइन",
        "tab_alerts": "🚨 परिवार अलर्ट केंद्र",

        # Language selector
        "select_language": "Language / भाषा / ભાષા",

        # Quick sample test buttons
        "genuine_samples_title": "✅ असली और सुरक्षित संदेश (फॉल्स-पॉजिटिव जांचें):",
        "scam_samples_title": "🚨 प्रमुख फ्रॉड और स्कैम संदेश (पहचान की जांच करें):",
        "sample_safe_bank": "🏦 HDFC बैंक डेबिट अलर्ट",
        "sample_safe_otp": "🔑 अमेज़न वेरिफिकेशन OTP",
        "sample_safe_delivery": "🍔 स्विगी डिलीवरी स्टेटस",
        "sample_safe_ticket": "🚆 IRCTC रेल टिकट",
        "sample_kyc": "⚠️ फर्जी SBI KYC ब्लॉक",
        "sample_lottery": "🎁 गूगल लकी ड्रॉ प्राइज",
        "sample_upi": "💳 UPI पिन का जाल",
        "sample_job": "💼 टेलीग्राम जॉब फ्रॉड",
        "sample_govt": "🏛️ TRAI सिम डिस्कनेक्ट",

        # Upload section
        "upload_header": "📤 संदिग्ध स्क्रीनशॉट अपलोड करें",
        "upload_prompt": "संदिग्ध एसएमएस, व्हाट्सएप चैट, फर्जी UPI स्क्रीन या APK प्रॉम्प्ट का स्क्रीनशॉट यहाँ डालें।",
        "upload_button_label": "छवि चुनें...",
        "upload_types": "JPG, PNG, WEBP — अधिकतम 10 MB",

        # Analysis section
        "analyze_button": "🔍 Gemma 4 से विश्लेषण करें",
        "analyzing": "Gemma 4 संकेतों और फ्रॉड पैटर्न की जाँच कर रहा है...",
        "analysis_result": "📊 स्कैमशील्ड जोखिम निर्णय",

        # Verdict labels
        "verdict_safe": "✅ सुरक्षित — कोई स्कैम नहीं पाया गया",
        "verdict_suspicious": "⚠️ संदिग्ध — अत्यधिक सावधानी बरतें",
        "verdict_scam": "🚨 खतरनाक स्कैम — बिल्कुल भी क्लिक न करें",

        # Result fields
        "risk_score": "जोखिम स्कोर",
        "summary": "AI सारांश",
        "red_flags": "पहचाने गए खतरे के संकेत",
        "advice": "सुरक्षा के लिए क्या करें",
        "scam_type": "स्कैम की श्रेणी",
        "confidence": "विश्वास स्तर",
        "reasoning_expander": "🧠 Gemma 4 की सोच और तर्क प्रक्रिया देखें",

        # Chat section
        "chat_header": "💬 स्कैमशील्ड AI सहायक से बात करें",
        "chat_caption": "सवाल पूछें, संदिग्ध टेक्स्ट पेस्ट करें, या आपातकालीन बचाव उपाय जानें।",
        "chat_welcome": "नमस्ते! मैं Gemma 4 द्वारा संचालित स्कैमशील्ड AI हूँ। कोई भी संदिग्ध संदेश यहाँ पेस्ट करें या फ्रॉड से जुड़े सवाल पूछें।",
        "chat_placeholder": "अपना सवाल लिखें या कोई संदिग्ध संदेश यहाँ पेस्ट करें...",
        "chat_send": "भेजें",
        "chat_clear": "चैट साफ़ करें",
        "chat_context_active": "💡 सक्रिय स्क्रीनशॉट का संदर्भ चैट में शामिल है",

        # Threat Intel section
        "intel_header": "📊 भारत में सक्रिय साइबर फ्रॉड के मुख्य तरीके",
        "intel_caption": "साइबर क्राइम सेल और बैंकिंग सतर्कता इकाइयों द्वारा पहचाने गए पैटर्न।",
        "golden_hour_header": "⏳ गोल्डन ऑवर एक्शन प्रोटोकॉल (पहले 60 मिनट)",
        "golden_hour_caption": "यदि आपके साथ या परिवार में किसी के साथ वित्तीय धोखाधड़ी हुई है, तो तुरंत ये कदम उठाएं:",

        # Alert section
        "alert_header": "🚨 परिवार के ग्रुप में अलर्ट भेजें",
        "alert_button": "📢 Discord वेबहुक पर अलर्ट भेजें",
        "alert_copy_button": "📋 क्लिपबोर्ड पर अलर्ट कॉपी करें",
        "alert_sent": "✅ Discord पर परिवार का अलर्ट सफलतापूर्वक भेज दिया गया!",
        "alert_copied": "📋 अलर्ट कॉपी हो गया! इसे अपने परिवार के व्हाट्सएप/टेलीग्राम ग्रुप में पेस्ट करें।",
        "alert_failed": "❌ अलर्ट भेजने में विफल। टेक्स्ट क्लिपबोर्ड पर कॉपी किया गया।",
        "alert_no_result": "अलर्ट भेजने से पहले कृपया पहले किसी स्क्रीनशॉट का विश्लेषण करें।",
        "alert_preview": "अलर्ट पूर्वावलोकन (व्हाट्सएप/डिस्कॉर्ड प्रारूप):",

        # Provider info
        "provider_gemini": "🌐 प्राथमिक: Google Gemini Cloud (gemma-4-26b-a4b-it)",
        "provider_ollama": "🖥️ स्थानीय बैकअप: Ollama (gemma4:e4b)",
        "provider_error": "❌ कोई AI प्रदाता उपलब्ध नहीं। अपनी .env कॉन्फ़िगरेशन जांचें।",

        # Emergency Banner
        "emergency_banner": "🚨 फ्रॉड हुआ? तुरंत 1930 (साइबर हेल्पलाइन) डायल करें या cybercrime.gov.in पर जाएं",

        # Errors
        "error_no_image": "कृपया पहले एक छवि अपलोड करें।",
        "error_analysis_failed": "विश्लेषण विफल रहा। कृपया पुनः प्रयास करें।",
        "error_image_too_large": "छवि बहुत बड़ी है। कृपया 10 MB से कम की छवि अपलोड करें।",
        "error_invalid_image": "अमान्य छवि फ़ाइल। कृपया JPG, PNG, या WEBP छवि अपलोड करें।",

        # Footer
        "footer": "ScamShield v1.1 • MIT लाइसेंस • Hacktoberfest 2026 के लिए बनाया गया",
        "disclaimer": "⚠️ यह उपकरण जन-जागरूकता के लिए है। किसी भी संदिग्ध लेनदेन के लिए हमेशा अपनी बैंक शाखा से संपर्क करें।",
    },

    "gu": {
        # App metadata
        "app_title": "🛡️ સ્કૅમશીલ્ડ AI",
        "app_subtitle": "સાયબર ફ્રોડ ઇન્ટેલિજન્સ અને સ્કૅમ ડિટેક્શન — Gemma 4 દ્વારા સંચાલિત",
        "app_tagline": "શંકાસ્પદ સ્ક્રીનશૉટ અપલોડ કરો, AI સાથે ચેટ કરો, નવા ફ્રોડ ટ્રેન્ડ્સ જુઓ અને પરિવારનું રક્ષણ કરો.",

        # Navigation Tabs
        "tab_scanner": "📸 સ્ક્રીનશૉટ સ્કેનર",
        "tab_chat": "💬 AI સુરક્ષા ચેટ",
        "tab_intel": "📊 સાયબર ખતરા અને ટ્રેન્ડ્સ",
        "tab_helpline": "🆘 ઇમરજન્સી હેલ્પલાઇન",
        "tab_alerts": "🚨 પરિવાર અલર્ટ કેન્દ્ર",

        # Language selector
        "select_language": "Language / भाषा / ભાષા",

        # Quick sample test buttons
        "genuine_samples_title": "✅ સાચા અને સુરક્ષિત મેસેજ (ખોટી ચેતવણી અટકાવવાની તપાસ):",
        "scam_samples_title": "🚨 જાણીતા સ્કૅમ અને ફ્રોડ (ખતરાની તપાસ કરો):",
        "sample_safe_bank": "🏦 HDFC બેંક ડેબિટ અલર્ટ",
        "sample_safe_otp": "🔑 એમેઝોન વેરિફિકેશન OTP",
        "sample_safe_delivery": "🍔 સ્વિગી ડિલિવરી અપડેટ",
        "sample_safe_ticket": "🚆 IRCTC ટ્રેન ટિકિટ",
        "sample_kyc": "⚠️ નકલી SBI KYC બ્લોક",
        "sample_lottery": "🎁 ગૂગલ લકી ડ્રો ઈનામ",
        "sample_upi": "💳 UPI પિનની જાળ",
        "sample_job": "💼 ટેલિગ્રામ જોબ ફ્રોડ",
        "sample_govt": "🏛️ TRAI સિમ ડિસ્કનેક્ટ",

        # Upload section
        "upload_header": "📤 શંકાસ્પદ સ્ક્રીનશૉટ અપલોડ કરો",
        "upload_prompt": "શંકાસ્પદ એસએમએસ, વ્હોટ્સએપ ચેટ, નકલી UPI સ્ક્રીન અથવા APK પ્રોમ્પ્ટનો ફોટો અપલોડ કરો.",
        "upload_button_label": "છબી પસંદ કરો...",
        "upload_types": "JPG, PNG, WEBP — મહત્તમ 10 MB",

        # Analysis section
        "analyze_button": "🔍 Gemma 4 વડે વિશ્લેષણ કરો",
        "analyzing": "Gemma 4 સંકેતો અને છેતરપિંડીના પેટર્નની તપાસ કરી રહ્યું છે...",
        "analysis_result": "📊 સ્કૅમશીલ્ડ જોખમ નિર્ણય",

        # Verdict labels
        "verdict_safe": "✅ સુરક્ષિત — કોઈ સ્કૅમ મળ્યો નથી",
        "verdict_suspicious": "⚠️ શંકાસ્પદ — અત્યંત સાવચેતી રાખો",
        "verdict_scam": "🚨 ગંભીર સ્કૅમ — બિલકુલ ક્લિક ન કરશો",

        # Result fields
        "risk_score": "જોખમ સ્કોર",
        "summary": "AI સારાંશ",
        "red_flags": "શોધાયેલ ખતરાના સંકેતો",
        "advice": "સુરક્ષા માટે શું કરવું",
        "scam_type": "સ્કૅમ પ્રકાર",
        "confidence": "વિશ્વસનીયતા",
        "reasoning_expander": "🧠 Gemma 4 ના તર્ક અને વિચારવાની પ્રક્રિયા જુઓ",

        # Chat section
        "chat_header": "💬 સ્કૅમશીલ્ડ AI સહાયક સાથે વાત કરો",
        "chat_caption": "પ્રશ્નો પૂછો, શંકાસ્પદ મેસેજ પેસ્ટ કરો, અથવા ઇમરજન્સી બચાવના પગલાં જાણો.",
        "chat_welcome": "નમસ્તે! હું Gemma 4 દ્વારા સંચાલિત સ્કૅમશીલ્ડ AI છું. કોઈપણ શંકાસ્પદ સંદેશ અહીં પેસ્ટ કરો અથવા ફ્રોડ સંબંધિત પ્રશ્ન પૂછો.",
        "chat_placeholder": "તમારો પ્રશ્ન લખો અથવા શંકાસ્પદ સંદેશ પેસ્ટ કરો...",
        "chat_send": "મોકલો",
        "chat_clear": "ચેટ સાફ કરો",
        "chat_context_active": "💡 સક્રિય સ્ક્રીનશૉટનો સંદર્ભ ચેટમાં ઉમેરાયો છે",

        # Threat Intel section
        "intel_header": "📊 ભારતમાં સક્રિય સાયબર ફ્રોડના મુખ્ય પ્રકારો",
        "intel_caption": "સાયબર ક્રાઈમ સેલ અને બેંકિંગ સતર્કતા એકમો દ્વારા ઓળખાયેલા પેટર્ન.",
        "golden_hour_header": "⏳ ગોલ્ડન અવર એક્શન પ્રોટોકોલ (પ્રથમ 60 મિનિટ)",
        "golden_hour_caption": "જો તમારી સાથે કે પરિવારમાં કોઈની સાથે છેતરપિંડી થઈ હોય, તો તાત્કાલિક આ કરો:",

        # Alert section
        "alert_header": "🚨 પરિવારના જૂથમાં અલર્ટ મોકલો",
        "alert_button": "📢 Discord વેબહૂક પર અલર્ટ મોકલો",
        "alert_copy_button": "📋 ક્લિપબોર્ડ પર અલર્ટ કૉપિ કરો",
        "alert_sent": "✅ Discord પર પરિવારનો અલર્ટ સફળતાપૂર્વક મોકલ્યો!",
        "alert_copied": "📋 અલર્ટ કૉપિ થઈ ગયો! તમારા કૌટુંબિક વ્હોટ્સએપ/ટેલિગ્રામ જૂથમાં પેસ્ટ કરો.",
        "alert_failed": "❌ અલર્ટ મોકલવામાં નિષ્ફળ. ટેક્સ્ટ ક્લિપબોર્ડ પર કૉપિ થયો.",
        "alert_no_result": "અલર્ટ મોકલતા પહેલા કૃપા કરીને પ્રથમ કોઈ સ્ક્રીનશૉટનું વિશ્લેષણ કરો.",
        "alert_preview": "અલર્ટ પૂર્વાવલોકન (વ્હોટ્સએપ/ડિસ્કોર્ડ ફોર્મેટ):",

        # Provider info
        "provider_gemini": "🌐 પ્રાથમિક: Google Gemini Cloud (gemma-4-26b-a4b-it)",
        "provider_ollama": "🖥️ સ્થાનિક બેકઅપ: Ollama (gemma4:e4b)",
        "provider_error": "❌ કોઈ AI પ્રદાતા ઉપલબ્ધ નથી. તમારી .env ગોઠવણી તપાસો.",

        # Emergency Banner
        "emergency_banner": "🚨 ફ્રોડ થયો? તરત જ 1930 (સાયબર હેલ્પલાઇન) ડાયલ કરો અથવા cybercrime.gov.in પર જાઓ",

        # Errors
        "error_no_image": "કૃપા કરીને પ્રથમ છબી અપલોડ કરો.",
        "error_analysis_failed": "વિશ્લેષણ નિષ્ફળ થયું. કૃપા કરી ફરી પ્રયાસ કરો.",
        "error_image_too_large": "છબી ખૂબ મોટી છે. કૃપા 10 MB થી ઓછી છબી અપલોડ કરો.",
        "error_invalid_image": "અમાન્ય છબી ફાઇલ. કૃપા JPG, PNG, અથવા WEBP છબી અપલોડ કરો.",

        # Footer
        "footer": "ScamShield v1.1 • MIT લાઇસન્સ • Hacktoberfest 2026 માટે બનાવ્યું",
        "disclaimer": "⚠️ આ સાધન સાયબર જાગૃતિ માટે છે. કોઈપણ શંકાસ્પદ વ્યવહાર માટે હંમેશા તમારી બેંકનો સંપર્ક કરો.",
    },
}


def get_string(lang: str, key: str) -> str:
    """Get a localized string for the given language and key.
    Falls back to English if key is not found in the target language.
    """
    lang = lang if lang in STRINGS else "en"
    return STRINGS[lang].get(key) or STRINGS["en"].get(key, key)


t = get_string

__all__ = ["SUPPORTED_LANGUAGES", "STRINGS", "get_string", "t"]
