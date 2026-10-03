"""ScamShield AI — Ultra-Modern Cybersecurity & Scam Defense Dashboard.

Powered by Google Gemma 4 (gemma-4-26b-a4b-it / gemma4:e4b).
Trilingual Support: English, Hindi (हिंदी), Gujarati (ગુજરાતી).
"""

from __future__ import annotations

import logging
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from scamshield.analyzer import analyze_screenshot, AnalysisError
from scamshield.alert import send_alert, copy_to_clipboard
from scamshield.chat import chat_with_scamshield
from scamshield.i18n import get_string
from scamshield.intel import EMERGENCY_CONTACTS, SCAM_TRENDS, GOLDEN_HOUR_STEPS
from scamshield.llm import get_provider, LLMError
from scamshield.prompts import build_alert_message

load_dotenv()
logging.basicConfig(level=logging.INFO)

# ── Streamlit Page Configuration ───────────────────────────────────────────────
st.set_page_config(
    page_title="ScamShield AI • Cyber Scam Defense",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Ultra-Cool Cyber-Shield Custom CSS ────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');

/* Base Canvas */
.stApp {
    background: radial-gradient(circle at 50% -10%, #0D1527 0%, #070B14 100%);
    color: #F8FAFC;
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* Hide Default Streamlit Menu Padding */
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 3rem !important;
    max-width: 1250px !important;
}

/* Glassmorphic Cyber Header */
.cyber-hero {
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.85) 0%, rgba(30, 41, 59, 0.7) 100%);
    border: 1px solid rgba(56, 189, 248, 0.25);
    border-radius: 20px;
    padding: 28px 32px;
    margin-bottom: 20px;
    box-shadow: 0 10px 40px -10px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(16px);
    position: relative;
    overflow: hidden;
}

.cyber-hero::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 3px;
    background: linear-gradient(90deg, #38BDF8, #818CF8, #EC4899, #38BDF8);
    background-size: 200% 100%;
    animation: cyber-glow-sweep 6s linear infinite;
}

@keyframes cyber-glow-sweep {
    0% { background-position: 0% 0%; }
    100% { background-position: 200% 0%; }
}

/* Emergency Hotline Ticker */
.emergency-ticker-bar {
    background: linear-gradient(90deg, rgba(185, 28, 28, 0.9) 0%, rgba(220, 38, 38, 0.95) 50%, rgba(185, 28, 28, 0.9) 100%);
    border: 1px solid rgba(248, 113, 113, 0.4);
    border-radius: 12px;
    padding: 12px 20px;
    margin-bottom: 22px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 4px 20px rgba(220, 38, 38, 0.35);
    backdrop-filter: blur(8px);
}

.emergency-ticker-badge {
    background: rgba(0, 0, 0, 0.45);
    color: #FEF08A;
    font-weight: 800;
    font-size: 0.95rem;
    padding: 6px 14px;
    border-radius: 8px;
    letter-spacing: 0.5px;
    border: 1px solid rgba(254, 240, 138, 0.3);
}

/* Status Chips & Badges */
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 5px 14px;
    border-radius: 9999px;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.3px;
}
.status-pill-gemini {
    background: rgba(56, 189, 248, 0.15);
    color: #38BDF8;
    border: 1px solid rgba(56, 189, 248, 0.4);
}
.status-pill-ollama {
    background: rgba(168, 85, 247, 0.15);
    color: #C084FC;
    border: 1px solid rgba(168, 85, 247, 0.4);
}
.status-pill-active {
    background: rgba(16, 185, 129, 0.15);
    color: #34D399;
    border: 1px solid rgba(16, 185, 129, 0.4);
}

/* Glassmorphism Section Card */
.glass-box {
    background: rgba(15, 23, 42, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 22px;
    margin-bottom: 18px;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.35);
    backdrop-filter: blur(12px);
}

/* Verdict Shield Containers */
.verdict-banner {
    border-radius: 18px;
    padding: 26px;
    text-align: center;
    margin: 18px 0;
    font-size: 1.75rem;
    font-weight: 900;
    letter-spacing: 1px;
    text-transform: uppercase;
}
.verdict-banner-safe {
    background: linear-gradient(135deg, rgba(6, 95, 70, 0.85) 0%, rgba(5, 150, 105, 0.95) 100%);
    border: 1.5px solid #34D399;
    color: #ECFDF5;
    box-shadow: 0 10px 30px rgba(16, 185, 129, 0.4);
}
.verdict-banner-suspicious {
    background: linear-gradient(135deg, rgba(154, 52, 18, 0.85) 0%, rgba(217, 119, 6, 0.95) 100%);
    border: 1.5px solid #FBBF24;
    color: #FFFBEB;
    box-shadow: 0 10px 30px rgba(245, 158, 11, 0.4);
}
.verdict-banner-scam {
    background: linear-gradient(135deg, rgba(153, 27, 27, 0.9) 0%, rgba(220, 38, 38, 0.95) 100%);
    border: 1.5px solid #F87171;
    color: #FEF2F2;
    box-shadow: 0 10px 35px rgba(239, 68, 68, 0.55);
    animation: scam-pulse 2.2s infinite;
}
@keyframes scam-pulse {
    0%, 100% { box-shadow: 0 10px 30px rgba(239, 68, 68, 0.45); }
    50% { box-shadow: 0 12px 50px rgba(239, 68, 68, 0.85); }
}

/* Progress Meter */
.cyber-progress-track {
    background: #1E293B;
    border-radius: 12px;
    height: 20px;
    overflow: hidden;
    margin: 12px 0 18px 0;
    border: 1px solid #334155;
}
.cyber-progress-fill {
    height: 100%;
    border-radius: 12px;
    transition: width 0.7s cubic-bezier(0.16, 1, 0.3, 1);
}

/* Warning & Check Signal Chips */
.threat-chip {
    background: rgba(239, 68, 68, 0.12);
    border-left: 4px solid #EF4444;
    border-top: 1px solid rgba(239, 68, 68, 0.2);
    border-right: 1px solid rgba(239, 68, 68, 0.2);
    border-bottom: 1px solid rgba(239, 68, 68, 0.2);
    padding: 12px 16px;
    margin: 8px 0;
    border-radius: 0 10px 10px 0;
    color: #FCA5A5;
    font-size: 0.96rem;
}
.safe-chip {
    background: rgba(16, 185, 129, 0.12);
    border-left: 4px solid #10B981;
    border-top: 1px solid rgba(16, 185, 129, 0.2);
    border-right: 1px solid rgba(16, 185, 129, 0.2);
    border-bottom: 1px solid rgba(16, 185, 129, 0.2);
    padding: 12px 16px;
    margin: 8px 0;
    border-radius: 0 10px 10px 0;
    color: #6EE7B7;
    font-size: 0.96rem;
}

/* Terminal / CoT Reasoning Box */
.terminal-card {
    background: #050811;
    border: 1px solid #1E293B;
    border-radius: 12px;
    padding: 16px 20px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.88rem;
    color: #94A3B8;
    line-height: 1.6;
    margin-top: 12px;
}

/* Hotline Card Box */
.hotline-card {
    background: rgba(30, 41, 59, 0.6);
    border: 1px solid rgba(56, 189, 248, 0.2);
    border-radius: 14px;
    padding: 20px;
    margin-bottom: 14px;
    transition: transform 0.2s ease, border-color 0.2s ease;
}
.hotline-card:hover {
    transform: translateY(-2px);
    border-color: rgba(56, 189, 248, 0.5);
}

/* Custom Buttons Styling */
div[data-testid="stHorizontalBlock"] button {
    border-radius: 10px;
    font-weight: 600;
    transition: all 0.2s ease;
}

/* Footer Styling */
.footer-container {
    text-align: center;
    color: #64748B;
    font-size: 0.82rem;
    margin-top: 60px;
    padding: 24px 0;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
}
</style>
""", unsafe_allow_html=True)

# ── Session State Initializer ─────────────────────────────────────────────────
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "analysis_provider" not in st.session_state:
    st.session_state.analysis_provider = None
if "active_image_bytes" not in st.session_state:
    st.session_state.active_image_bytes = None
if "active_image_name" not in st.session_state:
    st.session_state.active_image_name = None
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "lang" not in st.session_state:
    st.session_state.lang = "en"


def T(key: str) -> str:
    """Helper to fetch localized string based on active session language."""
    return get_string(st.session_state.get("lang", "en"), key)


# ── Sidebar Controls ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🛡️ ScamShield AI")
    st.caption("Gemma 4 Real-Time Scam & Phishing Defense")

    # Language Switcher
    lang_map = {
        "🇬🇧 English": "en",
        "🇮🇳 हिंदी (Hindi)": "hi",
        "🇮🇳 ગુજરાતી (Gujarati)": "gu",
    }
    selected_lang = st.selectbox(
        "🌐 " + T("select_language"),
        options=list(lang_map.keys()),
        index=0,
        key="lang_sidebar_select",
    )
    st.session_state.lang = lang_map[selected_lang]

    st.markdown("<br>", unsafe_allow_html=True)

    # Active AI Provider Indicator
    try:
        prov = get_provider()
        if prov == "gemini":
            st.markdown(f'<div class="status-pill status-pill-gemini">{T("provider_gemini")}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="status-pill status-pill-ollama">{T("provider_ollama")}</div>', unsafe_allow_html=True)
    except LLMError:
        st.error(T("provider_error"))

    st.markdown(
        f'<div style="margin-top: 8px;"><span class="status-pill status-pill-active">🟢 MODEL: gemma-4-26b-a4b-it</span></div>',
        unsafe_allow_html=True,
    )

    st.divider()

    # Quick Emergency Dial in Sidebar
    st.markdown("### 🚨 Emergency Cyber Crime Helpline")
    st.markdown("""
    **National Cyber Helpline:**
    # [📞 1930](tel:1930)
    *(Toll-free • 24x7 Pan-India)*
    """)
    st.link_button("🌐 File e-FIR (cybercrime.gov.in)", "https://cybercrime.gov.in")
    st.link_button("📱 Report Spam (Chakshu Portal)", "https://sancharsaathi.gov.in/sfc/")

    st.divider()
    st.caption("ScamShield v1.2 • Hacktoberfest 2026")


# ── Top Emergency Banner ──────────────────────────────────────────────────────
st.markdown(
    f"""
    <div class="emergency-ticker-bar">
        <span style="font-size: 0.98rem; font-weight: 700; color: #FFFFFF;">
            {T("emergency_banner")}
        </span>
        <span class="emergency-ticker-badge">TOLL-FREE: 1930</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Hero Branding Header ──────────────────────────────────────────────────────
st.markdown(
    f"""
    <div class="cyber-hero">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
            <div>
                <h1 style="margin: 0; font-size: 2.3rem; font-weight: 800; color: #FFFFFF; letter-spacing: -0.5px;">
                    {T("app_title")}
                </h1>
                <p style="margin: 6px 0 0 0; font-size: 1.08rem; color: #94A3B8; font-weight: 500;">
                    {T("app_subtitle")}
                </p>
                <p style="margin: 4px 0 0 0; font-size: 0.92rem; color: #64748B;">
                    {T("app_tagline")}
                </p>
            </div>
            <div>
                <span class="status-pill status-pill-active">🛡️ ACTIVE INTELLIGENCE</span>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Primary Navigation Tabs ───────────────────────────────────────────────────
tab_scan, tab_chat, tab_intel, tab_help, tab_alert = st.tabs([
    T("tab_scanner"),
    T("tab_chat"),
    T("tab_intel"),
    T("tab_helpline"),
    T("tab_alerts"),
])


# ==============================================================================
# TAB 1: 📸 SCREENSHOT SCANNER (WITH GENUINE & FRAUD TEST CHIPS)
# ==============================================================================
with tab_scan:
    samples_dir = Path(__file__).parent / "tests" / "samples"

    def load_sample_file(filename: str, label: str):
        path = samples_dir / filename
        if path.exists():
            with open(path, "rb") as f:
                st.session_state.active_image_bytes = f.read()
                st.session_state.active_image_name = label
                st.session_state.analysis_result = None

    # ── Test Suite 1: Genuine / Legitimate Messages ──
    st.markdown(f"##### {T('genuine_samples_title')}")
    g1, g2, g3, g4 = st.columns(4)
    with g1:
        if st.button(T("sample_safe_bank"), key="btn_safe_bank", use_container_width=True):
            load_sample_file("safe_bank_alert.png", "HDFC Debit Alert (Genuine)")
    with g2:
        if st.button(T("sample_safe_otp"), key="btn_safe_otp", use_container_width=True):
            load_sample_file("safe_login_otp.png", "Amazon Login OTP (Genuine)")
    with g3:
        if st.button(T("sample_safe_delivery"), key="btn_safe_del", use_container_width=True):
            load_sample_file("safe_swiggy_delivery.png", "Swiggy Order Update (Genuine)")
    with g4:
        if st.button(T("sample_safe_ticket"), key="btn_safe_tkt", use_container_width=True):
            load_sample_file("safe_irctc_ticket.png", "IRCTC Train Ticket (Genuine)")

    # ── Test Suite 2: Fraudulent / Scam Messages ──
    st.markdown(f"##### {T('scam_samples_title')}")
    s1, s2, s3, s4, s5 = st.columns(5)
    with s1:
        if st.button(T("sample_kyc"), key="btn_scam_kyc", use_container_width=True):
            load_sample_file("kyc_scam.png", "Fake SBI KYC SMS")
    with s2:
        if st.button(T("sample_lottery"), key="btn_scam_lottery", use_container_width=True):
            load_sample_file("lottery_scam.png", "Google Lucky Draw")
    with s3:
        if st.button(T("sample_upi"), key="btn_scam_upi", use_container_width=True):
            load_sample_file("upi_phishing.png", "UPI PIN Phishing")
    with s4:
        if st.button(T("sample_job"), key="btn_scam_job", use_container_width=True):
            load_sample_file("job_scam.png", "Part-time Job Fraud")
    with s5:
        if st.button(T("sample_govt"), key="btn_scam_govt", use_container_width=True):
            load_sample_file("govt_impersonation.png", "TRAI Disconnect Notice")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Upload or Custom Image ──
    uploaded_file = st.file_uploader(
        label=T("upload_header"),
        type=["jpg", "jpeg", "png", "webp"],
        help=T("upload_types"),
    )

    if uploaded_file is not None:
        st.session_state.active_image_bytes = uploaded_file.read()
        st.session_state.active_image_name = uploaded_file.name

    # ── Preview & Analyze Action ──
    if st.session_state.active_image_bytes:
        img_col, action_col = st.columns([1, 1])

        with img_col:
            st.markdown(f"**Loaded Image:** `{st.session_state.active_image_name or 'Uploaded Screenshot'}`")
            st.image(st.session_state.active_image_bytes, width="stretch")

        with action_col:
            st.markdown("#### Ready for Gemma 4 Inspection")
            st.markdown("""
            <div class="glass-box" style="padding: 16px;">
                <p style="margin: 0; font-size: 0.95rem; color: #CBD5E1;">
                    Gemma 4 will inspect OCR text, sender ID, coercive urgency, OTP theft traps,
                    unverified URLs, and banking disclaimers to determine if this message is <b>GENUINE</b> or a <b>SCAM</b>.
                </p>
            </div>
            """, unsafe_allow_html=True)

            if st.button(T("analyze_button"), type="primary", key="btn_run_analysis", use_container_width=True):
                with st.spinner(T("analyzing")):
                    try:
                        result, provider_used = analyze_screenshot(
                            st.session_state.active_image_bytes,
                            lang=st.session_state.lang,
                        )
                        st.session_state.analysis_result = result
                        st.session_state.analysis_provider = provider_used
                    except LLMError as e:
                        st.error(T("provider_error"))
                        st.exception(e)
                    except AnalysisError as e:
                        st.error(str(e))
                    except Exception as e:
                        st.error(T("error_analysis_failed"))
                        st.exception(e)

        # ── Result Presentation Card ──
        if st.session_state.analysis_result:
            res = st.session_state.analysis_result
            verdict = res.get("verdict", "SUSPICIOUS")
            score = res.get("risk_score", 50)
            conf = res.get("confidence", "MEDIUM")
            cat = res.get("scam_type", "None")

            st.divider()
            st.markdown(f"### {T('analysis_result')}")

            # Dynamic Glowing Shield Banner
            verdict_class = f"verdict-banner-{verdict.lower()}"
            verdict_text = T(f"verdict_{verdict.lower()}")
            st.markdown(
                f'<div class="verdict-banner {verdict_class}">{verdict_text}</div>',
                unsafe_allow_html=True,
            )

            # High-Visibility Metrics Row
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric(T("risk_score"), f"{score} / 100")
            with m2:
                st.metric(T("confidence"), conf)
            with m3:
                st.metric(T("scam_type"), cat)

            # Animated Risk Gauge Fill Bar
            fill_color = (
                "#10B981" if score < 30
                else "#F59E0B" if score < 70
                else "#EF4444"
            )
            st.markdown(
                f"""
                <div class="cyber-progress-track">
                    <div class="cyber-progress-fill" style="width: {score}%; background: {fill_color};"></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Summary and Protective Actions
            c_sum, c_adv = st.columns(2)
            with c_sum:
                st.markdown(f"#### 📝 {T('summary')}")
                st.markdown(f'<div class="glass-box">{res.get("summary")}</div>', unsafe_allow_html=True)

            with c_adv:
                st.markdown(f"#### 🛡️ {T('advice')}")
                st.markdown(
                    f'<div class="glass-box" style="border-left: 4px solid #10B981;">{res.get("advice")}</div>',
                    unsafe_allow_html=True,
                )

            # Red Flags / Fraud Signals
            flags = res.get("red_flags", [])
            st.markdown(f"#### 🚩 {T('red_flags')}")
            if flags:
                for fl in flags:
                    st.markdown(f'<div class="threat-chip">🚩 <b>{fl}</b></div>', unsafe_allow_html=True)
            else:
                st.markdown(
                    '<div class="safe-chip">✅ <b>No malicious signals or phishing tactics detected. Standard legitimate communication.</b></div>',
                    unsafe_allow_html=True,
                )

            # Gemma 4 Chain-of-Thought Deep Reasoning
            if res.get("reasoning"):
                with st.expander(T("reasoning_expander")):
                    st.markdown(f'<div class="terminal-card">{res.get("reasoning")}</div>', unsafe_allow_html=True)


# ==============================================================================
# TAB 2: 💬 AI SAFETY CHAT ASSISTANT
# ==============================================================================
with tab_chat:
    st.markdown(f"### {T('chat_header')}")
    st.caption(T("chat_caption"))

    # Active screenshot context indicator
    if st.session_state.analysis_result:
        res = st.session_state.analysis_result
        st.markdown(
            f'<div class="status-pill status-pill-gemini" style="margin-bottom: 16px;">'
            f'{T("chat_context_active")}: [{res.get("verdict")} — {res.get("scam_type")}]'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Preset Quick-Questions
    st.markdown("**💡 Quick Security Inquiries:**")
    q1, q2, q3 = st.columns(3)
    preset_query = None
    with q1:
        if st.button("📞 What is a Digital Arrest scam?", key="btn_q_arrest", use_container_width=True):
            preset_query = "What is a Digital Arrest scam and how do scammers impersonate police on video calls?"
    with q2:
        if st.button("💳 I entered my UPI PIN for cashback. Was I scammed?", key="btn_q_upi", use_container_width=True):
            preset_query = "I entered my UPI PIN because a merchant said it was required to receive a cashback refund. Did I lose money?"
    with q3:
        if st.button("🆘 I already sent money. What are my first steps?", key="btn_q_gold", use_container_width=True):
            preset_query = "I just sent money to a scammer 15 minutes ago. What should I do right now to freeze the money?"

    st.divider()

    # Chat Conversation History
    if not st.session_state.chat_messages:
        with st.chat_message("assistant", avatar="🛡️"):
            st.markdown(T("chat_welcome"))

    for msg in st.session_state.chat_messages:
        avatar = "👤" if msg["role"] == "user" else "🛡️"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # Chat Input Box
    user_input = st.chat_input(T("chat_placeholder"))
    active_prompt = preset_query or user_input

    if active_prompt:
        st.session_state.chat_messages.append({"role": "user", "content": active_prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(active_prompt)

        with st.chat_message("assistant", avatar="🛡️"):
            with st.spinner("Gemma 4 is thinking..."):
                try:
                    reply, prov = chat_with_scamshield(
                        messages=st.session_state.chat_messages,
                        current_analysis=st.session_state.analysis_result,
                        lang=st.session_state.lang,
                    )
                    st.markdown(reply)
                    st.session_state.chat_messages.append({"role": "assistant", "content": reply})
                except Exception as e:
                    st.error(f"Chat error: {e}")

    # Clear Chat Action
    if st.session_state.chat_messages:
        if st.button(T("chat_clear"), key="btn_clear_chat", type="secondary"):
            st.session_state.chat_messages = []
            st.rerun()


# ==============================================================================
# TAB 3: 📊 THREAT INTELLIGENCE & PATTERNS
# ==============================================================================
with tab_intel:
    st.markdown(f"### {T('intel_header')}")
    st.caption(T("intel_caption"))

    current_lang = st.session_state.get("lang", "en")
    for item in SCAM_TRENDS:
        title = (
            item["title_hi"] if current_lang == "hi"
            else item["title_gu"] if current_lang == "gu"
            else item["title"]
        )
        pattern = (
            item["pattern_hi"] if current_lang == "hi"
            else item["pattern_gu"] if current_lang == "gu"
            else item["pattern"]
        )
        reality = (
            item["reality_check_hi"] if current_lang == "hi"
            else item["reality_check_gu"] if current_lang == "gu"
            else item["reality_check"]
        )
        badge_color = "#EF4444" if item["severity"] == "CRITICAL" else "#F59E0B"

        with st.expander(f"⚠️ {title} — [{item['severity']}]"):
            st.markdown(f"**Modus Operandi (Fraud Pattern):**\n\n{pattern}")
            st.markdown(f"""
            <div style="background: rgba(16, 185, 129, 0.12); border-left: 4px solid #10B981; padding: 14px; border-radius: 8px; margin-top: 12px;">
                <b style="color: #34D399; font-size: 1rem;">🛡️ Reality Check / Defense:</b><br>
                <span style="color: #F1F5F9;">{reality}</span>
            </div>
            """, unsafe_allow_html=True)


# ==============================================================================
# TAB 4: 🆘 EMERGENCY HELPLINES & GOLDEN HOUR
# ==============================================================================
with tab_help:
    st.markdown(f"### {T('golden_hour_header')}")
    st.caption(T("golden_hour_caption"))

    current_lang = st.session_state.get("lang", "en")
    for step in GOLDEN_HOUR_STEPS:
        step_title = (
            step["step_hi"] if current_lang == "hi"
            else step["step_gu"] if current_lang == "gu"
            else step["step"]
        )
        step_detail = (
            step["detail_hi"] if current_lang == "hi"
            else step["detail_gu"] if current_lang == "gu"
            else step["detail"]
        )
        st.markdown(f"""
        <div class="glass-box" style="border-left: 4px solid #38BDF8; margin-bottom: 12px;">
            <b style="font-size: 1.15rem; color: #38BDF8;">{step_title}</b>
            <p style="margin: 6px 0 0 0; color: #E2E8F0; line-height: 1.5;">{step_detail}</p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.markdown("### 🏛️ Verified Official Portals & Contact Directory")

    h_cols = st.columns(2)
    for idx, c in enumerate(EMERGENCY_CONTACTS):
        name = (
            c["name_hi"] if current_lang == "hi"
            else c["name_gu"] if current_lang == "gu"
            else c["name"]
        )
        desc = (
            c["desc_hi"] if current_lang == "hi"
            else c["desc_gu"] if current_lang == "gu"
            else c["desc"]
        )
        with h_cols[idx % 2]:
            st.markdown(f"""
            <div class="hotline-card">
                <span class="status-pill status-pill-gemini">{c['badge']}</span>
                <h4 style="margin: 10px 0 4px 0; color: #FFFFFF; font-size: 1.2rem;">{name}</h4>
                <div style="font-size: 1.5rem; font-weight: 800; color: #38BDF8; font-family: 'JetBrains Mono', monospace;">
                    {c['number']}
                </div>
                <p style="margin: 8px 0 12px 0; font-size: 0.9rem; color: #94A3B8;">{desc}</p>
                <a href="{c['url']}" target="_blank" style="color: #38BDF8; font-weight: 700; text-decoration: none;">🔗 Open Official Portal →</a>
            </div>
            """, unsafe_allow_html=True)


# ==============================================================================
# TAB 5: 🚨 FAMILY ALERT CENTER
# ==============================================================================
with tab_alert:
    st.markdown(f"### {T('alert_header')}")

    if st.session_state.analysis_result:
        alert_msg = build_alert_message(st.session_state.analysis_result, st.session_state.lang)

        st.markdown(f"**{T('alert_preview')}**")
        st.text_area(label="Alert Content", value=alert_msg, height=220, disabled=True, label_visibility="collapsed")

        act1, act2 = st.columns(2)
        with act1:
            if st.button(T("alert_button"), key="btn_send_discord", type="primary", use_container_width=True):
                method, success = send_alert(st.session_state.analysis_result, alert_msg)
                if method == "discord" and success:
                    st.success(T("alert_sent"))
                elif method == "clipboard" and success:
                    st.info(T("alert_copied"))
                else:
                    st.error(T("alert_failed"))

        with act2:
            if st.button(T("alert_copy_button"), key="btn_copy_alert", type="secondary", use_container_width=True):
                if copy_to_clipboard(alert_msg):
                    st.success(T("alert_copied"))
                else:
                    st.info("Copy directly from the preview box above.")
    else:
        st.warning(T("alert_no_result"))
        st.info("Tip: Go to the Screenshot Scanner tab, pick any scam example or upload an image to generate an alert.")


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    f'<div class="footer-container">{T("disclaimer")}<br><br>{T("footer")}</div>',
    unsafe_allow_html=True,
)
