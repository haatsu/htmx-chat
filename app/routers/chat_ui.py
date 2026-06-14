from fastapi import APIRouter, Depends, Request

from app.core.auth import get_current_user
from app.core.templates import render

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/chat-ui")
async def chat_ui(request: Request):
    return render(request, "chat_ui.html", {
        "active_page": "chat",
        "thread_id": request.cookies.get("session_token"),
    })
