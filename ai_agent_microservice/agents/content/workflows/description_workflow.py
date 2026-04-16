from __future__ import annotations

import json
import logging
from typing import TypedDict

from langgraph.graph import END, StateGraph

from agents.content.prompts.brand_voice import get_system_prompt, get_user_message
from pim_core.llm.client import llm_client
from pim_core.schemas.product import BrandVoice, Product

logger = logging.getLogger(__name__)


class DescriptionState(TypedDict):
    product: Product
    channel: str
    brand_voice: BrandVoice
    title: str
    description: str
    seo_keywords: list[str]
    error: str | None


async def generate_node(state: DescriptionState) -> dict:
    """Call Claude API with a product + brand voice prompt and parse the JSON response."""
    system_prompt = get_system_prompt(state["brand_voice"])
    user_message = get_user_message(state["product"], state["channel"])

    logger.info(
        "Calling LLM for product %s on channel %s",
        state["product"].id,
        state["channel"],
    )

    try:
        raw_text = await llm_client.complete(
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            max_tokens=800,
        )
        parsed = json.loads(raw_text)
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
