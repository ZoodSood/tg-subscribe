import pytest
from unittest.mock import patch, AsyncMock
import aiofiles
import aiosqlite

from src.bot.database import get_database_schema_sql, create_schema_if_not_exist

@pytest.mark.asyncio
async def test_get_database_schema_sql_exception():
    """Test get_database_schema_sql when an exception occurs."""
    with patch('aiofiles.open', side_effect=Exception("File not found")):
        with pytest.raises(Exception, match="File not found"):
            await get_database_schema_sql()

@pytest.mark.asyncio
async def test_create_schema_if_not_exist_get_schema_exception():
    """Test create_schema_if_not_exist when get_database_schema_sql fails."""
    with patch('src.bot.database.get_database_schema_sql', side_effect=Exception("Failed to get schema")):
        with pytest.raises(Exception, match="Failed to get schema"):
            await create_schema_if_not_exist()

@pytest.mark.asyncio
async def test_create_schema_if_not_exist_connect_exception():
    """Test create_schema_if_not_exist when aiosqlite.connect fails."""
    with patch('src.bot.database.get_database_schema_sql', return_value="CREATE TABLE Users..."), \
         patch('aiosqlite.connect', side_effect=Exception("DB error")):
        with pytest.raises(Exception, match="DB error"):
            await create_schema_if_not_exist()


@pytest.mark.asyncio
async def test_get_database_schema_sql_happy_path():
    """Test get_database_schema_sql happy path."""
    mock_file = AsyncMock()
    mock_file.read.return_value = "CREATE TABLE Users;"

    mock_open = AsyncMock()
    mock_open.__aenter__.return_value = mock_file

    with patch('aiofiles.open', return_value=mock_open) as mock_aiofiles_open:
        sql = await get_database_schema_sql()
        assert sql == "CREATE TABLE Users;"
        mock_aiofiles_open.assert_called_once()


@pytest.mark.asyncio
async def test_create_schema_if_not_exist_happy_path():
    """Test create_schema_if_not_exist happy path."""
    mock_connection = AsyncMock()

    with patch('src.bot.database.get_database_schema_sql', return_value="CREATE TABLE Users;") as mock_get_schema, \
         patch('aiosqlite.connect') as mock_connect:

        mock_connect.return_value.__aenter__.return_value = mock_connection
        await create_schema_if_not_exist()

        mock_get_schema.assert_called_once()
        mock_connect.assert_called_once()
        mock_connection.executescript.assert_called_once_with("CREATE TABLE Users;")
        mock_connection.commit.assert_called_once()
