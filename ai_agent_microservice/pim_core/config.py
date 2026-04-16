from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")

    anthropic_api_key: str
    environment: str = "development"
    log_level: str = "INFO"
    claude_model: str = "claude-sonnet-4-6"


settings = Settings()
