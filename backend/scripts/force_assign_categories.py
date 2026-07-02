"""Force-assign category_id for all presentations that are still uncategorized.

Strategy (in order):
  1. If ai_category_id is set -> copy it to category_id
  2. Otherwise apply title-keyword rules against the 5 consolidated categories
  3. Final fallback -> Technology

Run from the backend directory:
    python scripts/force_assign_categories.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, text
from app.database import async_session_factory
from app.models.presentation import Presentation
from app.models.category import Category

# Title/filename keyword rules for the 5 categories (checked in order, first match wins)
TITLE_RULES: list[tuple[str, list[str]]] = [
    ("Security & Compliance", [
        "esg", "compliance", "governance", "security", "risk", "regulatory",
        "gdpr", "audit", "legal", "privacy", "ethics",
    ]),
    ("Business & Operations", [
        "cap table", "bridge", "valuation", "investor", "investment", "exit",
        "financial", "finance", "budget", "revenue", "p&l", "funding", "grant",
        "supply chain", "operations", "operational", "logistics", "procurement",
        "board", "stakeholder", "proposal", "strategic alliance",
    ]),
    ("People & HR", [
        "talent", "people", "hr ", "human resource", "employee", "onboarding",
        "culture", "mindset", "founder", "leader", "discipline", "oxford",
        "lineage", "heritage", "maternal", "rishis",
    ]),
    ("Sales & Marketing", [
        "sales", "marketing", "buyer", "crm", "brand", "campaign", "pitch",
        "growth strategy", "csp growth",
    ]),
    ("Technology", [
        "ai", "iot", "platform", "architecture", "engineering", "cloud",
        "infrastructure", "software", "tech", "digital", "cognitive",
        "intelligence", "agentic", "iiot", "aiot", "device", "network",
        "edge", "secure", "blockchain", "data", "algorithm", "automation",
        "microsoft", "aws", "azure",
    ]),
]


async def assign_categories() -> None:
    async with async_session_factory() as db:
        # Load all 5 category objects
        result = await db.execute(select(Category))
        cats_by_name: dict[str, Category] = {c.name: c for c in result.scalars().all()}
        print("Categories loaded:", list(cats_by_name.keys()), "\n")

        # Get all presentations
        result = await db.execute(
            select(Presentation)
            .where(Presentation.is_active == True)
            .order_by(Presentation.title)
        )
        all_pres = result.scalars().all()

        assigned = already = rule_based = fallback = 0

        for pres in all_pres:
            if pres.category_id is not None:
                already += 1
                continue

            # Strategy 1: use ai_category_id
            if pres.ai_category_id is not None:
                pres.category_id = pres.ai_category_id
                assigned += 1
                continue

            # Strategy 2: title keyword rules
            title_lower = (pres.title or pres.file_name or "").lower()
            matched_cat = None
            for cat_name, keywords in TITLE_RULES:
                if any(kw in title_lower for kw in keywords):
                    matched_cat = cats_by_name.get(cat_name)
                    break

            if matched_cat:
                pres.category_id = matched_cat.id
                rule_based += 1
                print(f"  [rule] {pres.title[:60]:<60} -> {matched_cat.name}")
            else:
                # Final fallback
                pres.category_id = cats_by_name["Technology"].id
                fallback += 1
                print(f"  [fall] {pres.title[:60]:<60} -> Technology")

        await db.commit()

        # Print final distribution
        result2 = await db.execute(text('''
            SELECT c.name, COUNT(p.id)
            FROM categories c
            LEFT JOIN presentations p ON p.category_id = c.id
            GROUP BY c.name, c.sort_order
            ORDER BY c.sort_order
        '''))
        rows = result2.fetchall()

        print(f"\nAlready had category_id: {already}")
        print(f"Assigned via ai_category_id: {assigned}")
        print(f"Assigned via title rules: {rule_based}")
        print(f"Fallback to Technology: {fallback}")
        print(f"\nFinal distribution:")
        for name, cnt in rows:
            bar = '#' * cnt
            print(f"  {name:<30} {cnt:>3}  {bar}")


if __name__ == "__main__":
    asyncio.run(assign_categories())
