import asyncio
from app.database import init_db, async_session_factory
from app.services.classification_service import classify_all_pending

async def run():
    print("Initializing database...")
    await init_db()
    print("Scanning and classifying all pending presentations...")
    async with async_session_factory() as db:
        stats = await classify_all_pending(db)
        print("Success! Classification Stats:", stats)

if __name__ == "__main__":
    asyncio.run(run())
