from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/provider")
def provider_info() -> dict[str, str]:
    return {
        "provider": settings.resolved_llm_provider,
        "model": settings.resolved_llm_model,
    }
