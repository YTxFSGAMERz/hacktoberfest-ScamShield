"""ScamShield — AI-Powered Cybersecurity Dashboard & Scam Defense.

Built with Gemma 4 (gemma-4-26b-a4b-it / gemma4:e4b).
Trilingual: English, Hindi, Gujarati.
"""

from __future__ import annotations

import io
import logging
from pathlib import Path

import streamlit as st
from PIL import Image
from dotenv import load_dotenv

from scamshield.analyzer import analyze_screenshot, AnalysisError
from scamshield.alert import send_alert
from scamshield.chat import chat_with_scamshield
from scamshield.i18n import get_string
from scamshield.intel import EMERGENCY_CONTACTS, SCAM_TRENDS, GOLDEN_HOUR_STEPS
from scamshield.llm import get_provider, LLMError
from scamshield.prompts import build_alert_message

load_dotenv()
logging.basicConfig(level=logging.INFO)

# ── Page Configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ScamShield AI — Gemma 4 Cyber Defense",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Premium Cyber-Shield Dark Theme CSS ───────────────────────────────────────
st.markdown("""
<style>
/* Main Background and Typography */
.stApp {
    background: radial-gradient(circle at 50% 0%, #111827 0%, #0B0F19 100%);
    color: #F3F4F6;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Header & Banner */
.cyber-header {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%);
    border: 1px solid rgba(59, 130, 246, 0.2);
    border-radius: 16px;
    padding: 24px 28px;
    margin-bottom: 20px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    backdrop-filter: blur(12px);
}

.emergency-ticker {
    background: linear-gradient(90deg, #991B1B 0%, #DC2626 50%, #991B1B 100%);
    color: #FFFFFF;
    font-weight: 700;
    padding: 10px 18px;
    border-radius: 10px;
    font-size: 0.92rem;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 4px 18px rgba(220, 38, 38, 0.4);
}

/* Glassmorphic Cards */
.glass-card {
    background: rgba(19, 27, 46, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 20px;
    margin-bottom: 16px;
    backdrop-filter: blur(10px);
}

/* Verdict Badges & Cards */
.verdict-card {
    border-radius: 16px;
    padding: 24px;
    text-align: center;
    margin: 16px 0;
    font-size: 1.6rem;
    font-weight: 800;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}
.verdict-safe {
    background: linear-gradient(135deg, #065F46 0%, #059669 100%);
    border: 1px solid #34D399;
    color: #ECFDF5;
    box-shadow: 0 8px 24px rgba(5, 150, 105, 0.35);
}
.verdict-suspicious {
    background: linear-gradient(135deg, #9A3412 0%, #D97706 100%);
    border: 1px solid #FBBF24;
    color: #FFFBEB;
    box-shadow: 0 8px 24px rgba(217, 119, 6, 0.35);
}
.verdict-scam {
    background: linear-gradient(135deg, #7F1D1D 0%, #DC2626 100%);
    border: 1px solid #F87171;
    color: #FEF2F2;
    box-shadow: 0 8px 28px rgba(220, 38, 38, 0.5);
    animation: pulse-border 2s infinite;
}
@keyframes pulse-border {
    0%, 100% { box-shadow: 0 8px 25px rgba(220, 38, 38, 0.4); }
    50% { box-shadow: 0 8px 45px rgba(220, 38, 38, 0.85); }
}

/* Risk Progress Bar */
.risk-meter-container {
    background: #1E293B;
    border-radius: 10px;
    height: 18px;
    overflow: hidden;
    margin: 12px 0;
    border: 1px solid #334155;
}
.risk-meter-fill {
    height: 100%;
    border-radius: 10px;
    transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Signal Chips */
.signal-chip {
    background: rgba(239, 68, 68, 0.12);
    border-left: 4px solid #EF4444;
    padding: 10px 14px;
    margin: 6px 0;
    border-radius: 0 8px 8px 0;
    color: #FCA5A5;
    font-size: 0.95rem;
}

/* Provider Chips */
.badge-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 0.82rem;
    font-weight: 600;
}
.badge-gemini {
    background: rgba(59, 130, 246, 0.15);
    color: #60A5FA;
    border: 1px solid rgba(59, 130, 246, 0.3);
}
.badge-ollama {
    background: rgba(168, 85, 247, 0.15);
    color: #C084FC;
    border: 1px solid rgba(168, 85, 247, 0.3);
}

/* Emergency Helpline Card */
.helpline-box {
    background: rgba(30, 41, 59, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;
}
.helpline-number {
    font-size: 1.4rem;
    font-weight: 800;
    color: #38BDF8;
}

/* Sample Quick-Pick Chips */
div[data-testid="stHorizontalBlock"] button {
    border-radius: 10px;
    font-weight: 600;
}

/* Footer styling */
.footer-text {
    text-align: center;
    color: #6B7280;
    font-size: 0.82rem;
    margin-top: 50px;
    padding: 20px 0;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
}
</style>
""", unsafe_allow_html=True)

# ── Session State Initialization ──────────────────────────────────────────────
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

# ── Sidebar Configuration ──────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://raw.githubusercontent.com/YTxFSGAMERz/hacktoberfest-ScamShield/main/tests/samples/safe_bank_alert.png", width=64) if False else st.markdown("## 🛡️ ScamShield AI")
    st.caption("Gemma 4 Real-Time Scam Defense")

    # Language Switcher
    lang_options = {
        "🇬🇧 English": "en",
        "🇮🇳 हिंदी (Hindi)": "hi",
        "🇮🇳 ગુજરાતી (Gujarati)": "gu",
    }
    selected_lang_label = st.selectbox(
        "Select Language / भाषा / ભાષા",
        options=list(lang_options.keys()),
        index=0,
        key="lang_sidebar_select",
    )
    lang = lang_options[selected_lang_label]
    st.session_state.lang = lang

    T = lambda key: get_string(lang, key)

    st.divider()

    # Active AI Provider Indicator
    try:
        prov = get_provider()
        if prov == "gemini":
            st.markdown(f'<div class="badge-pill badge-gemini">{T("provider_gemini")}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="badge-pill badge-ollama">{T("provider_ollama")}</div>', unsafe_allow_html=True)
    except LLMError:
        st.error(T("provider_error"))

    st.divider()

    # Quick Emergency Dial
    st.markdown("### 🚨 Emergency Helpline")
    st.markdown("""
    **National Cyber Helpline:**
    # [📞 1930](tel:1930)
    *(Toll-free • 24x7 India)*
    """)
    st.link_button("🌐 File e-FIR (cybercrime.gov.in)", "https://cybercrime.gov.in")

    st.divider()
    st.caption("ScamShield v1.1 • Hacktoberfest 2026")


# ── Top Emergency Alert Bar ───────────────────────────────────────────────────
T = lambda key: get_string(st.session_state.lang, key)

st.markdown(
    f"""
    <div class="emergency-ticker">
        <span>{T("emergency_banner")}</span>
        <span style="background: rgba(0,0,0,0.3); padding: 4px 10px; border-radius: 6px;">Toll-Free: 1930</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Top Hero Header ───────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div class="cyber-header">
        <h1 style="margin: 0; font-size: 2.2rem; font-weight: 800; color: #FFFFFF;">
            {T("app_title")}
        </h1>
        <p style="margin: 6px 0 0 0; font-size: 1.05rem; color: #94A3B8;">
            {T("app_subtitle")}
        </p>
        <p style="margin: 4px 0 0 0; font-size: 0.9rem; color: #64748B;">
            {T("app_tagline")}
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Dashboard Tabs Navigation ─────────────────────────────────────────────────
tab_scan, tab_chat, tab_intel, tab_help, tab_alert = st.tabs([
    T("tab_scanner"),
    T("tab_chat"),
    T("tab_intel"),
    T("tab_helpline"),
    T("tab_alerts"),
])


# ==============================================================================
# TAB 1: 📸 SCREENSHOT SCANNER
# ==============================================================================
with tab_scan:
    samples_dir = Path(__file__).parent / "tests" / "samples"

    def load_sample(filename: str, label: str):
        path = samples_dir / filename
        if path.exists():
            with open(path, "rb") as f:
                st.session_state.active_image_bytes = f.read()
                st.session_state.active_image_name = label
                st.session_state.analysis_result = None

    # Genuine / Safe Examples Row
    st.markdown(f"**{T('genuine_samples_title')}**")
    g1, g2, g3, g4 = st.columns(4)
    with g1:
        if st.button(T("sample_safe_bank"), use_container_width=True):
            load_sample("safe_bank_alert.png", "HDFC Debit Alert (Genuine)")
    with g2:
        if st.button(T("sample_safe_otp"), use_container_width=True):
            load_sample("safe_login_otp.png", "Amazon Login OTP (Genuine)")
    with g3:
        if st.button(T("sample_safe_delivery"), use_container_width=True):
            load_sample("safe_swiggy_delivery.png", "Swiggy Order Update (Genuine)")
    with g4:
        if st.button(T("sample_safe_ticket"), use_container_width=True):
            load_sample("safe_irctc_ticket.png", "IRCTC Train Ticket (Genuine)")

    # Fraudulent / Scam Examples Row
    st.markdown(f"**{T('scam_samples_title')}**")
    s1, s2, s3, s4, s5 = st.columns(5)
    with s1:
        if st.button(T("sample_kyc"), use_container_width=True):
            load_sample("kyc_scam.png", "Fake SBI KYC SMS")
    with s2:
        if st.button(T("sample_lottery"), use_container_width=True):
            load_sample("lottery_scam.png", "Google Lucky Draw")
    with s3:
        if st.button(T("sample_upi"), use_container_width=True):
            load_sample("upi_phishing.png", "UPI PIN Phishing")
    with s4:
        if st.button(T("sample_job"), use_container_width=True):
            load_sample("job_scam.png", "Part-time Job Fraud")
    with s5:
        if st.button(T("sample_govt"), use_container_width=True):
            load_sample("govt_impersonation.png", "TRAI Disconnect Notice")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Upload or Use Sample ──
    uploaded_file = st.file_uploader(
        label=T("upload_button_label"),
        type=["jpg", "jpeg", "png", "webp"],
        help=T("upload_types"),
    )

    if uploaded_file is not None:
        st.session_state.active_image_bytes = uploaded_file.read()
        st.session_state.active_image_name = uploaded_file.name

    # ── Display Image & Run Analysis ──
    if st.session_state.active_image_bytes:
        img_col, info_col = st.columns([1, 1])

        with img_col:
            st.markdown(f"**Loaded Image:** `{st.session_state.active_image_name or 'Uploaded Screenshot'}`")
            st.image(st.session_state.active_image_bytes, width="stretch")

        with info_col:
            st.markdown("#### Ready for Gemma 4 Inspection")
            st.info("Gemma 4 will analyze visual layout, text contents, pressure tactics, impersonated logos, and payment traps.")

            if st.button(T("analyze_button"), type="primary", use_container_width=True):
                with st.spinner(T("analyzing")):
                    try:
                        result, provider_used = analyze_screenshot(
                            st.session_state.active_image_bytes,
                            lang=lang,
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

        # ── Analysis Results Display ──
        if st.session_state.analysis_result:
            res = st.session_state.analysis_result
            verdict = res.get("verdict", "SUSPICIOUS")
            score = res.get("risk_score", 50)
            conf = res.get("confidence", "MEDIUM")
            cat = res.get("scam_type", "Unknown")

            st.divider()
            st.markdown(f"### {T('analysis_result')}")

            # Dynamic Verdict Shield
            verdict_class = f"verdict-{verdict.lower()}"
            verdict_title = T(f"verdict_{verdict.lower()}")
            st.markdown(
                f'<div class="verdict-card {verdict_class}">{verdict_title}</div>',
                unsafe_allow_html=True,
            )

            # Metrics Row
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric(T("risk_score"), f"{score} / 100")
            with m2:
                st.metric(T("confidence"), conf)
            with m3:
                st.metric(T("scam_type"), cat)

            # Color-coded Risk Progress Bar
            meter_color = (
                "#10B981" if score < 30
                else "#F59E0B" if score < 70
                else "#EF4444"
            )
            st.markdown(
                f"""
                <div class="risk-meter-container">
                    <div class="risk-meter-fill" style="width: {score}%; background: {meter_color};"></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Summary & Actions
            col_summ, col_act = st.columns(2)
            with col_summ:
                st.markdown(f"#### 📝 {T('summary')}")
                st.markdown(f'<div class="glass-card">{res.get("summary")}</div>', unsafe_allow_html=True)

            with col_act:
                st.markdown(f"#### 🛡️ {T('advice')}")
                st.markdown(f'<div class="glass-card" style="border-left: 4px solid #10B981;">{res.get("advice")}</div>', unsafe_allow_html=True)

            # Red Flags List
            flags = res.get("red_flags", [])
            st.markdown(f"#### 🚩 {T('red_flags')}")
            if flags:
                for f in flags:
                    st.markdown(f'<div class="signal-chip">🚩 <b>{f}</b></div>', unsafe_allow_html=True)
            else:
                st.success("No fraud signals detected in this screenshot.")

            # Gemma 4 Chain-of-Thought Reasoning
            if res.get("reasoning"):
                with st.expander(T("reasoning_expander")):
                    st.markdown(res.get("reasoning"))


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
            f'<div class="badge-pill badge-gemini" style="margin-bottom: 14px;">'
            f'{T("chat_context_active")}: [{res.get("verdict")} — {res.get("scam_type")}]'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Prompt Suggestions
    st.markdown("**💡 Quick Questions to Ask:**")
    q1, q2, q3 = st.columns(3)
    preset_query = None
    with q1:
        if st.button("📞 What is a Digital Arrest scam?", use_container_width=True):
            preset_query = "What is a Digital Arrest scam and how do scammers impersonate police on video calls?"
    with q2:
        if st.button("💳 I entered my UPI PIN for cashback. Was I scammed?", use_container_width=True):
            preset_query = "I entered my UPI PIN because a merchant said it was required to receive a cashback refund. Did I lose money?"
    with q3:
        if st.button("🆘 I already sent money. What are my first steps?", use_container_width=True):
            preset_query = "I just sent money to a scammer 15 minutes ago. What should I do right now to freeze the money?"

    st.divider()

    # Display Chat History
    if not st.session_state.chat_messages:
        with st.chat_message("assistant", avatar="🛡️"):
            st.markdown(T("chat_welcome"))

    for msg in st.session_state.chat_messages:
        avatar = "👤" if msg["role"] == "user" else "🛡️"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # Chat Input
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
                        lang=lang,
                    )
                    st.markdown(reply)
                    st.session_state.chat_messages.append({"role": "assistant", "content": reply})
                except Exception as e:
                    st.error(f"Chat error: {e}")

    # Clear chat button
    if st.session_state.chat_messages:
        if st.button(T("chat_clear"), type="secondary"):
            st.session_state.chat_messages = []
            st.rerun()


# ==============================================================================
# TAB 3: 📊 THREAT INTELLIGENCE & PATTERNS
# ==============================================================================
with tab_intel:
    st.markdown(f"### {T('intel_header')}")
    st.caption(T("intel_caption"))

    for item in SCAM_TRENDS:
        title = (
            item["title_hi"] if lang == "hi"
            else item["title_gu"] if lang == "gu"
            else item["title"]
        )
        pattern = (
            item["pattern_hi"] if lang == "hi"
            else item["pattern_gu"] if lang == "gu"
            else item["pattern"]
        )
        reality = (
            item["reality_check_hi"] if lang == "hi"
            else item["reality_check_gu"] if lang == "gu"
            else item["reality_check"]
        )
        sev_color = "#EF4444" if item["severity"] == "CRITICAL" else "#F59E0B"

        with st.expander(f"⚠️ {title} — [{item['severity']}]"):
            st.markdown(f"**Modus Operandi (Fraud Pattern):**\n\n{pattern}")
            st.markdown(f"""
            <div style="background: rgba(16, 185, 129, 0.1); border-left: 4px solid #10B981; padding: 12px; border-radius: 6px; margin-top: 10px;">
                <b style="color: #34D399;">🛡️ Reality Check / Defense:</b><br>{reality}
            </div>
            """, unsafe_allow_html=True)


# ==============================================================================
# TAB 4: 🆘 EMERGENCY HELPLINES & GOLDEN HOUR
# ==============================================================================
with tab_help:
    st.markdown(f"### {T('golden_hour_header')}")
    st.caption(T("golden_hour_caption"))

    for step in GOLDEN_HOUR_STEPS:
        step_title = (
            step["step_hi"] if lang == "hi"
            else step["step_gu"] if lang == "gu"
            else step["step"]
        )
        step_detail = (
            step["detail_hi"] if lang == "hi"
            else step["detail_gu"] if lang == "gu"
            else step["detail"]
        )
        st.markdown(f"""
        <div class="glass-card" style="border-left: 4px solid #38BDF8;">
            <b style="font-size: 1.1rem; color: #38BDF8;">{step_title}</b>
            <p style="margin: 6px 0 0 0; color: #E2E8F0;">{step_detail}</p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.markdown("### 🏛️ Verified Official Portals & Numbers")

    h_cols = st.columns(2)
    for idx, c in enumerate(EMERGENCY_CONTACTS):
        name = (
            c["name_hi"] if lang == "hi"
            else c["name_gu"] if lang == "gu"
            else c["name"]
        )
        desc = (
            c["desc_hi"] if lang == "hi"
            else c["desc_gu"] if lang == "gu"
            else c["desc"]
        )
        with h_cols[idx % 2]:
            st.markdown(f"""
            <div class="helpline-box">
                <span class="badge-pill badge-gemini">{c['badge']}</span>
                <h4 style="margin: 8px 0 4px 0; color: #FFFFFF;">{name}</h4>
                <div class="helpline-number">{c['number']}</div>
                <p style="margin: 6px 0 10px 0; font-size: 0.88rem; color: #94A3B8;">{desc}</p>
                <a href="{c['url']}" target="_blank" style="color: #38BDF8; font-weight: 600; text-decoration: none;">🔗 Open Official Portal →</a>
            </div>
            """, unsafe_allow_html=True)


# ==============================================================================
# TAB 5: 🚨 FAMILY ALERT CENTER
# ==============================================================================
with tab_alert:
    st.markdown(f"### {T('alert_header')}")

    if st.session_state.analysis_result:
        alert_msg = build_alert_message(st.session_state.analysis_result, lang)

        st.markdown(f"**{T('alert_preview')}**")
        st.text_area(label="Alert Content", value=alert_msg, height=220, disabled=True, label_visibility="collapsed")

        act1, act2 = st.columns(2)
        with act1:
            if st.button(T("alert_button"), type="primary", use_container_width=True):
                method, success = send_alert(st.session_state.analysis_result, alert_msg)
                if method == "discord" and success:
                    st.success(T("alert_sent"))
                elif method == "clipboard" and success:
                    st.info(T("alert_copied"))
                else:
                    st.error(T("alert_failed"))

        with act2:
            if st.button(T("alert_copy_button"), type="secondary", use_container_width=True):
                from scamshield.alert import copy_to_clipboard
                if copy_to_clipboard(alert_msg):
                    st.success(T("alert_copied"))
                else:
                    st.info("Copy directly from the preview box above.")
    else:
        st.warning(T("alert_no_result"))
        st.info("Tip: Go to the Screenshot Scanner tab and load any scam example to generate an alert.")


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    f'<div class="footer-text">{T("disclaimer")}<br><br>{T("footer")}</div>',
    unsafe_allow_html=True,
)
