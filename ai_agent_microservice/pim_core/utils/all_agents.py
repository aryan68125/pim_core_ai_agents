from __future__ import annotations

from enum import Enum


class AllAgents(str, Enum):
    """Registry of all agents in the system.

    RULE: Before writing a new agent, add it here first.
    Every place in the codebase that references an agent name
    must import from this enum — no bare string literals allowed.

    When a new agent is added:
    1. Add its entry to this enum
    2. Create agents/<agent_name>/
    3. Use AllAgents.<AGENT_NAME> everywhere in that agent's code
    """
    PRODUCT_DESCRIPTION_GENERATOR = "product_description_generator"

    # Future agents — uncomment and implement when ready:
    # CATALOG = "catalog"
    # PROCUREMENT = "procurement"
