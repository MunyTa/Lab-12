from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from taskboard.config import get_settings
from taskboard.database import Base, engine
from taskboard.routers import admin, analytics, auth, boards, cards, comments, lists


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Path("data").mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    @app.get("/health")
    def health() -> dict[str, bool]:
        return {"ok": True}

    app.include_router(auth.router)
    app.include_router(boards.router)
    app.include_router(lists.router)
    app.include_router(cards.router)
    app.include_router(comments.router)
    app.include_router(analytics.router)
    app.include_router(admin.router)
    return app


app = create_app()
