import pytest
from unittest.mock import AsyncMock, patch
from src.bot.handlers.check_subscription import check_subscription
from src.bot.database.models import User
from datetime import datetime, timedelta

@pytest.fixture
def mock_message():
    """Fixture for a mock Message object."""
    message = AsyncMock()
    message.from_user = AsyncMock()
    message.from_user.id = 123
    return message

@pytest.mark.asyncio
async def test_check_subscription_active(mock_message):
    """Test when the user has an active subscription."""
    future_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    mock_user = User(id=1, telegram_id=123, first_name='Test', last_name='User', username='testuser', days_sub_end=future_date, balance=0, invite_link='', is_banned=0, last_active=None)
    with patch('src.bot.handlers.check_subscription.UserRepository.get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_user
        await check_subscription(mock_message)
        mock_message.answer.assert_called_once_with(text=f"Your subscription is active until <code>{future_date}</code>")

@pytest.mark.asyncio
async def test_check_subscription_expired(mock_message):
    """Test when the user's subscription has expired."""
    past_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    mock_user = User(id=1, telegram_id=123, first_name='Test', last_name='User', username='testuser', days_sub_end=past_date, balance=0, invite_link='', is_banned=0, last_active=None)
    with patch('src.bot.handlers.check_subscription.UserRepository.get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_user
        await check_subscription(mock_message)
        mock_message.answer.assert_called_once_with(text=f"Your subscription has expired <code>{past_date}</code>")

@pytest.mark.asyncio
async def test_check_subscription_user_not_found(mock_message):
    """Test when the user is not found."""
    with patch('src.bot.handlers.check_subscription.UserRepository.get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        await check_subscription(mock_message)
        mock_message.answer.assert_not_called()

@pytest.mark.asyncio
async def test_check_subscription_no_user(mock_message):
    """Test when message.from_user is None."""
    mock_message.from_user = None
    with patch('src.bot.handlers.check_subscription.UserRepository.get', new_callable=AsyncMock) as mock_get:
        await check_subscription(mock_message)
        mock_get.assert_not_called()
