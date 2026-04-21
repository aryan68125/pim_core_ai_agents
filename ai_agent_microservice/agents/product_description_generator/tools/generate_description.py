from __future__ import annotations

from fastmcp import FastMCP

from agents.product_description_generator.workflows.description_workflow import description_graph
from pim_core.llm.registry import agent_model_registry
from pim_core.schemas.product import BrandVoice, DescriptionResult, Product
from pim_core.utils.all_agents import AllAgents

mcp = FastMCP("Content Agent")


@mcp.tool()
async def generate_description(
    product: Product,
    channel: str,
    brand_voice: BrandVoice | None = None,
) -> DescriptionResult:
    """Generate an SEO-optimised title and description for a product.

    Args:
        product: The product record to describe.
        channel: Target distribution channel (e.g. 'ecommerce', 'wholesale', 'marketplace').
        brand_voice: Optional brand voice configuration. Uses defaults when omitted.

    Returns:
        DescriptionResult with generated title, description, and SEO keywords.

    Raises:
        ValueError: When the LLM returns a response that cannot be parsed as JSON.
    """
    if brand_voice is None:
        brand_voice = BrandVoice()

    state = {
        "product": product,
        "channel": channel,
        "brand_voice": brand_voice,
        "title": "",
        "description": "",
        "seo_keywords": [],
        "error": None,
    }

    result_state = await description_graph.ainvoke(state)

    if result_state.get("error"):
        raise ValueError(result_state["error"])

    return DescriptionResult(
        product_id=product.id,
        channel=channel,
        title=result_state["title"],
        description=result_state["description"],
        seo_keywords=result_state["seo_keywords"],
        word_count=len(result_state["description"].split()),
        model_used=agent_model_registry.get(AllAgents.PRODUCT_DESCRIPTION_GENERATOR.value),
    )
