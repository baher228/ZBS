"""Optional MuBit learning setup for LLM-backed agents."""

from __future__ import annotations

import logging
import os

from app.core.config import settings

logger = logging.getLogger(__name__)

_INITIALIZED = False


def initialize_mubit_learning() -> bool:
    """Initialize mubit.learn once when MuBit is configured.

    MuBit remains fully optional: local mock mode and deployments without a
    MUBIT_API_KEY keep the current behavior.
    """
    global _INITIALIZED

    if _INITIALIZED:
        return True
    if not settings.should_initialize_mubit:
        return False

    _apply_endpoint_env()

    try:
        import mubit.learn as mubit_learn
    except ImportError:
        logger.warning("MUBIT_API_KEY is set but mubit-sdk is not installed; skipping MuBit learning")
        return False

    try:
        mubit_learn.init(
            api_key=settings.mubit_api_key,
            agent_id=settings.mubit_agent_id,
        )
    except Exception:
        logger.exception("Failed to initialize MuBit learning; continuing without MuBit")
        return False

    _INITIALIZED = True
    logger.info("MuBit learning initialized for agent '%s'", settings.mubit_agent_id)
    return True


def _apply_endpoint_env() -> None:
    values = {
        "MUBIT_ENDPOINT": settings.mubit_endpoint,
        "MUBIT_HTTP_ENDPOINT": settings.mubit_http_endpoint,
        "MUBIT_GRPC_ENDPOINT": settings.mubit_grpc_endpoint,
        "MUBIT_TRANSPORT": settings.mubit_transport,
    }
    for key, value in values.items():
        if value:
            os.environ.setdefault(key, value)


def _reset_mubit_for_tests() -> None:
    global _INITIALIZED
    _INITIALIZED = False
