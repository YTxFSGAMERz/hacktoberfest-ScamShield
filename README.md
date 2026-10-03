# 🛡️ ScamShield

**ScamShield** is an AI-powered scam detection tool built with Gemma 4. Upload a screenshot of a suspicious message, call, or website and get an instant risk analysis — in English, Hindi, or Gujarati.

Built for Hacktoberfest 2026.

---

## ✨ Features

- 🤖 **Gemma 4 AI** — Uses `gemma-4-26b-a4b-it` via Gemini API (primary) or local Ollama `gemma4:e4b` (fallback)
- 🌍 **Trilingual** — English, Hindi (हिंदी), and Gujarati (ગુજરાતી) UI and AI output
- 📸 **Screenshot Analysis** — Upload images of scam messages, phishing sites, fake UPI apps
- 🚨 **Family Alert** — One-click Discord webhook notification to warn family members
- 📋 **Copy Fallback** — If Discord isn't configured, copies alert text to clipboard
- 🎯 **Risk Scoring** — Clear SAFE / SUSPICIOUS / SCAM verdict with confidence score

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- A [Gemini API key](https://aistudio.google.com/apikey) (free tier works)
- Optionally: [Ollama](https://ollama.com) with `gemma4:e4b` for offline fallback

### Installation

```bash
git clone https://github.com/YTxFSGAMERz/hacktoberfest-ScamShield
cd hacktoberfest-ScamShield

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure secrets
copy .env.example .env
# Edit .env with your keys
```

### Configuration (`.env`)

```env
# Required: Gemini API key from https://aistudio.google.com/apikey
GEMINI_API_KEY=AIza...

# Optional: Discord webhook for family alerts
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# AI provider: auto | gemini | ollama
LLM_PROVIDER=auto

# Gemini model (official Gemma 4 model on Gemini API)
GEMINI_MODEL=gemma-4-26b-a4b-it

# Ollama model
OLLAMA_MODEL=gemma4:e4b
OLLAMA_BASE_URL=http://localhost:11434
```

### Run

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501)

## 🏗️ Architecture

```
ScamShield/
├── app.py              # Streamlit UI (trilingual)
├── scamshield/
│   ├── analyzer.py     # Core AI scam analysis logic
│   ├── llm.py          # LLM provider (Gemini API / Ollama with auto-fallback)
│   ├── alert.py        # Discord webhook + clipboard fallback
│   ├── i18n.py         # English / Hindi / Gujarati strings
│   └── prompts.py      # Gemma 4 prompt templates
├── tests/
│   ├── test_analyzer.py
│   ├── test_llm.py
│   └── samples/        # Sample scam screenshots for testing
├── .env.example
├── requirements.txt
└── README.md
```

## 🧪 Sample Tests

The `tests/samples/` folder includes synthetic scam screenshots for:
- Fake KYC/bank SMS
- UPI phishing
- Lottery scam (Nigerian prince variant)
- Job offer scam
- Fake government notice

Run tests:
```bash
pytest tests/ -v
```

## 🌐 Languages

| Language | UI | AI Output |
|----------|-----|-----------|
| English | ✅ | ✅ |
| Hindi | ✅ | ✅ |
| Gujarati | ✅ | ✅ |

## 🔒 Privacy

- Images are analyzed in-memory and never stored to disk
- No analytics or tracking
- API keys stay in your local `.env` file

## 🤝 Contributing

This project is part of Hacktoberfest 2026! Check the [Issues](../../issues) for good first issues.

## 📄 License

MIT — see [LICENSE](LICENSE)
