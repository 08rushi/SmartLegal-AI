import asyncio
from database import init_db_pool, get_db_ctx
from services.yojana_ingest import seed_default_schemes_if_empty

async def main():
    await init_db_pool()
    async with get_db_ctx() as db:
        count = await seed_default_schemes_if_empty(db)
        print(f"AUTOMATED_SEED_SUCCESS: {count} schemes active")

if __name__ == "__main__":
    asyncio.run(main())
