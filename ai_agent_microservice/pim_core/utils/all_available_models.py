from __future__ import annotations

from enum import Enum


class AllAvailableModelsAnthropic(str, Enum):
    """All supported Anthropic Claude models.

    When Anthropic releases a new model, add it here first.
    The factory and agent_registry route read from this enum —
    no other file needs updating.
    """
    CLAUDE_OPUS_4_6 = "claude-opus-4-6"
    CLAUDE_SONNET_4_6 = "claude-sonnet-4-6"
    CLAUDE_HAIKU_4_5 = "claude-haiku-4-5-20251001"


class AllAvailableModelsOpenAI(str, Enum):
    """All supported OpenAI models.

    When OpenAI releases a new model, add it here first.
    """
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4_TURBO = "gpt-4-turbo"
    O1 = "o1"
    O1_MINI = "o1-mini"
    O3_MINI = "o3-mini"
    O4_MINI = "o4-mini"


class AllAvailableModelsGoogle(str, Enum):
    """All supported Google Gemini models.

    When Google releases a new model, add it here first.
    """
    GEMINI_2_0_FLASH = "gemini-2.0-flash"
    GEMINI_1_5_PRO = "gemini-1.5-pro"
    GEMINI_1_5_FLASH = "gemini-1.5-flash"
