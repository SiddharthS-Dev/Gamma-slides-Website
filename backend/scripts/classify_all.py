"""Classify all presentations into the 5 consolidated categories.

Run from the backend directory:
    python scripts/classify_all.py

Uses a fresh DB session per presentation to survive connection drops.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, text
from app.database import async_session_factory
from app.models.presentation import Presentation
from app.services.classification_service import classify_presentation


async def get_all_ids() -> list[tuple]:
    async with async_session_factory() as db:
        result = await db.execute(
            select(Presentation.id, Presentation.title)
            .where(Presentation.is_active == True)
            .order_by(Presentation.title)
        )
        return result.fetchall()


async def classify_one(pres_id, title: str, idx: int, total: int) -> str:
    try:
        async with async_session_factory() as db:
            r = await classify_presentation(db, pres_id, force=True)
            await db.commit()
            status = r.get("status")
            if status == "classified":
                cat = r.get("category", "?")
                conf = r.get("confidence_category", 0)
                return f"[{idx:3}/{total}] OK  {title[:55]:<55} -> {cat} ({conf:.0%})"
            elif "File not found" in r.get("message", ""):
                return f"[{idx:3}/{total}] !   {title[:55]:<55} (no file)"
            else:
                return f"[{idx:3}/{total}] ERR {title[:55]:<55} {r.get('message','')}"
    except Exception as e:
        return f"[{idx:3}/{total}] EXC {title[:55]:<55} {str(e)[:60]}"


async def classify_all() -> None:
    rows = await get_all_ids()
    total = len(rows)
    print(f"Found {total} presentations to classify\n")

    classified = failed = no_file = 0
    for i, (pres_id, title) in enumerate(rows, 1):
        msg = await classify_one(pres_id, title or "", i, total)
        print(msg)
        if " OK " in msg:
            classified += 1
        elif " !  " in msg:
            no_file += 1
        else:
            failed += 1

    print(f"\nDone: {classified} classified, {failed} failed, {no_file} no-file  (total {total})")


if __name__ == "__main__":
    asyncio.run(classify_all())
