"""ScamShield — Victim Recovery Assistant & Emergency Guide.

Provides step-by-step incident response, golden hour calculation,
and official bank/app fraud helplines for Indian financial fraud victims.
"""

from __future__ import annotations

# ── Major Bank & FinTech Fraud Helplines (India) ─────────────────────────────
BANK_NUMBERS: dict[str, dict[str, str]] = {
    "State Bank of India (SBI)": {
        "toll_free": "1800 1234 / 1800 2100",
        "fraud_helpline": "1800 11 1109",
        "sms_block": "SMS 'BLOCK <last 4 digits>' to 567676",
        "portal": "https://www.onlinesbi.sbi",
    },
    "HDFC Bank": {
        "toll_free": "1800 202 6161 / 1860 267 6161",
        "fraud_helpline": "1800 258 3838",
        "sms_block": "SMS 'BLOCK' to 5676712",
        "portal": "https://www.hdfcbank.com",
    },
    "ICICI Bank": {
        "toll_free": "1800 1080",
        "fraud_helpline": "1800 2662",
        "sms_block": "SMS 'BLOCK <card number>' to 5676766",
        "portal": "https://www.icicibank.com",
    },
    "Axis Bank": {
        "toll_free": "1860 419 5555 / 1860 500 5555",
        "fraud_helpline": "1800 209 5577",
        "sms_block": "SMS 'BLOCK <card number>' to 5676782",
        "portal": "https://www.axisbank.com",
    },
    "Kotak Mahindra Bank": {
        "toll_free": "1860 266 2666",
        "fraud_helpline": "1800 209 0000",
        "sms_block": "SMS 'DCBLOCK <last 4 digits>' to 9971056767",
        "portal": "https://www.kotak.com",
    },
    "Punjab National Bank (PNB)": {
        "toll_free": "1800 180 2222 / 1800 103 2222",
        "fraud_helpline": "0120 2490000",
        "sms_block": "SMS 'HOT <Card No>' to 5607040",
        "portal": "https://www.pnbindia.in",
    },
    "Bank of Baroda": {
        "toll_free": "1800 5700 / 1800 5000",
        "fraud_helpline": "1800 258 4455",
        "sms_block": "SMS 'BLOCK <last 4 digits>' to 8422009988",
        "portal": "https://www.bankofbaroda.in",
    },
    "Canara Bank": {
        "toll_free": "1800 425 0018 / 1800 103 0018",
        "fraud_helpline": "080 25584040",
        "sms_block": "SMS 'BLOCK <card number>' to 9266623333",
        "portal": "https://canarabank.com",
    },
    "Union Bank of India": {
        "toll_free": "1800 22 22 44 / 1800 208 2244",
        "fraud_helpline": "080 61817110",
        "sms_block": "SMS 'UBLOCK <card number>' to 9223008486",
        "portal": "https://www.unionbankofindia.co.in",
    },
    "PhonePe": {
        "toll_free": "080-68727374 / 022-68727374",
        "fraud_helpline": "In-app: Help > Report a Problem > Fraud",
        "sms_block": "Block linked bank via bank helpline",
        "portal": "https://support.phonepe.com",
    },
    "Google Pay (GPay)": {
        "toll_free": "1800-419-0157",
        "fraud_helpline": "In-app: Profile > Help & Feedback > Raise Dispute",
        "sms_block": "De-register UPI number via bank",
        "portal": "https://support.google.com/pay/india",
    },
    "Paytm / Paytm Payments Bank": {
        "toll_free": "0120-4456-456",
        "fraud_helpline": "0120-3888-388 (24x7 Cyber Fraud)",
        "sms_block": "In-app: 24x7 Help > Report unauthorized charges",
        "portal": "https://paytm.com/care",
    },
}

# ── Golden Hour Status Calculator ─────────────────────────────────────────────
def get_golden_hour_status(minutes_elapsed: int) -> dict:
    """Calculate the urgency level and recovery chances based on elapsed time."""
    if minutes_elapsed <= 60:
        return {
            "status": "CRITICAL_GOLDEN_HOUR",
            "badge": "🚨 Active Golden Hour (< 1h)",
            "color": "#ef4444",
            "chance": "HIGH (70-90% account freeze probability)",
            "message": "Call 1930 immediately! The recipient fraud account can be frozen before ATM withdrawal.",
            "urgent_actions": [
                "Call 1930 (National Cyber Crime Helpline) NOW",
                "Keep UTR / Transaction Reference Number ready",
                "Contact your bank to place debit freeze / chargeback request",
            ],
        }
    elif minutes_elapsed <= 180:
        return {
            "status": "EXTENDED_GOLDEN_HOUR",
            "badge": "⚠️ Extended Window (1-3h)",
            "color": "#f97316",
            "chance": "MODERATE (40-60% freeze probability)",
            "message": "Act immediately. Scammers may begin transferring through mule accounts.",
            "urgent_actions": [
                "Call 1930 without delay",
                "Inform your bank fraud monitoring desk",
                "Submit e-FIR at cybercrime.gov.in",
            ],
        }
    elif minutes_elapsed <= 1440:
        return {
            "status": "POST_GOLDEN_HOUR",
            "badge": "⏳ Post Golden Hour (3-24h)",
            "color": "#eab308",
            "chance": "LOW-MODERATE (Funds may have moved to mule accounts)",
            "message": "File official complaint on cybercrime.gov.in and visit your bank branch with written complaint.",
            "urgent_actions": [
                "File formal cyber complaint at cybercrime.gov.in",
                "Submit written notice to your Home Branch with transaction proof",
                "Block compromised cards and reset Internet Banking credentials",
            ],
        }
    else:
        return {
            "status": "EXTENDED_TIMELINE",
            "badge": "📋 Beyond 24 Hours",
            "color": "#6b7280",
            "chance": "RECOVERY VIA LEGAL PROCESS",
            "message": "Follow statutory RBI guidelines for unauthorized electronic transactions within 3 days for zero/limited liability.",
            "urgent_actions": [
                "File official FIR at nearest Cyber Crime Police Station",
                "Submit written dispute under RBI Charter (Circular DBR.No.Leg.BC.78/09.07.005/2017-18)",
                "Preserve all chat transcripts, call recordings, and SMS as legal evidence",
            ],
        }
