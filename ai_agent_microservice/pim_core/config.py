from pydantic_settings import BaseSettings
from pydantic import ConfigDict

from pim_core.utils.all_available_models import AllAvailableModelsAnthropic


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")

    anthropic_api_key: str
    openai_api_key: str | None = None
    google_api_key: str | None = None
    environment: str = "development"
    log_level: str = "INFO"
    claude_model: str = AllAvailableModelsAnthropic.CLAUDE_SONNET_4_6.value


settings = Settings()
