from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    google_api_key: str
    default_model: str = "gemini-2.5-flash"


@lru_cache
def get_settings() -> Settings:
    """設定のシングルトンを返す(起動時に必須変数の欠落を検出する)。"""
    return Settings()
