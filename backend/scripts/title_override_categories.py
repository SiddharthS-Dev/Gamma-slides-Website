"""Override category assignments using title keywords — higher priority than AI content analysis.

The rule-based AI scores extracted body text, so tech-heavy company decks get labelled
Technology even when the title clearly says 'Talent Engine' or 'Cap Table'.
This script reads the title and applies deterministic rules to correct those assignments.

Run from the backend directory:
    python scripts/title_override_categories.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, text
from app.database import async_session_factory
from app.models.presentation import Presentation
from app.models.category import Category

# Ordered rules — FIRST match wins. Each entry: (target_category_name, [title_keywords])
# Keywords are matched case-insensitively anywhere in the title or filename.
TITLE_OVERRIDE_RULES: list[tuple[str, list[str]]] = [
    # ── People & HR ──────────────────────────────────────────────────────────
    ("People & HR", [
        "talent engine", "talent evaluation", "culture iceberg", "discipline engine",
        "difficult employees", "from performer to leader", "founder mindset",
        "founder narrative", "people risk", "shatamarshana", "oxford union speech",
        "tips and tricks", "gamma tips", "hr ", "human resource", "onboarding",
        "leave management", "payroll", "recruitment", "employee",
    ]),

    # ── Sales & Marketing ────────────────────────────────────────────────────
    ("Sales & Marketing", [
        "buyer targeting", "csp growth strategy", "strategic alliance",
        "go-to-market", "pitch deck", "sales strategy", "marketing campaign",
        "brand strategy",
    ]),

    # ── Security & Compliance ────────────────────────────────────────────────
    ("Security & Compliance", [
        "esg first", "esg ai", "sustainability partnership", "ic esg",
        "cognitive dx iiot", "esg wallet", "carbon", "emissions",
        "environmental", "compliance audit", "risk management", "gdpr",
        "data governance", "privacy policy",
    ]),

    # ── Business & Operations ────────────────────────────────────────────────
    ("Business & Operations", [
        "cap table", "bridge participation", "exit bridge", "exit readiness",
        "exit execution", "exit runway", "exit phase", "exit opportunity",
        "exit proecess", "exit process",
        "valuation", "investment thesis", "investor", "investment",
        "board review", "board view", "board session", "board edition",
        "confidential board", "stakeholder",
        "iptif", "structured for investor", "probability weighted",
        "optional pro rata", "bridge subscription", "br-2026",
        "iiot europe", "impact 30", "crossroads to the boardroom",
        "supply chain war", "execution credibility",
        "capital structure", "funding", "grant opportunity",
        "astrax critical path", "astrax eb1 supply chain",
        "settlement", "structured resolution",
        "from concerns to decision",
    ]),
]


async def override_by_title() -> None:
    async with async_session_factory() as db:
        result = await db.execute(select(Category))
        cats_by_name: dict[str, Category] = {c.name: c for c in result.scalars().all()}

        result = await db.execute(
            select(Presentation)
            .where(Presentation.is_active == True)
            .order_by(Presentation.title)
        )
        all_pres = result.scalars().all()

        overridden = 0
        for pres in all_pres:
            title_lower = (pres.title or pres.file_name or "").lower()
            for cat_name, keywords in TITLE_OVERRIDE_RULES:
                if any(kw in title_lower for kw in keywords):
                    target = cats_by_name[cat_name]
                    if pres.category_id != target.id:
                        old_name = next(
                            (n for n, c in cats_by_name.items() if c.id == pres.category_id),
                            "None"
                        )
                        print(f"  {pres.title[:58]:<58}  {old_name} -> {cat_name}")
                        pres.category_id = target.id
                        overridden += 1
                    break

        await db.commit()
        print(f"\nOverrode {overridden} presentations\n")

        result2 = await db.execute(text('''
            SELECT c.name, COUNT(p.id)
            FROM categories c
            LEFT JOIN presentations p ON p.category_id = c.id
            GROUP BY c.name, c.sort_order
            ORDER BY c.sort_order
        '''))
        print("Final distribution:")
        for name, cnt in result2.fetchall():
            bar = '#' * cnt
            print(f"  {name:<30} {cnt:>3}  {bar}")


if __name__ == "__main__":
    asyncio.run(override_by_title())
