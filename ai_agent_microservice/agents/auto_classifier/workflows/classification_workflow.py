from __future__ import annotations

import json
from typing import Any, TypedDict

import structlog
from langgraph.graph import END, StateGraph

from agents.auto_classifier.config import settings
from agents.auto_classifier.prompts.classification import get_system_prompt, get_user_message
from pim_core.llm.client import llm_client

logger = structlog.get_logger()

AGENT_NAME = "auto_classifier"


class ClassificationState(TypedDict):
    product: dict[str, Any]
    taxonomy_type: str
    category_path: str | None
    code: str | None
    confidence: float
    reasoning: str
    error: str | None


async def classify_node(state: ClassificationState) -> dict:
    system = get_system_prompt()
    user = get_user_message(state["product"], state["taxonomy_type"])

    logger.info("classifying", taxonomy_type=state["taxonomy_type"], model=settings.classifier_model)

    try:
        raw = await llm_client.complete(
            system=system,
            messages=[{"role": "user", "content": user}],
            model=settings.classifier_model,
            max_tokens=512,
        )
        parsed = json.loads(raw)
        return {
            "category_path": parsed.get("category_path"),
            "code": parsed.get("code"),
            "confidence": float(parsed.get("confidence", 0.0)),
            "reasoning": parsed.get("reasoning", ""),
            "error": None,
        }
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        logger.error("classify_failed", error=str(exc))
        return {
            "category_path": None,
            "code": None,
            "confidence": 0.0,
            "reasoning": "Failed to parse LLM response",
            "error": str(exc),
        }


def build_classification_graph():
    graph: StateGraph = StateGraph(ClassificationState)
    graph.add_node("classify", classify_node)
    graph.set_entry_point("classify")
    graph.add_edge("classify", END)
    return graph.compile()


classification_graph = build_classification_graph()
