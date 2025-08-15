import pytest
from unittest.mock import AsyncMock, patch
from src.bot.filters.is_admin import IsAdminFilter

@pytest.fixture
def mock_message():
    """Fixture for a mock Message object."""
    message = AsyncMock()
    message.from_user = AsyncMock()
    return message

@pytest.mark.asyncio
@patch('src.bot.filters.is_admin.ADMINS_ID_LIST', [123])
async def test_is_admin_filter_is_admin(mock_message):
    """Test IsAdminFilter when the user is an admin."""
    mock_message.from_user.id = 123
    is_admin_filter = IsAdminFilter()
    result = await is_admin_filter(mock_message)
    assert result is True

@pytest.mark.asyncio
@patch('src.bot.filters.is_admin.ADMINS_ID_LIST', [123])
async def test_is_admin_filter_not_admin(mock_message):
    """Test IsAdminFilter when the user is not an admin."""
    mock_message.from_user.id = 456
    is_admin_filter = IsAdminFilter()
    result = await is_admin_filter(mock_message)
    assert result is False


# --- UserNotSubscribedFilter tests ---

from src.bot.filters.user_not_subscribed import UserNotSubscribedFilter
from src.bot.database.models import User
from datetime import datetime, timedelta

@pytest.mark.asyncio
async def test_user_not_subscribed_filter_not_subscribed(mock_message):
    """Test UserNotSubscribedFilter when user is not subscribed."""
    past_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    mock_user = User(id=1, telegram_id=123, first_name='Test', last_name='User', username='testuser', days_sub_end=past_date, balance=0, invite_link='', is_banned=0, last_active=None)

    with patch('src.bot.filters.user_not_subscribed.UserRepository.get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_user
        user_filter = UserNotSubscribedFilter()
        result = await user_filter(mock_message)
        assert result is True

@pytest.mark.asyncio
async def test_user_not_subscribed_filter_is_subscribed(mock_message):
    """Test UserNotSubscribedFilter when user is subscribed."""
    future_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    mock_user = User(id=1, telegram_id=123, first_name='Test', last_name='User', username='testuser', days_sub_end=future_date, balance=0, invite_link='', is_banned=0, last_active=None)

    with patch('src.bot.filters.user_not_subscribed.UserRepository.get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_user
        user_filter = UserNotSubscribedFilter()
        result = await user_filter(mock_message)
        assert result is False

@pytest.mark.asyncio
async def test_user_not_subscribed_filter_user_not_found(mock_message):
    """Test UserNotSubscribedFilter when user is not found."""
    with patch('src.bot.filters.user_not_subscribed.UserRepository.get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        user_filter = UserNotSubscribedFilter()
        result = await user_filter(mock_message)
        assert result is False

@pytest.mark.asyncio
async def test_user_not_subscribed_filter_no_user(mock_message):
    """Test UserNotSubscribedFilter when message.from_user is None."""
    mock_message.from_user = None
    user_filter = UserNotSubscribedFilter()
    result = await user_filter(mock_message)
    assert result is False


# --- UserSubscribedFilter tests ---
from src.bot.filters.user_subscribed import UserSubscribedFilter

@pytest.mark.asyncio
async def test_user_subscribed_filter_is_subscribed(mock_message):
    """Test UserSubscribedFilter when user is subscribed."""
    future_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    mock_user = User(id=1, telegram_id=123, first_name='Test', last_name='User', username='testuser', days_sub_end=future_date, balance=0, invite_link='', is_banned=0, last_active=None)

    with patch('src.bot.filters.user_subscribed.UserRepository.get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_user
        user_filter = UserSubscribedFilter()
        result = await user_filter(mock_message)
        assert result is True

@pytest.mark.asyncio
async def test_user_subscribed_filter_not_subscribed(mock_message):
    """Test UserSubscribedFilter when user is not subscribed."""
    past_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    mock_user = User(id=1, telegram_id=123, first_name='Test', last_name='User', username='testuser', days_sub_end=past_date, balance=0, invite_link='', is_banned=0, last_active=None)

    with patch('src.bot.filters.user_subscribed.UserRepository.get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_user
        user_filter = UserSubscribedFilter()
        result = await user_filter(mock_message)
        assert result is False

@pytest.mark.asyncio
async def test_user_subscribed_filter_user_not_found(mock_message):
    """Test UserSubscribedFilter when user is not found."""
    with patch('src.bot.filters.user_subscribed.UserRepository.get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        user_filter = UserSubscribedFilter()
        result = await user_filter(mock_message)
        assert result is False

@pytest.mark.asyncio
async def test_user_subscribed_filter_no_user(mock_message):
    """Test UserSubscribedFilter when message.from_user is None."""
    mock_message.from_user = None
    user_filter = UserSubscribedFilter()
    result = await user_filter(mock_message)
    assert result is False
