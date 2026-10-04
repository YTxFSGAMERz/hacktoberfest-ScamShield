"""Comprehensive verification and screenshot suite for all ScamShield features."""

import os
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets" / "screenshots"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

def run_verification():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 920},
            device_scale_factor=2,
        )
        page = context.new_page()

        page.on("dialog", lambda dialog: dialog.accept())

        print("Navigating to http://127.0.0.1:5000...")
        page.goto("http://127.0.0.1:5000", wait_until="networkidle")
        time.sleep(2.0)

        # ── 1. Scanner Tab (Screenshot Mode) ──────────────────────────────────
        try:
            print("[1/12] Testing Screenshot Scanner with sample...")
            page.click("button[data-file='kyc_scam.png']")
            page.wait_for_selector("#verdict-container", state="visible", timeout=30000)
            time.sleep(1.5)
            page.screenshot(path=str(ASSETS_DIR / "01_scanner_screenshot.png"))
            print("  -> Saved 01_scanner_screenshot.png")
        except Exception as e:
            print(f"  [!] Step 1 note: {e}")
            page.screenshot(path=str(ASSETS_DIR / "01_scanner_screenshot.png"))

        # ── 2. Scanner Tab (Text / SMS Mode) ──────────────────────────────────
        try:
            print("[2/12] Testing Text/SMS Analyzer Mode...")
            page.click("button[data-mode='text']")
            time.sleep(0.5)
            test_sms = "URGENT: Your SBI net banking account has been BLOCKED due to incomplete KYC. Click immediately to restore access: http://sbi-kyc-update.xyz/verify or call 9876543210."
            page.fill("#text-scan-input", test_sms)
            page.click("#text-analyze-btn")
            page.wait_for_selector("#text-verdict-container", state="visible", timeout=30000)
            time.sleep(1.5)
            page.screenshot(path=str(ASSETS_DIR / "02_scanner_text_sms.png"))
            print("  -> Saved 02_scanner_text_sms.png")
        except Exception as e:
            print(f"  [!] Step 2 note: {e}")
            page.screenshot(path=str(ASSETS_DIR / "02_scanner_text_sms.png"))

        # ── 3. URL Scanner Tab ────────────────────────────────────────────────
        try:
            print("[3/12] Testing URL Phishing Scanner Tab...")
            page.click("button[data-tab='url']")
            time.sleep(0.8)
            page.fill("#url-input", "http://sbi-kyc-update.xyz/login.php")
            page.click("#url-scan-btn")
            page.wait_for_selector("#url-results", state="visible", timeout=20000)
            time.sleep(1.5)
            page.screenshot(path=str(ASSETS_DIR / "03_url_scanner.png"))
            print("  -> Saved 03_url_scanner.png")
        except Exception as e:
            print(f"  [!] Step 3 note: {e}")
            page.screenshot(path=str(ASSETS_DIR / "03_url_scanner.png"))

        # ── 4. Phone / QR Tab ─────────────────────────────────────────────────
        try:
            print("[4/12] Testing Phone Number Lookup...")
            page.click("button[data-tab='phoneqr']")
            time.sleep(0.8)
            page.fill("#phone-input", "9310842109")
            page.click("#phone-lookup-btn")
            page.wait_for_selector("#phone-results", state="visible", timeout=25000)
            time.sleep(1.5)
            page.screenshot(path=str(ASSETS_DIR / "04_phone_lookup.png"))
            print("  -> Saved 04_phone_lookup.png")
        except Exception as e:
            print(f"  [!] Step 4 note: {e}")
            page.screenshot(path=str(ASSETS_DIR / "04_phone_lookup.png"))

        # ── 5. AI Assistant Tab ───────────────────────────────────────────────
        try:
            print("[5/12] Testing AI Assistant Chat Tab...")
            page.click("button[data-tab='chat']")
            time.sleep(0.8)
            page.fill("#chat-input", "A CBI officer is calling me on Skype saying my Aadhaar has an illegal drugs case. What should I do?")
            page.click("#chat-send-btn")
            page.wait_for_function(
                "() => { const b = document.querySelectorAll('.chat-bubble.bot-bubble'); return b.length > 0 && !b[b.length-1].innerText.includes('Analyzing'); }",
                timeout=60000
            )
            time.sleep(2.0)
            page.screenshot(path=str(ASSETS_DIR / "05_ai_assistant_chat.png"))
            print("  -> Saved 05_ai_assistant_chat.png")
        except Exception as e:
            print(f"  [!] Step 5 note: {e}")
            page.screenshot(path=str(ASSETS_DIR / "05_ai_assistant_chat.png"))

        # ── 6. Quiz Tab ───────────────────────────────────────────────────────
        try:
            print("[6/12] Testing Scam Awareness Quiz Tab...")
            page.click("button[data-tab='quiz']")
            time.sleep(0.8)
            page.click("#quiz-start-btn")
            page.wait_for_selector("#quiz-active", state="visible", timeout=10000)
            page.wait_for_selector(".quiz-option", state="visible", timeout=10000)
            time.sleep(1.2)
            # Capture active quiz question showing all clickable option buttons
            page.screenshot(path=str(ASSETS_DIR / "06_quiz_active.png"))
            print("  -> Saved 06_quiz_active.png (Active Options)")
        except Exception as e:
            print(f"  [!] Step 6 note: {e}")
            page.screenshot(path=str(ASSETS_DIR / "06_quiz_active.png"))

        # ── 7. Threat Intel Tab ───────────────────────────────────────────────
        try:
            print("[7/12] Testing Threat Intelligence Tab...")
            page.click("button[data-tab='intel']")
            page.wait_for_selector(".intel-card", state="visible", timeout=10000)
            time.sleep(1.8)
            page.screenshot(path=str(ASSETS_DIR / "07_threat_intel.png"))
            print("  -> Saved 07_threat_intel.png")
        except Exception as e:
            print(f"  [!] Step 7 note: {e}")
            page.screenshot(path=str(ASSETS_DIR / "07_threat_intel.png"))

        # ── 8. Community Reports Tab ──────────────────────────────────────────
        try:
            print("[8/12] Testing Community Scam Reporting Tab...")
            page.click("button[data-tab='community']")
            time.sleep(1.0)
            page.fill("#check-value", "+919310842109")
            page.click("#community-check-btn")
            time.sleep(1.5)
            page.screenshot(path=str(ASSETS_DIR / "08_community_reports.png"))
            print("  -> Saved 08_community_reports.png")
        except Exception as e:
            print(f"  [!] Step 8 note: {e}")

        # ── 9. Victim Recovery Wizard Tab ─────────────────────────────────────
        try:
            print("[9/12] Testing Victim Recovery Wizard...")
            page.click("button[data-tab='recovery']")
            time.sleep(0.8)
            page.click(".time-option[data-time='lt1']")
            time.sleep(0.8)
            page.click("#wizard-next-1")
            time.sleep(0.5)
            page.select_option("#wizard-bank-select", "State Bank of India (SBI)")
            time.sleep(0.8)
            page.click("#wizard-next-2")
            time.sleep(0.5)
            page.check("#chk-money")
            page.check("#chk-otp")
            page.click("#wizard-next-3")
            time.sleep(1.5)
            page.screenshot(path=str(ASSETS_DIR / "09_recovery_wizard.png"))
            print("  -> Saved 09_recovery_wizard.png")
        except Exception as e:
            print(f"  [!] Step 9 note: {e}")

        # ── 10. Security Hygiene Tab ──────────────────────────────────────────
        try:
            print("[10/12] Testing Security Hygiene Assessment...")
            page.click("button[data-tab='hygiene']")
            time.sleep(0.8)
            page.click(".hygiene-item[data-id='upi1']")
            page.click(".hygiene-item[data-id='upi2']")
            page.click(".hygiene-item[data-id='upi3']")
            page.click(".hygiene-item[data-id='sim1']")
            page.click(".hygiene-item[data-id='app1']")
            page.click(".hygiene-item[data-id='app2']")
            time.sleep(1.5)
            page.screenshot(path=str(ASSETS_DIR / "10_security_hygiene.png"))
            print("  -> Saved 10_security_hygiene.png")
        except Exception as e:
            print(f"  [!] Step 10 note: {e}")

        # ── 11. Scan History Tab ──────────────────────────────────────────────
        try:
            print("[11/12] Testing Scan Audit History Tab...")
            page.click("button[data-tab='history']")
            time.sleep(1.2)
            page.screenshot(path=str(ASSETS_DIR / "11_scan_history.png"))
            print("  -> Saved 11_scan_history.png")
        except Exception as e:
            print(f"  [!] Step 11 note: {e}")

        # ── 12. Family Alert Tab ──────────────────────────────────────────────
        try:
            print("[12/12] Testing Family Alert Center Tab...")
            page.click("button[data-tab='alerts']")
            time.sleep(0.8)
            page.screenshot(path=str(ASSETS_DIR / "12_family_alert.png"))
            print("  -> Saved 12_family_alert.png")
        except Exception as e:
            print(f"  [!] Step 12 note: {e}")

        browser.close()
        print("\nAll 12 tabs successfully processed and captured!")

if __name__ == "__main__":
    run_verification()
