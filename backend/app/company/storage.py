from __future__ import annotations

import json
import logging
from pathlib import Path

from app.company.models import CompanyProfile
from app.core.config import BACKEND_ROOT
from app.company.context_store import get_enriched_context

logger = logging.getLogger(__name__)

DATA_DIR = BACKEND_ROOT / "data"
PROFILE_JSON = DATA_DIR / "company_profile.json"
PROFILE_MD = DATA_DIR / "company_profile.md"


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def save_profile(profile: CompanyProfile) -> Path:
    _ensure_data_dir()
    PROFILE_JSON.write_text(profile.model_dump_json(indent=2), encoding="utf-8")
    PROFILE_MD.write_text(profile.to_markdown(), encoding="utf-8")
    logger.info("Company profile saved: %s", profile.name)
    return PROFILE_MD


def load_profile() -> CompanyProfile | None:
    if not PROFILE_JSON.exists():
        return None
    try:
        raw = PROFILE_JSON.read_text(encoding="utf-8")
        return CompanyProfile.model_validate(json.loads(raw))
    except Exception:
        logger.exception("Failed to load company profile")
        return None


def delete_profile() -> bool:
    deleted = False
    for path in (PROFILE_JSON, PROFILE_MD):
        if path.exists():
            path.unlink()
            deleted = True
    return deleted


def get_company_context() -> str | None:
    profile = load_profile()
    if profile is None:
        return None
    base = profile.to_context_string()
    enriched = get_enriched_context()
    if enriched:
        return base + "\n\n" + enriched
    return base
