"""ScamShield AI — Local Application Runner.

Launches the unified Cyber-Shield Web Application & Gemma 4 API.
Visit http://127.0.0.1:5000 in your browser.
"""

from __future__ import annotations

import os
import sys
import webbrowser
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from api.index import app

def main() -> None:
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "127.0.0.1")
    url = f"http://{host}:{port}"
    print("=" * 60)
    print(f"🛡️  SCAMSHIELD AI • LOCAL SERVER")
    print(f"🌐  Serving Cyber-Shield UI at: {url}")
    print(f"⚡  AI Provider & Failover Engine: Active")
    print("=" * 60)
    
    if os.environ.get("SCAMSHIELD_AUTO_BROWSER", "1") == "1":
        try:
            webbrowser.open(url)
        except Exception:
            pass

    app.run(host=host, port=port, debug=False)

if __name__ == "__main__":
    main()
