import pytest
from unittest.mock import AsyncMock, patch
from src.bot.handlers.close_functionality import show_private_channels

@pytest.fixture
def mock_message():
    """Fixture for a mock Message object."""
    message = AsyncMock()
    return message

@pytest.mark.asyncio
async def test_show_private_channels(mock_message):
    with patch('src.bot.handlers.close_functionality.inline_keyboard.channels', new_callable=AsyncMock) as mock_keyboard:
        mock_keyboard.return_value = "keyboard"
        await show_private_channels(mock_message)
        mock_message.answer.assert_called_once_with(
            text="You can subscribe to closed channels.",
            reply_markup="keyboard"
        )
