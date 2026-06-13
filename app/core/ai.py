from fastapi import Request
from langchain.chat_models import init_chat_model

from app.core.config import get_settings


def create_model(model_name: str):
    settings = get_settings()
    return init_chat_model(
        model=model_name,
        model_provider="google_genai",
        google_api_key=settings.google_api_key,
    )


def get_model(request: Request, model_name: str = ""):
    name = model_name or get_settings().default_model
    models = request.app.state.models
    if name not in models:
        models[name] = create_model(name)
    return models[name]
