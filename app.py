"""ScamShield — Main Streamlit application.

Run with: streamlit run app.py
"""

from __future__ import annotations

import io
import logging

import streamlit as st
from PIL import Image
from dotenv import load_dotenv

from scamshield.analyzer import analyze_screenshot, AnalysisError
from scamshield.alert import send_alert
from scamshield.i18n import get_string
from scamshield.llm import get_provider, LLMError
from scamshield.prompts import build_alert_message

load_dotenv()
logging.basicConfig(level=logging.INFO)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ScamShield",
    page_icon="🛡️",
    layout="centered",
    initial_sidebar_state="auto",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Overall app styling */
.stApp {
    max-width: 860px;
    margin: 0 auto;
}

/* Verdict cards */
.verdict-safe {
    background: linear-gradient(135deg, #00C851, #007E33);
    color: white;
    border-radius: 12px;
    padding: 20px 24px;
    text-align: center;
    font-size: 1.6rem;
    font-weight: 700;
    margin: 12px 0;
    box-shadow: 0 4px 15px rgba(0, 200, 81, 0.4);
}
.verdict-suspicious {
    background: linear-gradient(135deg, #FF8800, #CC6600);
    color: white;
    border-radius: 12px;
    padding: 20px 24px;
    text-align: center;
    font-size: 1.6rem;
    font-weight: 700;
    margin: 12px 0;
    box-shadow: 0 4px 15px rgba(255, 136, 0, 0.4);
}
.verdict-scam {
    background: linear-gradient(135deg, #FF4444, #CC0000);
    color: white;
    border-radius: 12px;
    padding: 20px 24px;
    text-align: center;
    font-size: 1.6rem;
    font-weight: 700;
    margin: 12px 0;
    box-shadow: 0 4px 15px rgba(255, 68, 68, 0.5);
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { box-shadow: 0 4px 15px rgba(255, 68, 68, 0.5); }
    50% { box-shadow: 0 4px 30px rgba(255, 68, 68, 0.9); }
}

/* Risk meter */
.risk-bar-container {
    background: #eee;
    border-radius: 8px;
    height: 18px;
    margin: 8px 0;
    overflow: hidden;
}
.risk-bar {
    height: 100%;
    border-radius: 8px;
    transition: width 0.5s ease;
}

/* Red flag list */
.red-flag-item {
    background: #fff3cd;
    border-left: 4px solid #FF8800;
    padding: 8px 12px;
    margin: 4px 0;
    border-radius: 0 6px 6px 0;
    font-size: 0.95rem;
}

/* Provider badge */
.provider-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 0.8rem;
    font-weight: 600;
    margin-bottom: 8px;
}
.provider-gemini { background: #e8f4fd; color: #1a73e8; }
.provider-ollama { background: #f0f0f0; color: #333; }

/* Footer */
.footer {
    text-align: center;
    color: #888;
    font-size: 0.8rem;
    margin-top: 40px;
    padding-top: 16px;
    border-top: 1px solid #eee;
}
</style>
""", unsafe_allow_html=True)


# ── Session state ──────────────────────────────────────────────────────────────
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "analysis_provider" not in st.session_state:
    st.session_state.analysis_provider = None
if "lang" not in st.session_state:
    st.session_state.lang = "en"

# ── Language selector ──────────────────────────────────────────────────────────
lang_options = {
    "English": "en",
    "हिंदी (Hindi)": "hi",
    "ગુજરાતી (Gujarati)": "gu",
}

selected_lang_label = st.selectbox(
    get_string(st.session_state.lang, "select_language"),
    options=list(lang_options.keys()),
    index=0,
    key="lang_selector",
)
lang = lang_options[selected_lang_label]
st.session_state.lang = lang

T = lambda key: get_string(lang, key)  # noqa: E731 — shorthand translator


# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(f"# {T('app_title')}")
st.markdown(f"**{T('app_subtitle')}**")
st.caption(T("app_tagline"))

# ── Provider status ────────────────────────────────────────────────────────────
try:
    provider = get_provider()
    if provider == "gemini":
        st.markdown(
            f'<div class="provider-badge provider-gemini">{T("provider_gemini")}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="provider-badge provider-ollama">{T("provider_ollama")}</div>',
            unsafe_allow_html=True,
        )
except LLMError:
    st.error(T("provider_error"))

st.divider()

# ── Upload section ─────────────────────────────────────────────────────────────
st.markdown(f"### {T('upload_header')}")
st.caption(T("upload_prompt"))

uploaded_file = st.file_uploader(
    label=T("upload_button_label"),
    type=["jpg", "jpeg", "png", "webp"],
    label_visibility="collapsed",
)

if uploaded_file is not None:
    image_bytes = uploaded_file.read()

    # Preview
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(image_bytes, caption=uploaded_file.name, use_container_width=True)

    st.divider()

    # ── Analyze button ─────────────────────────────────────────────────────────
    if st.button(T("analyze_button"), type="primary", use_container_width=True):
        with st.spinner(T("analyzing")):
            try:
                result, provider_used = analyze_screenshot(image_bytes, lang=lang)
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

# ── Results display ────────────────────────────────────────────────────────────
if st.session_state.analysis_result:
    result = st.session_state.analysis_result
    verdict = result.get("verdict", "SUSPICIOUS")
    risk_score = result.get("risk_score", 50)
    confidence = result.get("confidence", "MEDIUM")
    scam_type = result.get("scam_type", "Unknown")
    summary = result.get("summary", "")
    red_flags = result.get("red_flags", [])
    advice = result.get("advice", "")

    st.markdown(f"### {T('analysis_result')}")

    # Verdict card
    verdict_key = f"verdict_{verdict.lower()}"
    verdict_label = T(verdict_key)
    verdict_css = f"verdict-{verdict.lower()}"
    st.markdown(
        f'<div class="{verdict_css}">{verdict_label}</div>',
        unsafe_allow_html=True,
    )

    # Risk score meter
    col_score, col_conf, col_type = st.columns(3)
    with col_score:
        st.metric(T("risk_score"), f"{risk_score}/100")
    with col_conf:
        st.metric(T("confidence"), confidence)
    with col_type:
        st.metric(T("scam_type"), scam_type)

    # Risk bar (visual)
    bar_color = (
        "#00C851" if risk_score < 30
        else "#FF8800" if risk_score < 70
        else "#FF4444"
    )
    st.markdown(
        f"""
        <div class="risk-bar-container">
            <div class="risk-bar" style="width:{risk_score}%; background:{bar_color};"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Summary
    st.markdown(f"**{T('summary')}**")
    st.info(summary)

    # Red flags
    if red_flags:
        st.markdown(f"**{T('red_flags')}**")
        for flag in red_flags:
            st.markdown(
                f'<div class="red-flag-item">🚩 {flag}</div>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown(f"**{T('red_flags')}:** None detected")

    st.markdown("")

    # Advice
    st.markdown(f"**{T('advice')}**")
    st.success(advice)

    st.divider()

    # ── Alert section ──────────────────────────────────────────────────────────
    st.markdown(f"### {T('alert_header')}")

    alert_text = build_alert_message(result, lang)
    st.text_area("Alert preview:", value=alert_text, height=200, disabled=True)

    if st.button(T("alert_button"), type="secondary", use_container_width=True):
        method, success = send_alert(result, alert_text)
        if method == "discord" and success:
            st.success(T("alert_sent"))
        elif method == "clipboard" and success:
            st.info(T("alert_copied"))
        else:
            st.error(T("alert_failed"))

    st.divider()

# ── Empty state ────────────────────────────────────────────────────────────────
elif uploaded_file is None:
    st.markdown("""
    <div style="text-align: center; padding: 40px; color: #999;">
        <div style="font-size: 4rem;">📸</div>
        <p style="font-size: 1.1rem; margin-top: 12px;">
            Upload a screenshot above to get started.
        </p>
    </div>
    """, unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown(
    f'<div class="footer">{T("disclaimer")}<br><br>{T("footer")}</div>',
    unsafe_allow_html=True,
)
