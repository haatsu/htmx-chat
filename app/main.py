from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.core.ai import create_model
from app.core.auth import RequiresLoginException
from app.core.config import get_settings
from app.core.templates import templates
from app.routers import chat, chat_ui, home, launch


async def lifespan(app: FastAPI):
    settings = get_settings()
    default = settings.default_model
    app.state.models = {default: create_model(default)}
    yield


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan, docs_url="/docs", redoc_url=None)
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    app.include_router(launch.router)
    app.include_router(home.router)
    app.include_router(chat_ui.router)
    app.include_router(chat.router)

    @app.exception_handler(RequiresLoginException)
    async def requires_login_handler(request: Request, exc: RequiresLoginException):
        return RedirectResponse(url="/")

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):
        return templates.TemplateResponse(request, "errors/404.html", status_code=404)

    @app.exception_handler(500)
    async def server_error_handler(request: Request, exc):
        return templates.TemplateResponse(request, "errors/500.html", status_code=500)

    @app.get("/healthz", response_class=PlainTextResponse)
    async def healthz() -> str:
        return "ok"

    return app


app = create_app()
