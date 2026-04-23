"""
One-time script: load Web Category Hierarchy Excel -> embed each category -> insert into DB.

Usage:
  cd pim_core_ai_agents/ai_agent_microservice
  python -m agents.auto_classifier.tools.seed_categories \
    --excel "/path/to/Web Category Hierarchy 08.19.25 (1).xlsx"
"""
from __future__ import annotations

import argparse
import asyncio

import openpyxl
import structlog

logger = structlog.get_logger()


def parse_hierarchy(excel_path: str) -> list[dict]:
    """Parse Web Category Hierarchy Excel into flat list of category dicts."""
    wb = openpyxl.load_workbook(excel_path)
    ws = wb["Web Category Hierarchy"]

    categories = []
    current_l1 = ""
    current_l2 = ""

    for row in ws.iter_rows(min_row=3, values_only=True):
        l1_val = str(row[0]).strip() if row[0] else ""
        l2_val = str(row[1]).strip() if row[1] else ""
        l3_val = str(row[2]).strip() if row[2] else ""
        cat_id = row[4]

        if not isinstance(cat_id, int):
            continue

        if l1_val:
            current_l1 = l1_val
            current_l2 = ""
            categories.append({
                "category_id": cat_id,
                "level1": current_l1,
                "level2": None,
                "level3": None,
                "category_path": current_l1,
            })
        elif l2_val:
            current_l2 = l2_val
            categories.append({
                "category_id": cat_id,
                "level1": current_l1,
                "level2": current_l2,
                "level3": None,
                "category_path": f"{current_l1} > {l2_val}",
            })
        elif l3_val:
            categories.append({
                "category_id": cat_id,
                "level1": current_l1,
                "level2": current_l2,
                "level3": l3_val,
                "category_path": f"{current_l1} > {current_l2} > {l3_val}",
            })

    logger.info("parsed_categories", count=len(categories))
    return categories


async def seed(excel_path: str) -> None:
    from agents.auto_classifier.config import settings
    from agents.auto_classifier.db.base import get_session, init_db
    from agents.auto_classifier.db.models import WebCategory
    from agents.auto_classifier.tools.embedding import get_embedding_provider
    from sqlalchemy import select

    await init_db(settings.database_url)
    provider = get_embedding_provider()
    categories = parse_hierarchy(excel_path)

    async for session in get_session():
        result = await session.execute(select(WebCategory).limit(1))
        if result.first():
            logger.info("categories_already_seeded_skipping")
            return

        logger.info("seeding_categories", total=len(categories))
        seen_ids: set[int] = set()
        inserted = 0
        for i, cat in enumerate(categories):
            if cat["category_id"] in seen_ids:
                continue
            seen_ids.add(cat["category_id"])
            embedding = await provider.embed(cat["category_path"])
            session.add(WebCategory(
                category_id=cat["category_id"],
                level1=cat["level1"],
                level2=cat["level2"],
                level3=cat["level3"],
                category_path=cat["category_path"],
                embedding=embedding,
            ))
            inserted += 1
            if inserted % 50 == 0:
                await session.commit()
                logger.info("seeding_progress", done=inserted, total=len(categories))

        await session.commit()
        logger.info("seeding_complete", inserted=inserted, total=len(categories))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--excel", required=True, help="Path to Web Category Hierarchy xlsx")
    args = parser.parse_args()
    asyncio.run(seed(args.excel))
