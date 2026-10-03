"""ScamShield AI — Dual Local Runner & Streamlit Bridge.

Runs the exact modern Cyber-Shield Web App powered by Gemma 4.
Can be executed directly via:
    python app.py
    python run.py
or via Streamlit:
    streamlit run app.py
"""

from __future__ import annotations

import os
import sys
import threading
import time
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from api.index import app as flask_app

FLASK_PORT = 5000
_server_started = False
_server_lock = threading.Lock()


def _start_flask_server():
    global _server_started
    with _server_lock:
        if not _server_started:
            def _runner():
                import werkzeug.serving
                werkzeug.serving.run_simple("127.0.0.1", FLASK_PORT, flask_app, threaded=True)

            t = threading.Thread(target=_runner, daemon=True)
            t.start()
            _server_started = True
            time.sleep(0.5)


# Check if running under Streamlit
try:
    import streamlit as st
    is_streamlit = st.runtime.exists()
except Exception:
    is_streamlit = False

if is_streamlit:
    _start_flask_server()
    st.set_page_config(
        page_title="ScamShield AI • Cyber Scam Defense",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    # Hide default Streamlit chrome to display pure Cyber-Shield UI
    st.markdown(
        """
        <style>
        #MainMenu, header[data-testid="stHeader"], footer { visibility: hidden !important; display: none !important; }
        .block-container { padding: 0 !important; max-width: 100vw !important; margin: 0 !important; }
        iframe { width: 100% !important; min-height: 98vh !important; border: none !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    import streamlit.components.v1 as components
    components.iframe(f"http://127.0.0.1:{FLASK_PORT}", height=1100, scrolling=True)
else:
    if __name__ == "__main__":
        from run import main
        main()
