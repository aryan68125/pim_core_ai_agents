from __future__ import annotations

import structlog
import httpx

logger = structlog.get_logger()

_SEARCH_URL = "https://en.wikipedia.org/w/api.php"
_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"


async def search_wikipedia(query: str, max_chars: int = 500) -> str:
    """Search Wikipedia and return a summary of the best matching article."""
    headers = {"User-Agent": "pim-auto-classifier/1.0 (smit.patel@credencys.com)"}
    async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
        search_resp = await client.get(
            _SEARCH_URL,
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "srlimit": 1,
            },
        )
        search_resp.raise_for_status()
        results = search_resp.json().get("query", {}).get("search", [])
        if not results:
            logger.info("wikipedia_no_results", query=query)
            return ""

        title = results[0]["title"]

        summary_resp = await client.get(
            _SUMMARY_URL.format(title=title.replace(" ", "_"))
        )
        if summary_resp.status_code != 200:
            return ""

        extract = summary_resp.json().get("extract", "")
        logger.info("wikipedia_found", title=title, chars=len(extract))
        return extract[:max_chars]
