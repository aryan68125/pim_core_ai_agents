from __future__ import annotations

_SYSTEM_BASE = """\
You are a product category classifier for a PIM system.
Return ONLY valid JSON — no markdown, no explanation outside the JSON.
"""

_PATH_A_SYSTEM = _SYSTEM_BASE + """
You will receive a product description and a list of candidate categories from our database.
Pick the single best category from the list provided.

Return:
{
  "category_path": "<exact path from the list>",
  "confidence": <0.0 to 1.0>,
  "reasoning": "<one sentence>"
}
"""

_PATH_B_SYSTEM = _SYSTEM_BASE + """
You will receive a product description, web context about the product, and candidate categories from our database.
Use the web context to better understand the product, then pick the single best category from the list provided.

Return:
{
  "category_path": "<exact path from the list>",
  "confidence": <0.0 to 1.0>,
  "reasoning": "<one sentence>"
}
"""

_PATH_C_SYSTEM = _SYSTEM_BASE + """
You will receive a product description and web context about the product.
No pre-defined categories matched. Generate the most accurate category path in L1 > L2 > L3 format.

Return:
{
  "category_path": "<L1> > <L2> > <L3>",
  "confidence": <0.0 to 1.0>,
  "reasoning": "<one sentence>"
}
"""


def _format_candidates(candidates: list[dict]) -> str:
    return "\n".join(
        f"{i+1}. {c['category_path']} (score: {c['score']:.2f})"
        for i, c in enumerate(candidates)
    )


def get_path_a_messages(product_text: str, candidates: list[dict]) -> tuple[str, str]:
    user = (
        f"Product:\n{product_text}\n\n"
        f"Candidate categories:\n{_format_candidates(candidates)}"
    )
    return _PATH_A_SYSTEM, user


def get_path_b_messages(
    product_text: str, web_context: str, candidates: list[dict]
) -> tuple[str, str]:
    user = (
        f"Product:\n{product_text}\n\n"
        f"Web context:\n{web_context}\n\n"
        f"Candidate categories:\n{_format_candidates(candidates)}"
    )
    return _PATH_B_SYSTEM, user


def get_path_c_messages(product_text: str, web_context: str) -> tuple[str, str]:
    user = (
        f"Product:\n{product_text}\n\n"
        f"Web context:\n{web_context}"
    )
    return _PATH_C_SYSTEM, user
