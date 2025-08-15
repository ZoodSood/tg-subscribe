import pytest
from unittest.mock import AsyncMock, patch
from src.bot.handlers.channels_join_requests import private_channel_join_request
from src.bot.database.models import User
from datetime import datetime, timedelta

@pytest.fixture
def mock_join_request():
    """Fixture for a mock ChatJoinRequest object."""
    request = AsyncMock()
    request.from_user = AsyncMock()
    request.from_user.id = 123
    return request

@pytest.mark.asyncio
async def test_private_channel_join_request_approved(mock_join_request):
    """Test when the user is subscribed and the request is approved."""
    future_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    mock_user = User(id=1, telegram_id=123, first_name='Test', last_name='User', username='testuser', days_sub_end=future_date, balance=0, invite_link='', is_banned=0, last_active=None)
    with patch('src.bot.handlers.channels_join_requests.UserRepository.get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_user
        await private_channel_join_request(mock_join_request)
        mock_join_request.approve.assert_called_once()
        mock_join_request.decline.assert_not_called()

@pytest.mark.asyncio
async def test_private_channel_join_request_declined(mock_join_request):
    """Test when the user is not subscribed and the request is declined."""
    past_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    mock_user = User(id=1, telegram_id=123, first_name='Test', last_name='User', username='testuser', days_sub_end=past_date, balance=0, invite_link='', is_banned=0, last_active=None)
    with patch('src.bot.handlers.channels_join_requests.UserRepository.get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_user
        await private_channel_join_request(mock_join_request)
        mock_join_request.decline.assert_called_once()
        mock_join_request.approve.assert_not_called()

@pytest.mark.asyncio
async def test_private_channel_join_request_user_not_found(mock_join_request):
    """Test when the user is not found."""
    with patch('src.bot.handlers.channels_join_requests.UserRepository.get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        await private_channel_join_request(mock_join_request)
        mock_join_request.approve.assert_not_called()
        mock_join_request.decline.assert_not_called()
