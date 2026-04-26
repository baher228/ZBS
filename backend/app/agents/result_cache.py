from __future__ import annotations

import hashlib
import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

from app.core.config import BACKEND_ROOT, settings

logger = logging.getLogger(__name__)

DATA_DIR = BACKEND_ROOT / "data"
CACHE_JSON = DATA_DIR / "agent_result_cache.json"
CACHE_VERSION = "v1"

ModelT = TypeVar("ModelT", bound=BaseModel)

_lock = threading.RLock()


def cache_key(namespace: str, payload: dict[str, Any]) -> str:
    normalized = json.dumps(_jsonable(payload), sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"{CACHE_VERSION}:{namespace}:{digest}"


def get_cached_model(key: str, model_type: type[ModelT]) -> ModelT | None:
    if not settings.agent_cache_enabled:
        return None
    entry = _read_cache().get(key)
    if not isinstance(entry, dict):
        return None
    payload = entry.get("payload")
    if not isinstance(payload, dict):
        return None
    try:
        return model_type.model_validate(payload)
    except Exception:
        logger.warning("Ignoring invalid cached agent result for %s", key, exc_info=True)
        return None


def set_cached_model(key: str, value: BaseModel) -> None:
    if not settings.agent_cache_enabled:
        return
    payload = value.model_dump(mode="json")
    with _lock:
        cache = _read_cache_unlocked()
        cache[key] = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }
        _trim_cache(cache)
        _write_cache_unlocked(cache)


def clear_agent_cache() -> None:
    with _lock:
        if CACHE_JSON.exists():
            CACHE_JSON.unlink()


def _read_cache() -> dict[str, dict[str, Any]]:
    with _lock:
        return _read_cache_unlocked()


def _read_cache_unlocked() -> dict[str, dict[str, Any]]:
    if not CACHE_JSON.exists():
        return {}
    try:
        raw = CACHE_JSON.read_text(encoding="utf-8")
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        logger.warning("Failed to read agent result cache", exc_info=True)
        return {}


def _write_cache_unlocked(cache: dict[str, dict[str, Any]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temp_path = Path(str(CACHE_JSON) + ".tmp")
    temp_path.write_text(json.dumps(cache, indent=2, sort_keys=True), encoding="utf-8")
    temp_path.replace(CACHE_JSON)


def _trim_cache(cache: dict[str, dict[str, Any]]) -> None:
    max_entries = max(settings.agent_cache_max_entries, 1)
    if len(cache) <= max_entries:
        return
    ordered = sorted(
        cache.items(),
        key=lambda item: str(item[1].get("created_at", "")),
    )
    for key, _ in ordered[: len(cache) - max_entries]:
        cache.pop(key, None)


def _jsonable(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {str(key): _jsonable(nested) for key, nested in value.items()}
    if isinstance(value, list | tuple):
        return [_jsonable(item) for item in value]
    return value
