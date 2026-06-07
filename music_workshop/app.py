"""Application-level configuration and resource paths."""

from __future__ import annotations

import logging
import os
import sys

# Load .env file from project root (if present) for API keys
try:
    from dotenv import load_dotenv

    _dotenv_loaded = load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except Exception:
    _dotenv_loaded = False

# Configure a simple root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)

_log = logging.getLogger(__name__)


def resource_path(sub_path: str = "") -> str:
    """Return the absolute path to a resource file.

    Resources live under ``music_workshop/resources/``.
    """
    base = os.path.join(os.path.dirname(__file__), "resources")
    return os.path.join(base, sub_path)


def startup() -> None:
    """Perform one-time initialisation at application launch."""
    _log.info("Music Workshop %s starting up ...", "0.1.0")
    if _dotenv_loaded:
        _log.info("Loaded .env file")
    if os.environ.get("DEEPSEEK_API_KEY"):
        _log.info("DeepSeek API key found")
    else:
        _log.warning("No DEEPSEEK_API_KEY set — AI features will use local fallback")
