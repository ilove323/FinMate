from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    volcengine_api_key: str = ""
    volcengine_model: str = "doubao-pro-32k-241215"
    volcengine_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    database_url: str = "sqlite+aiosqlite:///./finmate.db"
    cors_origins: str = "http://localhost:5173"

    model_config = {
        "env_file": str(Path(__file__).resolve().parent.parent.parent / ".env"),
        "env_file_encoding": "utf-8",
    }


settings = Settings()
