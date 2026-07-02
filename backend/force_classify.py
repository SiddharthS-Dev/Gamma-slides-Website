import asyncio
from app.database import init_db, async_session_factory
from app.models.presentation import Presentation
from app.services.classification_service import classify_presentation
from sqlalchemy import select

async def run():
    print("Initializing database...")
    await init_db()
    async with async_session_factory() as db:
        # Load all presentations
        result = await db.execute(select(Presentation))
        presentations = result.scalars().all()
        
        print(f"Found {len(presentations)} presentations in database.")
        
        classified_count = 0
        for idx, pres in enumerate(presentations):
            # Clean title for console print to avoid encoding errors
            safe_title = pres.title.encode('ascii', errors='ignore').decode('ascii')
            print(f"[{idx+1}/{len(presentations)}] Processing: {safe_title} (Status: {pres.ai_classification_status})")
            
            # Force classification even if they were classified or pending
            res = await classify_presentation(db, pres.id, force=True)
            if res.get("status") == "classified":
                classified_count += 1
                
        await db.commit()
        print(f"Successfully classified {classified_count} presentations!")

if __name__ == "__main__":
    asyncio.run(run())
