from fastapi import Request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.core.config import get_settings

TOKEN_MAX_AGE = 86400  # 24時間


class RequiresLoginException(Exception):
    pass


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(get_settings().secret_key)


def create_token(username: str) -> str:
    return _serializer().dumps({"username": username})


def decode_token(token: str) -> str | None:
    try:
        data = _serializer().loads(token, max_age=TOKEN_MAX_AGE)
        return data["username"]
    except (BadSignature, SignatureExpired, KeyError):
        return None


def get_current_user(request: Request) -> str:
    token = request.cookies.get("session_token")
    if token:
        username = decode_token(token)
        if username:
            request.state.user = username
            return username
    raise RequiresLoginException()
