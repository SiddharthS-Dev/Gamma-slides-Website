"""Consolidate categories into 5 top-level groups.

Run from the backend directory:
    python scripts/consolidate_categories.py

What it does:
  1. Creates 5 new consolidated categories
  2. Reassigns all presentations (category_id, ai_category_id) to the new categories
  3. Deletes all old categories

The 5 new categories:
  Technology            - Engineering, IT Infrastructure, Product, AI, Cloud...
  Security & Compliance - Cybersecurity, Risk, Legal, Governance, ESG...
  Business & Operations - Operations, Finance, Administration, Supply Chain...
  People & HR           - HR, Training, Soft Skills, Customer Success...
  Sales & Marketing     - Sales, Marketing, CRM, Events, Brand...
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import uuid as uuid_lib
from sqlalchemy import select, update
from app.database import async_session_factory
from app.models.category import Category
from app.models.presentation import Presentation


NEW_CATEGORIES = [
    {
        "name": "Technology",
        "slug": "technology",
        "color": "#3b82f6",
        "icon": "cpu",
        "sort_order": 0,
        "description": "Engineering, infrastructure, AI, cloud, DevOps, product and technical domains",
        "absorbs": [
            "engineering", "architecture", "backend", "frontend", "devops",
            "ai", "data-engineering",
            "it-infrastructure", "network", "cloud", "systems",
            "product", "fleetexplorer", "pdlc", "product-documentation",
            "technical-training", "it-governance",
        ],
    },
    {
        "name": "Security & Compliance",
        "slug": "security-compliance",
        "color": "#ef4444",
        "icon": "shield",
        "sort_order": 1,
        "description": "Cybersecurity, compliance, risk, legal, audit, governance and ESG",
        "absorbs": [
            "security", "cybersecurity", "access-control", "data-security",
            "compliance", "regulatory", "risk-management", "legal",
            "audit", "data-governance",
            "governance", "corporate-governance", "governance-esg",
            "esg", "environmental", "social", "esg-wallet",
        ],
    },
    {
        "name": "Business & Operations",
        "slug": "business-operations",
        "color": "#f59e0b",
        "icon": "briefcase",
        "sort_order": 2,
        "description": "Operations, finance, administration, supply chain and asset management",
        "absorbs": [
            "operations", "fleet-operations", "supply-chain", "process-improvement",
            "finance", "budgeting", "financial-reporting",
            "administration", "office-management", "vendor-management", "asset-management",
        ],
    },
    {
        "name": "People & HR",
        "slug": "people-hr",
        "color": "#ec4899",
        "icon": "users",
        "sort_order": 3,
        "description": "Human resources, training, onboarding, soft skills and customer success",
        "absorbs": [
            "human-resources", "discipline-engine", "leave-management",
            "employee-onboarding", "policies",
            "training", "soft-skills", "onboarding-training",
            "customer-success", "support", "account-management", "customer-feedback",
        ],
    },
    {
        "name": "Sales & Marketing",
        "slug": "sales-marketing",
        "color": "#a855f7",
        "icon": "target",
        "sort_order": 4,
        "description": "Sales strategy, enablement, CRM, marketing, branding and events",
        "absorbs": [
            "sales", "sales-strategy", "sales-enablement", "crm",
            "marketing", "digital-marketing", "brand", "events",
        ],
    },
]


async def consolidate() -> None:
    async with async_session_factory() as db:
        # Load all existing categories keyed by slug
        result = await db.execute(select(Category))
        existing: dict[str, Category] = {c.slug: c for c in result.scalars().all()}
        print(f"Found {len(existing)} existing categories in database\n")

        # Build slug → new category ID mapping
        slug_to_new_id: dict[str, uuid_lib.UUID] = {}
        new_cat_objects: list[Category] = []

        for cat_def in NEW_CATEGORIES:
            new_slug = cat_def["slug"]

            if new_slug in existing:
                # Already exists — reuse it
                new_cat = existing[new_slug]
                print(f"[reuse]  {new_cat.name}  (id={new_cat.id})")
            else:
                new_cat = Category(
                    id=uuid_lib.uuid4(),
                    name=cat_def["name"],
                    slug=new_slug,
                    color=cat_def["color"],
                    icon=cat_def["icon"],
                    sort_order=cat_def["sort_order"],
                    description=cat_def["description"],
                    parent_id=None,
                )
                db.add(new_cat)
                await db.flush()
                print(f"[create] {new_cat.name}  (id={new_cat.id})")

            new_cat_objects.append(new_cat)
            for old_slug in cat_def["absorbs"]:
                slug_to_new_id[old_slug] = new_cat.id

        print()

        # Build reverse map: new_id → new category name (for logging)
        new_id_to_name: dict[uuid_lib.UUID, str] = {
            c.id: d["name"] for c, d in zip(new_cat_objects, NEW_CATEGORIES)
        }

        # Reassign presentations
        total_reassigned = 0
        for old_slug, new_id in slug_to_new_id.items():
            if old_slug not in existing:
                continue
            old_id = existing[old_slug].id

            r1 = await db.execute(
                update(Presentation)
                .where(Presentation.category_id == old_id)
                .values(category_id=new_id)
            )
            r2 = await db.execute(
                update(Presentation)
                .where(Presentation.ai_category_id == old_id)
                .values(ai_category_id=new_id)
            )
            moved = (r1.rowcount or 0) + (r2.rowcount or 0)
            if moved:
                print(f"  reassigned {moved} presentations: '{old_slug}' -> '{new_id_to_name[new_id]}'")
                total_reassigned += moved

        print(f"\nTotal presentations reassigned: {total_reassigned}\n")

        # Delete old categories (sub-categories first to satisfy FK constraint)
        new_ids = {c.id for c in new_cat_objects}
        to_delete = [c for c in existing.values() if c.id not in new_ids]

        sub_cats = [c for c in to_delete if c.parent_id is not None]
        parent_cats = [c for c in to_delete if c.parent_id is None]

        deleted = 0
        for c in sub_cats:
            await db.delete(c)
            deleted += 1
        for c in parent_cats:
            await db.delete(c)
            deleted += 1

        await db.commit()
        print(f"Deleted {deleted} old categories ({len(sub_cats)} sub + {len(parent_cats)} parents)")
        print(f"\nDone -- {len(NEW_CATEGORIES)} consolidated categories remain.")


if __name__ == "__main__":
    asyncio.run(consolidate())
