import asyncio
import pytest
import aiosqlite
import aiofiles

from src.bot.database.repositories import UserRepository, TransactionRepository, PromoCodeRepository

@pytest.fixture(scope="function")
async def db_session():
    db = await aiosqlite.connect(":memory:")
    async with aiofiles.open("src/db/database_schema.sql", "r") as f:
        await db.executescript(await f.read())
    await db.commit()
    yield db
    await db.close()
