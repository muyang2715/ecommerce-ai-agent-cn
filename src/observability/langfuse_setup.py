"""
Langfuse Observability — tracing, evaluation & cost tracking for the ReAct agent.

Configure via .env:
    LANGFUSE_PUBLIC_KEY=pk-lf-...
    LANGFUSE_SECRET_KEY=sk-lf-...
    LANGFUSE_HOST=https://cloud.langfuse.com   (or self-hosted)
"""
import logging
import os
from typing import Optional

from src.config import settings

logger = logging.getLogger(__name__)

_client = None
_handler = None


def _is_configured() -> bool:
    return bool(settings.langfuse_public_key and settings.langfuse_secret_key)


def init_langfuse():
    """Call once at app startup — sets env vars, then initializes client & handler."""
    global _client, _handler
    if _client is not None:
        return
    if not _is_configured():
        logger.info("Langfuse not configured — tracing disabled.")
        return

    # CRITICAL: Set env vars BEFORE any langfuse imports
    os.environ["LANGFUSE_PUBLIC_KEY"] = settings.langfuse_public_key
    os.environ["LANGFUSE_SECRET_KEY"] = settings.langfuse_secret_key
    os.environ["LANGFUSE_HOST"] = settings.langfuse_host

    from langfuse import Langfuse
    from langfuse.langchain import CallbackHandler

    _client = Langfuse()
    _handler = CallbackHandler()
    logger.info("Langfuse tracing enabled → %s", settings.langfuse_host)


def get_langfuse_handler():
    return _handler


def get_langfuse_client():
    return _client
    """Returns a Langfuse client for direct logging (scores, events, etc.)."""
    if not _is_configured():
        return None
    _ensure_env()
    return Langfuse()
