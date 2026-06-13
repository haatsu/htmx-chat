from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from app.core.auth import create_token
from app.core.templates import templates

router = APIRouter()


@router.get("/")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/launch")
async def launch(username: str = Form(..., min_length=1)):
    token = create_token(username)
    response = RedirectResponse(url="/home", status_code=303)
    response.set_cookie("session_token", token, httponly=True, samesite="lax", max_age=86400)
    return response
