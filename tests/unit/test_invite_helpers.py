import pytest
from unittest.mock import AsyncMock, patch
from src.bot.handlers.invite import is_invite_link_expired, generate_single_use_invite_link

@pytest.mark.asyncio
async def test_is_invite_link_expired_valid():
    """Test is_invite_link_expired for a valid link."""
    with patch('src.bot.handlers.invite.bot') as mock_bot:
        mock_bot.get_me = AsyncMock(return_value="some_info")
        expired = await is_invite_link_expired("http://valid.link")
        assert expired is False

@pytest.mark.asyncio
async def test_is_invite_link_expired_invalid():
    """Test is_invite_link_expired for an invalid link."""
    with patch('src.bot.handlers.invite.bot') as mock_bot:
        mock_bot.get_me.side_effect = Exception("Invalid link")
        expired = await is_invite_link_expired("http://invalid.link")
        assert expired is True

@pytest.mark.asyncio
async def test_generate_single_use_invite_link_success():
    """Test generate_single_use_invite_link on success."""
    with patch('src.bot.handlers.invite.bot') as mock_bot:
        mock_invite_link = AsyncMock()
        mock_invite_link.invite_link = "http://new.link"
        mock_bot.create_chat_invite_link = AsyncMock(return_value=mock_invite_link)

        link = await generate_single_use_invite_link(123)
        assert link == "http://new.link"

@pytest.mark.asyncio
async def test_generate_single_use_invite_link_failure():
    """Test generate_single_use_invite_link on failure."""
    with patch('src.bot.handlers.invite.bot') as mock_bot:
        mock_bot.create_chat_invite_link.side_effect = Exception("API error")
        with pytest.raises(Exception, match="API error"):
            await generate_single_use_invite_link(123)
