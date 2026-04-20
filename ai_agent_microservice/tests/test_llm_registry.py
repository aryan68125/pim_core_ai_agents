from unittest.mock import patch

from pim_core.utils.all_agents import AllAgents

AGENT_KEY = AllAgents.PRODUCT_DESCRIPTION_GENERATOR.value

# All tests use patch("pim_core.db.agent_model_db.load_all", return_value={})
# so each registry starts empty and independent of the real SQLite database.
# This keeps tests deterministic even when the DB has leftover data from prior runs.

_EMPTY_DB = {"load_all": lambda: {}, "upsert": lambda *a: None, "delete": lambda *a: None}


def _fresh_registry():
    """Return a registry isolated from the real SQLite database."""
    with patch("pim_core.db.agent_model_db.load_all", return_value={}), \
         patch("pim_core.db.agent_model_db.upsert"), \
         patch("pim_core.db.agent_model_db.delete"):
        from pim_core.llm.registry import AgentModelRegistry
        return AgentModelRegistry()


def test_registry_get_returns_default_when_agent_not_set():
    """Registry falls back to settings.claude_model for unknown agents."""
    from pim_core.config import settings
    reg = _fresh_registry()
    assert reg.get(AGENT_KEY) == settings.claude_model


def test_registry_set_and_get():
    """set() stores a model; get() returns it."""
    reg = _fresh_registry()
    with patch("pim_core.db.agent_model_db.upsert"):
        reg.set(AGENT_KEY, "gpt-4o")
    assert reg.get(AGENT_KEY) == "gpt-4o"


def test_registry_multiple_agents_independent():
    """Different agents have independent model assignments."""
    reg = _fresh_registry()
    with patch("pim_core.db.agent_model_db.upsert"):
        reg.set(AGENT_KEY, "claude-sonnet-4-6")
        reg.set("catalog", "gpt-4o")
    assert reg.get(AGENT_KEY) == "claude-sonnet-4-6"
    assert reg.get("catalog") == "gpt-4o"


def test_registry_all_returns_snapshot():
    """all() returns a dict copy — mutating it does not affect the registry."""
    reg = _fresh_registry()
    with patch("pim_core.db.agent_model_db.upsert"):
        reg.set(AGENT_KEY, "gemini-1.5-pro")
    snapshot = reg.all()
    assert snapshot == {AGENT_KEY: "gemini-1.5-pro"}
    snapshot[AGENT_KEY] = "changed"
    assert reg.get(AGENT_KEY) == "gemini-1.5-pro"


def test_registry_remove_reverts_to_default():
    """remove() clears an agent's model; subsequent get() returns default."""
    from pim_core.config import settings
    reg = _fresh_registry()
    with patch("pim_core.db.agent_model_db.upsert"):
        reg.set(AGENT_KEY, "gpt-4o")
    with patch("pim_core.db.agent_model_db.delete"):
        reg.remove(AGENT_KEY)
    assert reg.get(AGENT_KEY) == settings.claude_model
