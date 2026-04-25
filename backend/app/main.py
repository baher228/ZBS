from fastapi import APIRouter, FastAPI

from app.api.routes.health import router as health_router
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.app_debug,
    )

    api_v1_router = APIRouter(prefix="/api/v1")
    api_v1_router.include_router(health_router)

    @app.get("/")
    def root() -> dict[str, str]:
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.app_env,
        }

    app.include_router(api_v1_router)
    return app


app = create_app()
