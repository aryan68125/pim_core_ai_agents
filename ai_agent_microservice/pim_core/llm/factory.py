from __future__ import annotations

from pim_core.llm.providers.base import BaseLLMProvider
from pim_core.utils.all_available_models import (
    AllAvailableModelsAnthropic,
    AllAvailableModelsGoogle,
    AllAvailableModelsOpenAI,
)

_instances: dict[str, BaseLLMProvider] = {}

# Derive valid model name sets directly from the enums — no hardcoded strings.
_ANTHROPIC_MODELS: frozenset[str] = frozenset(m.value for m in AllAvailableModelsAnthropic)
_OPENAI_MODELS: frozenset[str] = frozenset(m.value for m in AllAvailableModelsOpenAI)
_GOOGLE_MODELS: frozenset[str] = frozenset(m.value for m in AllAvailableModelsGoogle)


def get_provider(model_name: str) -> BaseLLMProvider:
    """Return the cached provider instance for the given model name.

    Provider is determined by looking the model name up in the enum sets:
    - AllAvailableModelsAnthropic → AnthropicProvider
    - AllAvailableModelsOpenAI    → OpenAIProvider
    - AllAvailableModelsGoogle    → GoogleProvider

    Raises:
        ValueError: When the model is not listed in any of the three enums.
    """
    if model_name in _ANTHROPIC_MODELS:
        key = "anthropic"
        if key not in _instances:
            from pim_core.llm.providers.anthropic_provider import AnthropicProvider
            _instances[key] = AnthropicProvider()
        return _instances[key]

    if model_name in _OPENAI_MODELS:
        key = "openai"
        if key not in _instances:
            from pim_core.llm.providers.openai_provider import OpenAIProvider
            _instances[key] = OpenAIProvider()
        return _instances[key]

    if model_name in _GOOGLE_MODELS:
        key = "google"
        if key not in _instances:
            from pim_core.llm.providers.google_provider import GoogleProvider
            _instances[key] = GoogleProvider()
        return _instances[key]

    all_models = sorted(_ANTHROPIC_MODELS | _OPENAI_MODELS | _GOOGLE_MODELS)
    raise ValueError(
        f"No provider found for model '{model_name}'. "
        f"Supported models: {', '.join(all_models)}"
    )
