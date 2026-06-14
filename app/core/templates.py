from fastapi import Request
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")


def render(request: Request, template_name: str, context: dict = {}) -> templates.TemplateResponse:
    ctx = {
        "username": getattr(request.state, "user", None),
        "hx_request": request.headers.get("HX-Request") == "true",
        **context,
    }
    return templates.TemplateResponse(request, template_name, ctx)
