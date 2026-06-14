from fastapi import APIRouter, Depends, Request

from app.core.auth import get_current_user
from app.core.templates import render

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/home")
async def home(request: Request):
    return render(request, "home.html", {"active_page": "home"})
