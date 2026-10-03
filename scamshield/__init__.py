"""ScamShield package."""
from .analyzer import analyze_screenshot
from .alert import send_alert
from .i18n import get_string, SUPPORTED_LANGUAGES, t
from .chat import chat_with_scamshield
from .intel import EMERGENCY_CONTACTS, SCAM_TRENDS, GOLDEN_HOUR_STEPS

__all__ = [
    "analyze_screenshot",
    "send_alert",
    "get_string",
    "chat_with_scamshield",
    "EMERGENCY_CONTACTS",
    "SCAM_TRENDS",
    "GOLDEN_HOUR_STEPS",
    "SUPPORTED_LANGUAGES",
    "t",
]
__version__ = "1.1.0"

