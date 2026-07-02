"""Seed 5 consolidated top-level categories on first startup.

Called during startup if the categories table is empty.
To consolidate an existing database, run: python scripts/consolidate_categories.py
"""

import logging
import re

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models.category import Category

logger = logging.getLogger(__name__)


def _slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    slug = text.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug


# ═══════════════════════════════════════════════════════════════
# Full category hierarchy with colors and icons
# ═══════════════════════════════════════════════════════════════

CATEGORY_HIERARCHY: list[dict] = [
    {
        "name": "Technology",
        "color": "#3b82f6",
        "icon": "cpu",
        "description": "Engineering, infrastructure, AI, cloud, DevOps, product and technical domains",
        "sub_categories": [],
    },
    {
        "name": "Security & Compliance",
        "color": "#ef4444",
        "icon": "shield",
        "description": "Cybersecurity, compliance, risk, legal, audit, governance and ESG",
        "sub_categories": [],
    },
    {
        "name": "Business & Operations",
        "color": "#f59e0b",
        "icon": "briefcase",
        "description": "Operations, finance, administration, supply chain and asset management",
        "sub_categories": [],
    },
    {
        "name": "People & HR",
        "color": "#ec4899",
        "icon": "users",
        "description": "Human resources, training, onboarding, soft skills and customer success",
        "sub_categories": [],
    },
    {
        "name": "Sales & Marketing",
        "color": "#a855f7",
        "icon": "target",
        "description": "Sales strategy, enablement, CRM, marketing, branding and events",
        "sub_categories": [],
    },
]


async def seed_categories_if_empty() -> None:
    """Populate the category hierarchy if the categories table is empty."""
    async with async_session_factory() as db:
        # Check if categories already exist
        count_result = await db.execute(
            select(func.count()).select_from(Category)
        )
        count = count_result.scalar() or 0
        if count > 0:
            logger.info(f"Categories already seeded ({count} categories found)")
            return

        logger.info("Seeding 5 consolidated categories...")
        created = 0

        for sort_order, cat_data in enumerate(CATEGORY_HIERARCHY):
            parent = Category(
                name=cat_data["name"],
                slug=_slugify(cat_data["name"]),
                description=cat_data.get("description"),
                color=cat_data.get("color", "#6366f1"),
                icon=cat_data.get("icon", "folder"),
                sort_order=sort_order,
            )
            db.add(parent)
            created += 1

        await db.commit()
        logger.info(f"✅ Seeded {created} top-level categories")
