from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles

from app.core.ai import create_model
from app.core.config import get_settings

from app.routers import chat


async def lifespan(app: FastAPI):
    """起動時にクライアントを生成し、終了時に解放する。"""
    settings = get_settings()
    default = settings.default_model
    app.state.models = {default: create_model(default)}

    yield


def create_app() -> FastAPI:
    """アプリケーションを構築する。"""
    app = FastAPI(lifespan=lifespan, docs_url="/docs", redoc_url=None)
    # app.mount("/static", StaticFiles(directory="app/static"), name="static")

    # register_error_handlers(app)
    # app.include_router(launch.router)
    # app.include_router(home.router)
    # app.include_router(ir.router)
    app.include_router(chat.router)

    @app.get("/healthz", response_class=PlainTextResponse)
    async def healthz() -> str:
        """死活監視用。認証不要。"""
        return "ok"

    return app


app = create_app()
