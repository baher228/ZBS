from fastapi import APIRouter

from app.agents.llm import get_last_llm_error
from app.core.config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/provider")
def provider_info() -> dict[str, str | int | None]:
    return {
        "provider": settings.resolved_llm_provider,
        "model": settings.resolved_llm_model,
        "timeout_seconds": settings.llm_timeout_seconds,
        "content_timeout_seconds": settings.llm_content_timeout_seconds,
        "max_retries": settings.llm_max_retries,
        "last_error": get_last_llm_error(),
    }
