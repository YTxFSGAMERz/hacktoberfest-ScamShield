"""Script to capture pixel-perfect screenshots of the Cyber-Shield UI for README assets."""

import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

def capture():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(
            viewport={"width": 1360, "height": 880},
            device_scale_factor=2,  # Retina crispness
        )
        page = context.new_page()
        page.on("console", lambda msg: print(f"[BROWSER] {msg.type}: {msg.text}"))
        page.on("dialog", lambda dialog: print(f"[DIALOG] {dialog.message}") or dialog.accept())

        print("Navigating to http://127.0.0.1:5000...")
        page.goto("http://127.0.0.1:5000", wait_until="networkidle")
        time.sleep(1)

        # 1. Capture Scanner with a live analysis
        print("Clicking 'SBI KYC Block' sample...")
        page.click("button[data-file='kyc_scam.png']")
        
        # Wait for analysis verdict to render
        print("Waiting for verdict display...")
        page.wait_for_selector("#verdict-container", state="visible", timeout=45000)
        time.sleep(2.0)  # Let CSS animations and score meter complete

        scanner_path = ASSETS_DIR / "preview_scanner.png"
        page.screenshot(path=str(scanner_path), full_page=False)
        print(f"Saved scanner preview to: {scanner_path}")

        # 2. Switch to Chat tab & send a query
        print("Switching to AI Assistant tab...")
        page.click("button[data-tab='chat']")
        time.sleep(1.0)

        print("Typing and sending cyber-safety question...")
        page.fill("#chat-input", "Someone claiming to be Mumbai Police called saying I am under Digital Arrest for a suspicious courier. What should I do?")
        page.click("#chat-send-btn")

        print("Waiting for AI assistant response...")
        # Wait until the bot placeholder text is replaced
        page.wait_for_function(
            "() => { const bubbles = document.querySelectorAll('.chat-bubble.bot-bubble p'); return bubbles.length > 1 && !bubbles[bubbles.length - 1].innerText.includes('Analyzing'); }",
            timeout=45000
        )
        time.sleep(2.0)

        chat_path = ASSETS_DIR / "preview_chat.png"
        page.screenshot(path=str(chat_path), full_page=False)
        print(f"Saved chat preview to: {chat_path}")

        # 3. Threat Intel Tab Preview
        print("Switching to Threat Intel tab...")
        page.click("button[data-tab='intel']")
        time.sleep(1.5)

        intel_path = ASSETS_DIR / "preview_intel.png"
        page.screenshot(path=str(intel_path), full_page=False)
        print(f"Saved threat intel preview to: {intel_path}")

        browser.close()
        print("All screenshots successfully captured!")

if __name__ == "__main__":
    capture()
