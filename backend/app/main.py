from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.campaigns import router as campaigns_router
from app.api.routes.company import router as company_router
from app.api.routes.demo_sessions import router as demo_sessions_router
from app.api.routes.health import router as health_router
from app.api.routes.live_demo import router as live_demo_router
from app.api.routes.tasks import router as tasks_router
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.app_debug,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.resolved_cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api_v1_router = APIRouter(prefix="/api/v1")
    api_v1_router.include_router(health_router)
    api_v1_router.include_router(campaigns_router)
    api_v1_router.include_router(company_router)
    api_v1_router.include_router(tasks_router)
    api_v1_router.include_router(demo_sessions_router)
    api_v1_router.include_router(live_demo_router)

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
