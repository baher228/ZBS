from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_ROOT.parent


class Settings(BaseSettings):
    app_name: str = "ZBS API"
    app_version: str = "0.1.0"
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    frontend_base_url: str = "http://localhost:5173"
    llm_provider: str = "mock"
    llm_model: str = "mock-gtm-v1"
    llm_api_key: str | None = None
    openai_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=(str(REPO_ROOT / ".env"), str(BACKEND_ROOT / ".env")),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def resolved_llm_api_key(self) -> str | None:
        return self.llm_api_key or self.openai_api_key


settings = Settings()
