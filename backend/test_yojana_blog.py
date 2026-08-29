import asyncio
from database import init_db_pool, get_db_ctx
from services.yojana_blog_service import seed_default_blogs_if_empty

async def main():
    await init_db_pool()
    async with get_db_ctx() as db:
        cnt = await seed_default_blogs_if_empty(db)
        print(f"BLOG_SEED_SUCCESS: {cnt} blogs active in yojana_blogs table")

if __name__ == "__main__":
    asyncio.run(main())
