import os


def test_settings_has_anthropic_api_key():
    """Settings exposes ANTHROPIC_API_KEY from environment."""
    from pim_core.config import settings
    assert settings.anthropic_api_key == os.environ["ANTHROPIC_API_KEY"]


def test_settings_default_model_is_claude():
    """Default claude_model starts with 'claude-'."""
    from pim_core.config import settings
    assert settings.claude_model.startswith("claude-")


def test_settings_default_environment():
    """Default environment is 'development'."""
    from pim_core.config import settings
    assert settings.environment == "development"
