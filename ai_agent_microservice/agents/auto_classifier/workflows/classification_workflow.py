from __future__ import annotations

import json
import logging
from typing import TypedDict

import structlog
from langgraph.graph import END, StateGraph

from agents.auto_classifier.config import settings
from agents.auto_classifier.prompts.classification import get_system_prompt, get_user_message
from pim_core.llm.client import llm_client
from pim_core.schemas.product import Product

logger = structlog.get_logger()

AGENT_NAME = "auto_classifier"


class ClassificationState(TypedDict):
    product: Product
    taxonomy_type: str
    candidates: list[dict]   # pre-populated by embed search in classify_product tool
    tier: int                # 1 | 2 | 3
    model: str               # LLM model name for this tier
    code: str | None
    name: str | None
    confidence: float
    reasoning: str
    stage: str               # "embedding_accept" | "llm_tier1" | "llm_tier2" | "llm_tier3"
    error: str | None


def _should_use_embedding(state: ClassificationState) -> str:
    """Accept top embedding result if similarity exceeds threshold, else call LLM."""
    candidates = state.get("candidates", [])
    if candidates and candidates[0]["score"] >= settings.confidence_embedding_threshold:
        return "accept"
    return "llm"


async def embedding_accept_node(state: ClassificationState) -> dict:
    best = state["candidates"][0]
    logger.info(
        "embedding_accept",
        code=best["code"],
        score=best["score"],
        taxonomy_type=state["taxonomy_type"],
    )
    return {
        "code": best["code"],
        "name": best["name"],
        "confidence": best["score"],
        "reasoning": f"Embedding similarity {best['score']:.3f} above auto-accept threshold",
        "stage": "embedding_accept",
        "error": None,
    }


async def llm_classify_node(state: ClassificationState) -> dict:
    model = state["model"]
    system = get_system_prompt()
    user = get_user_message(state["product"], state["taxonomy_type"], state["candidates"])
    stage = f"llm_tier{state['tier']}"

    logger.info("llm_classify", model=model, tier=state["tier"], taxonomy_type=state["taxonomy_type"])

    try:
        raw = await llm_client.complete(
            system=system,
            messages=[{"role": "user", "content": user}],
            model=model,
            max_tokens=512,
        )
        parsed = json.loads(raw)
        return {
            "code": parsed.get("code"),
            "name": parsed.get("name"),
            "confidence": float(parsed.get("confidence", 0.0)),
            "reasoning": parsed.get("reasoning", ""),
            "stage": stage,
            "error": None,
        }
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        logger.error("llm_classify_failed", model=model, error=str(exc))
        return {
            "code": None,
            "name": None,
            "confidence": 0.0,
            "reasoning": "Failed to parse LLM response",
            "stage": stage,
            "error": str(exc),
        }


def build_classification_graph():
    graph: StateGraph = StateGraph(ClassificationState)

    graph.add_node("embedding_accept", embedding_accept_node)
    graph.add_node("llm_classify", llm_classify_node)

    graph.set_conditional_entry_point(
        _should_use_embedding,
        {"accept": "embedding_accept", "llm": "llm_classify"},
    )
    graph.add_edge("embedding_accept", END)
    graph.add_edge("llm_classify", END)

    return graph.compile()


classification_graph = build_classification_graph()
