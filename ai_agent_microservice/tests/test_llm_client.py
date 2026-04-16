import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_llm_client_complete_returns_text():
    """LLMClient.complete returns the text content from Anthropic response."""
    mock_content_block = MagicMock()
    mock_content_block.text = "Generated product description."
    mock_message = MagicMock()
    mock_message.content = [mock_content_block]

    with patch("anthropic.AsyncAnthropic") as MockAnthropic:
        mock_instance = MagicMock()
        mock_instance.messages.create = AsyncMock(return_value=mock_message)
        MockAnthropic.return_value = mock_instance

        from pim_core.llm.client import LLMClient
        client = LLMClient()
        result = await client.complete(
            system="You are a copywriter.",
            messages=[{"role": "user", "content": "Write a title."}],
        )

    assert result == "Generated product description."


@pytest.mark.asyncio
async def test_llm_client_passes_custom_model_to_api():
    """LLMClient.complete forwards a custom model name to the Anthropic API."""
    mock_content_block = MagicMock()
    mock_content_block.text = "ok"
    mock_message = MagicMock()
    mock_message.content = [mock_content_block]

    with patch("anthropic.AsyncAnthropic") as MockAnthropic:
        mock_instance = MagicMock()
        mock_instance.messages.create = AsyncMock(return_value=mock_message)
        MockAnthropic.return_value = mock_instance

        from pim_core.llm.client import LLMClient
        client = LLMClient()
        await client.complete(
            system="sys",
            messages=[{"role": "user", "content": "msg"}],
            model="claude-opus-4-6",
        )

    call_kwargs = mock_instance.messages.create.call_args.kwargs
    assert call_kwargs["model"] == "claude-opus-4-6"


@pytest.mark.asyncio
async def test_llm_client_uses_default_model_from_settings():
    """LLMClient.complete uses settings.claude_model when no model is passed."""
    mock_content_block = MagicMock()
    mock_content_block.text = "ok"
    mock_message = MagicMock()
    mock_message.content = [mock_content_block]

    with patch("anthropic.AsyncAnthropic") as MockAnthropic:
        mock_instance = MagicMock()
        mock_instance.messages.create = AsyncMock(return_value=mock_message)
        MockAnthropic.return_value = mock_instance

        from pim_core.llm.client import LLMClient
        from pim_core.config import settings
        client = LLMClient()
        await client.complete(system="sys", messages=[{"role": "user", "content": "msg"}])

    call_kwargs = mock_instance.messages.create.call_args.kwargs
    assert call_kwargs["model"] == settings.claude_model
