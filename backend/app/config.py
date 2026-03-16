from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    database_url: str = "sqlite+aiosqlite:///./finmate.db"
    cors_origins: str = "http://localhost:5173"

    model_config = {
        "env_file": str(Path(__file__).resolve().parent.parent.parent / ".env"),
        "env_file_encoding": "utf-8",
    }


settings = Settings()
