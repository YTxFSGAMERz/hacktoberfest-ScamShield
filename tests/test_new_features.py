"""Tests for ScamShield new feature modules & endpoints."""

import json
import pytest
from api.index import app
from scamshield.quiz_data import QUIZ_QUESTIONS, QUIZ_BADGES
from scamshield.victim_recovery import BANK_NUMBERS, get_golden_hour_status
from scamshield.hygiene import HYGIENE_CHECKS, calculate_hygiene_score
from scamshield.community import report_scam, check_community_reports, get_recent_reports
from scamshield.scanner_url import analyze_url
from scamshield.scanner_phone import analyze_phone


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ── Quiz & Intel Tests ─────────────────────────────────────────────────────────
def test_quiz_data_integrity():
    assert len(QUIZ_QUESTIONS) >= 40
    for q in QUIZ_QUESTIONS:
        assert "id" in q
        assert "difficulty" in q
        assert q["difficulty"] in ("beginner", "intermediate", "expert")
        assert "question_en" in q
        assert len(q["options"]) == 4
        # Exactly one correct option
        correct_count = sum(1 for o in q["options"] if o.get("is_correct"))
        assert correct_count == 1, f"Question {q['id']} has {correct_count} correct answers"


def test_quiz_badges():
    assert len(QUIZ_BADGES) >= 5
    for b in QUIZ_BADGES:
        assert "name" in b
        assert "icon" in b


def test_api_quiz_endpoint(client):
    res = client.get("/api/quiz?difficulty=beginner&limit=5")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert len(data["questions"]) <= 5
    assert len(data["badges"]) >= 5


# ── Recovery & Bank Tests ──────────────────────────────────────────────────────
def test_golden_hour_calculation():
    # < 60 mins -> Critical
    s1 = get_golden_hour_status(30)
    assert s1["status"] == "CRITICAL_GOLDEN_HOUR"

    # 1-3 hrs -> Extended
    s2 = get_golden_hour_status(120)
    assert s2["status"] == "EXTENDED_GOLDEN_HOUR"

    # > 24 hrs -> Legal route
    s3 = get_golden_hour_status(2000)
    assert s3["status"] == "EXTENDED_TIMELINE"


def test_api_victim_banks(client):
    res = client.get("/api/victim/banks")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "State Bank of India (SBI)" in data["banks"]
    assert "HDFC Bank" in data["banks"]
    assert "PhonePe" in data["banks"]


def test_api_victim_status(client):
    res = client.post("/api/victim/status", json={"minutes_elapsed": 45})
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "Golden Hour" in data["data"]["badge"]


# ── Hygiene Tests ─────────────────────────────────────────────────────────────
def test_hygiene_checks_count():
    assert len(HYGIENE_CHECKS) >= 15


def test_calculate_hygiene_score():
    # Empty -> F
    res_empty = calculate_hygiene_score([])
    assert res_empty["score"] == 0
    assert res_empty["grade"] == "F"

    # All checked -> A+
    all_ids = [c["id"] for c in HYGIENE_CHECKS]
    res_full = calculate_hygiene_score(all_ids)
    assert res_full["score"] == 100
    assert res_full["grade"] == "A+"


def test_api_hygiene_endpoints(client):
    res = client.get("/api/hygiene/checks")
    assert res.status_code == 200
    assert res.get_json()["total"] >= 15

    res2 = client.post("/api/hygiene/score", json={"checked_ids": ["upi_pin_private"]})
    assert res2.status_code == 200
    assert "score" in res2.get_json()["data"]


# ── Community Reporting Tests ──────────────────────────────────────────────────
def test_community_report_and_check():
    test_number = "+919999900001"
    # Report scam
    r = report_scam("phone", test_number, "Test scammer posing as CBI")
    assert r["success"] is True
    assert r["entry"]["reports_count"] >= 1

    # Check report
    chk = check_community_reports("phone", test_number)
    assert chk["found"] is True
    assert chk["reports_count"] >= 1


def test_api_community_endpoints(client):
    res = client.get("/api/community/recent")
    assert res.status_code == 200
    assert "reports" in res.get_json()

    res_chk = client.get("/api/community/check?type=phone&value=9310842109")
    assert res_chk.status_code == 200
    assert res_chk.get_json()["data"]["found"] is True


# ── URL Scanner Tests ──────────────────────────────────────────────────────────
def test_scanner_url_known_suspicious():
    res = analyze_url("http://sbi-kyc-update.xyz/login.php")
    assert "verdict" in res
    assert "risk_score" in res
    assert res["verdict"] in ("SCAM", "SUSPICIOUS")
    assert res["risk_score"] >= 50


def test_scanner_url_legitimate():
    res = analyze_url("https://www.sbi.co.in")
    assert res["verdict"] == "SAFE"
    assert res["risk_score"] <= 30


def test_api_scan_url(client):
    res = client.post("/api/scan/url", json={"url": "https://www.onlinesbi.sbi"})
    assert res.status_code == 200
    assert res.get_json()["data"]["verdict"] == "SAFE"


# ── Phone Scanner Tests ───────────────────────────────────────────────────────
def test_scanner_phone_prefix_check():
    res = analyze_phone("+91 9310 123456")
    assert "verdict" in res
    assert "risk_score" in res


def test_api_scan_phone(client):
    res = client.post("/api/scan/phone", json={"phone": "9876543210"})
    assert res.status_code == 200
    assert "verdict" in res.get_json()["data"]


# ── Languages Endpoint Test ───────────────────────────────────────────────────
def test_api_languages(client):
    res = client.get("/api/languages")
    assert res.status_code == 200
    langs = res.get_json()["languages"]
    assert "ta" in langs  # Tamil
    assert "te" in langs  # Telugu
    assert "bn" in langs  # Bengali
    assert "mr" in langs  # Marathi
    assert "kn" in langs  # Kannada
    assert "pa" in langs  # Punjabi
    assert "es" in langs  # Spanish
    assert "ja" in langs  # Japanese
