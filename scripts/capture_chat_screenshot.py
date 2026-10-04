"""Capture high-resolution screenshot of the AI Assistant Chat view demonstrating Markdown & KaTeX LaTeX formatting."""

import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets" / "screenshots"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

def capture_chat():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 950},
            device_scale_factor=2,
        )
        page = context.new_page()
        page.on("dialog", lambda dialog: dialog.accept())

        print("Navigating to http://127.0.0.1:5000...")
        page.goto("http://127.0.0.1:5000", wait_until="networkidle")
        time.sleep(2.0)

        print("Navigating to Chat tab...")
        page.click("button[data-tab='chat']")
        time.sleep(1.0)

        print("Sending message to AI Assistant...")
        prompt = "Someone from CBI called me on Skype about an illegal narcotics parcel and put me under digital arrest. Explain why this is a scam, show the Golden Hour recovery equation in LaTeX, and tell me what to do immediately."
        page.fill("#chat-input", prompt)
        page.click("#chat-send-btn")

        print("Waiting for rich response from Gemma 4...")
        page.wait_for_function(
            "() => { const b = document.querySelectorAll('.chat-bubble.bot-bubble .md-content'); return b.length > 0 && !b[b.length-1].innerText.includes('Analyzing'); }",
            timeout=60000
        )
        time.sleep(2.0)
        # Scroll chat thread slightly to reveal the full response body
        page.evaluate("const ct = document.querySelector('#chat-thread'); if(ct) ct.scrollTop = 140;")
        time.sleep(0.8)

        out_path = ASSETS_DIR / "05_ai_assistant_chat.png"
        page.screenshot(path=str(out_path))
        print(f"Captured: {out_path}")
        browser.close()

if __name__ == "__main__":
    capture_chat()
