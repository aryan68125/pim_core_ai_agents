from __future__ import annotations

import json
from typing import Any, TypedDict

import structlog
from langgraph.graph import END, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from agents.auto_classifier.config import settings
from agents.auto_classifier.prompts.classification import (
    get_path_a_messages,
    get_path_b_messages,
    get_path_c_messages,
)
from agents.auto_classifier.tools.category_search import search_categories
from agents.auto_classifier.tools.embed_product import embed_text
from agents.auto_classifier.tools.web_search import search_wikipedia
from pim_core.llm.client import llm_client
from pim_core.llm.registry import agent_model_registry

logger = structlog.get_logger()

AGENT_NAME = "auto_classifier"


class ClassificationState(TypedDict):
    product_text: str
    session: Any                       # AsyncSession passed through
    embedding: list[float] | None
    candidates: list[dict]
    top_score: float
    web_context: str | None
    path: str | None                   # "A", "B", or "C"
    category_path: str | None
    category_id: int | None
    confidence: float
    method: str
    error: str | None


async def embed_node(state: ClassificationState) -> dict:
    try:
        embedding = await embed_text(state["product_text"])
        return {"embedding": embedding, "error": None}
    except Exception as exc:
        logger.error("embed_failed", error=str(exc))
        return {"embedding": None, "error": str(exc)}


async def search_node(state: ClassificationState) -> dict:
    if state.get("error") or state.get("embedding") is None:
        return {}
    candidates = await search_categories(state["embedding"], state["session"])
    top_score = candidates[0]["score"] if candidates else 0.0
    return {"candidates": candidates, "top_score": top_score}


def route_node(state: ClassificationState) -> dict:
    score = state.get("top_score", 0.0)
    if score >= settings.high_confidence_threshold:
        path = "A"
    elif score >= settings.low_confidence_threshold:
        path = "B"
    else:
        path = "C"
    logger.info("routing", top_score=score, path=path)
    return {"path": path}


async def web_search_node(state: ClassificationState) -> dict:
    try:
        context = await search_wikipedia(state["product_text"][:200])
        return {"web_context": context}
    except Exception as exc:
        logger.warning("web_search_failed", error=str(exc))
        return {"web_context": ""}


async def llm_node(state: ClassificationState) -> dict:
    path = state["path"]
    product_text = state["product_text"]
    candidates = state.get("candidates", [])
    web_context = state.get("web_context", "")

    if path == "A":
        system, user = get_path_a_messages(product_text, candidates)
    elif path == "B":
        system, user = get_path_b_messages(product_text, web_context, candidates)
    else:
        system, user = get_path_c_messages(product_text, web_context)

    try:
        raw = await llm_client.complete(
            system=system,
            messages=[{"role": "user", "content": user}],
            model=agent_model_registry.get(AGENT_NAME),
            max_tokens=256,
        )
        raw_clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        parsed = json.loads(raw_clean)
        category_path = parsed.get("category_path", "")
        confidence = float(parsed.get("confidence", 0.0))

        category_id = None
        if path in ("A", "B") and candidates:
            for c in candidates:
                if c["category_path"] == category_path:
                    category_id = c["category_id"]
                    break

        return {
            "category_path": category_path,
            "category_id": category_id,
            "confidence": confidence,
            "method": path,
            "error": None,
        }
    except Exception as exc:
        logger.error("llm_failed", error=str(exc))
        return {"category_path": None, "confidence": 0.0, "method": path, "error": str(exc)}


async def save_category_node(state: ClassificationState) -> dict:
    """Path C only: save new LLM-generated category to DB for future use."""
    import random
    from agents.auto_classifier.db.models import WebCategory
    from agents.auto_classifier.tools.embed_product import embed_text

    session: AsyncSession = state["session"]
    category_path = state.get("category_path", "")
    if not category_path:
        return {}

    parts = [p.strip() for p in category_path.split(">")]
    level1 = parts[0] if len(parts) > 0 else ""
    level2 = parts[1] if len(parts) > 1 else None
    level3 = parts[2] if len(parts) > 2 else None

    try:
        embedding = await embed_text(category_path)
        new_id = -random.randint(1, 2**30)

        new_cat = WebCategory(
            category_id=new_id,
            level1=level1,
            level2=level2,
            level3=level3,
            category_path=category_path,
            embedding=embedding,
        )
        session.add(new_cat)
        await session.commit()
        await session.refresh(new_cat)
        logger.info("new_category_saved", category_path=category_path, category_id=new_cat.category_id)
        return {"category_id": new_id}
    except Exception as exc:
        logger.warning("save_category_failed", error=str(exc))
        return {}


def _route_after_route(state: ClassificationState) -> str:
    return state["path"]


def _route_after_llm(state: ClassificationState) -> str:
    return "save" if state.get("path") == "C" else END


def build_classification_graph():
    graph: StateGraph = StateGraph(ClassificationState)
    graph.add_node("embed", embed_node)
    graph.add_node("search", search_node)
    graph.add_node("route", route_node)
    graph.add_node("web_search", web_search_node)
    graph.add_node("llm", llm_node)
    graph.add_node("save_category", save_category_node)

    graph.set_entry_point("embed")
    graph.add_edge("embed", "search")
    graph.add_edge("search", "route")
    graph.add_conditional_edges(
        "route",
        _route_after_route,
        {"A": "llm", "B": "web_search", "C": "web_search"},
    )
    graph.add_edge("web_search", "llm")
    graph.add_conditional_edges(
        "llm",
        _route_after_llm,
        {"save": "save_category", END: END},
    )
    graph.add_edge("save_category", END)
    return graph.compile()


classification_graph = build_classification_graph()
