import pytest
from unittest.mock import AsyncMock, patch
from src.bot.handlers.balance import show_balance
from src.bot.database.models import User

@pytest.fixture
def mock_message():
    """Fixture for a mock Message object."""
    message = AsyncMock()
    message.from_user = AsyncMock()
    message.from_user.id = 123
    return message

@pytest.mark.asyncio
async def test_show_balance_user_found(mock_message):
    """Test show_balance when the user is found."""
    mock_user = User(id=1, telegram_id=123, first_name='Test', last_name='User', username='testuser', days_sub_end='', balance=100, invite_link='', is_banned=0, last_active=None)
    with patch('src.bot.handlers.balance.UserRepository.get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_user
        await show_balance(mock_message)
        mock_message.answer.assert_called_once_with(text="Your balance: <code>100</code>")

@pytest.mark.asyncio
async def test_show_balance_user_not_found(mock_message):
    """Test show_balance when the user is not found."""
    with patch('src.bot.handlers.balance.UserRepository.get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        await show_balance(mock_message)
        mock_message.answer.assert_not_called()

@pytest.mark.asyncio
async def test_show_balance_no_user(mock_message):
    """Test show_balance when message.from_user is None."""
    mock_message.from_user = None
    with patch('src.bot.handlers.balance.UserRepository.get', new_callable=AsyncMock) as mock_get:
        await show_balance(mock_message)
        mock_get.assert_not_called()
