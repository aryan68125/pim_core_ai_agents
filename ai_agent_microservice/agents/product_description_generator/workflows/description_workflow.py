from __future__ import annotations

import json
import logging
import re
from typing import TypedDict

from langgraph.graph import END, StateGraph

from agents.product_description_generator.prompts.brand_voice import get_system_prompt, get_user_message
from pim_core.llm.client import llm_client
from pim_core.llm.registry import agent_model_registry
from pim_core.schemas.product import BrandVoice, Product
from pim_core.utils.all_agents import AllAgents

logger = logging.getLogger(__name__)

_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def _extract_json(raw: str) -> str:
    """Return the raw JSON string, stripping markdown code fences if present.

    Claude sometimes wraps its JSON output in ```json ... ``` even when
    instructed not to. This function handles both cases:
    - Plain JSON  → returned as-is
    - Fenced JSON → inner content extracted and returned
    """
    stripped = raw.strip()
    match = _FENCE_RE.search(stripped)
    if match:
        return match.group(1).strip()
    return stripped


class DescriptionState(TypedDict):
    product: Product
    channel: str
    brand_voice: BrandVoice
    title: str
    description: str
    seo_keywords: list[str]
    error: str | None


async def generate_node(state: DescriptionState) -> dict:
    """Call the assigned LLM with a product + brand voice prompt and parse the JSON."""
    model = agent_model_registry.get(AllAgents.PRODUCT_DESCRIPTION_GENERATOR.value)
    system_prompt = get_system_prompt(state["brand_voice"])
    user_message = get_user_message(state["product"], state["channel"])

    logger.info(
        "Calling LLM model '%s' for product %s on channel %s",
        model,
        state["product"].id,
        state["channel"],
    )

    try:
        raw_text = await llm_client.complete(
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            model=model,
            max_tokens=1200,
        )
        parsed = json.loads(_extract_json(raw_text))
        return {
            "title": parsed["title"],
            "description": parsed["description"],
            "seo_keywords": parsed.get("seo_keywords", []),
            "error": None,
        }
    except (json.JSONDecodeError, KeyError) as exc:
        logger.error("LLM parse failed for product %s: %s", state["product"].id, exc)
        return {"error": f"Failed to parse LLM response: {exc}"}


def build_description_graph():
    """Compile and return the description StateGraph."""
    graph: StateGraph = StateGraph(DescriptionState)
    graph.add_node("generate", generate_node)
    graph.set_entry_point("generate")
    graph.add_edge("generate", END)
    return graph.compile()


description_graph = build_description_graph()
