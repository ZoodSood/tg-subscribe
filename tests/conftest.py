import asyncio
import pytest
import aiosqlite
import aiofiles
import os
from environs import Env

def pytest_configure(config):
    """
    Allows plugins and conftest files to perform initial configuration.
    This hook is called for every plugin and initial conftest file
    after command line options have been parsed.
    """
    env = Env()
    env.read_env(".env.test")


@pytest.fixture(scope="function")
async def db_session():
    db = await aiosqlite.connect(":memory:")
    async with aiofiles.open("src/db/database_schema.sql", "r") as f:
        await db.executescript(await f.read())
    await db.commit()
    yield db
    await db.close()
