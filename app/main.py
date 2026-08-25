from fastapi import FastAPI

from app.api.routes.database import router as database_router
from app.api.routes.documents import router as documents_router
from app.api.routes.health import router as health_router
from app.api.routes.questions import router as questions_router
from app.infrastructure.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="1.0.0")
    app.include_router(health_router)
    app.include_router(documents_router, prefix=settings.api_prefix)
    app.include_router(questions_router, prefix=settings.api_prefix)
    app.include_router(database_router, prefix=settings.api_prefix)
    return app


app = create_app()
