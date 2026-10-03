"""ScamShield package."""
from .analyzer import analyze_screenshot
from .alert import send_alert
from .i18n import get_string

__all__ = ["analyze_screenshot", "send_alert", "get_string"]
__version__ = "1.0.0"
