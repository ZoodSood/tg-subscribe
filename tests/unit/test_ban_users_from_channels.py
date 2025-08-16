import pytest
from unittest.mock import AsyncMock, patch
from src.bot.utils.ban_users_from_channels import task
from src.bot.database.models import User
from datetime import datetime

@pytest.fixture
def mock_bot():
    """Fixture for a mock Bot object."""
    bot = AsyncMock()
    bot.get_chat.return_value = AsyncMock(id=-100)
    bot.get_chat_member.return_value = AsyncMock(status="member")
    bot.ban_chat_member = AsyncMock()
    bot.unban_chat_member = AsyncMock()
    return bot

@pytest.mark.asyncio
@patch('src.bot.utils.ban_users_from_channels.UserRepository')
@patch('src.bot.utils.ban_users_from_channels.private_channels', {"Channel 1": {"id": -100}})
async def test_ban_users_task(mock_user_repo, mock_bot):
    """Test the ban users task."""
    future_date = datetime(2025, 12, 31).strftime("%Y-%m-%d %H:%M:%S")
    past_date = datetime(2020, 1, 1).strftime("%Y-%m-%d %H:%M:%S")

    users = [
        User(id=1, telegram_id=456, first_name='Subscribed', last_name='User', username='sub', days_sub_end=future_date, balance=0, invite_link='', is_banned=0, last_active=None),
        User(id=2, telegram_id=789, first_name='NotSubscribed', last_name='User', username='notsub', days_sub_end=past_date, balance=0, invite_link='', is_banned=0, last_active=None),
    ]
    mock_user_repo.get_all = AsyncMock(return_value=users)

    await task(mock_bot)

    # Should try to ban the not-subscribed user
    mock_bot.ban_chat_member.assert_called_once_with(-100, 789)
    mock_bot.unban_chat_member.assert_called_once_with(-100, 789)


@pytest.mark.asyncio
@patch('src.bot.utils.ban_users_from_channels.UserRepository')
@patch('src.bot.utils.ban_users_from_channels.private_channels', {"Channel 1": {"id": -100}})
async def test_ban_users_task_get_member_exception(mock_user_repo, mock_bot):
    """Test the task when get_chat_member raises an exception."""
    past_date = datetime(2020, 1, 1).strftime("%Y-%m-%d %H:%M:%S")
    users = [User(id=1, telegram_id=789, first_name='NotSubscribed', last_name='User', username='notsub', days_sub_end=past_date, balance=0, invite_link='', is_banned=0, last_active=None)]
    mock_user_repo.get_all = AsyncMock(return_value=users)
    mock_bot.get_chat_member.side_effect = Exception("API error")

    await task(mock_bot)

    mock_bot.ban_chat_member.assert_not_called()

@pytest.mark.asyncio
@patch('src.bot.utils.ban_users_from_channels.UserRepository')
@patch('src.bot.utils.ban_users_from_channels.private_channels', {"Channel 1": {"id": -100}})
async def test_ban_users_task_member_is_creator(mock_user_repo, mock_bot):
    """Test the task when the member is the creator."""
    past_date = datetime(2020, 1, 1).strftime("%Y-%m-%d %H:%M:%S")
    users = [User(id=1, telegram_id=789, first_name='NotSubscribed', last_name='User', username='notsub', days_sub_end=past_date, balance=0, invite_link='', is_banned=0, last_active=None)]
    mock_user_repo.get_all = AsyncMock(return_value=users)
    # Re-create the mock bot inside this test to modify its return value for this specific test
    mock_bot_local = AsyncMock()
    mock_bot_local.get_chat.return_value = AsyncMock(id=-100)
    mock_bot_local.get_chat_member.return_value = AsyncMock(status="creator")

    await task(mock_bot_local)

    mock_bot_local.ban_chat_member.assert_not_called()

@pytest.mark.asyncio
@patch('src.bot.utils.ban_users_from_channels.UserRepository')
@patch('src.bot.utils.ban_users_from_channels.private_channels', {"Channel 1": {"id": -100}})
async def test_ban_users_task_ban_exception(mock_user_repo, mock_bot):
    """Test the task when ban_chat_member raises an exception."""
    past_date = datetime(2020, 1, 1).strftime("%Y-%m-%d %H:%M:%S")
    users = [User(id=1, telegram_id=789, first_name='NotSubscribed', last_name='User', username='notsub', days_sub_end=past_date, balance=0, invite_link='', is_banned=0, last_active=None)]
    mock_user_repo.get_all = AsyncMock(return_value=users)
    mock_bot.ban_chat_member.side_effect = Exception("API error")

    await task(mock_bot)

    mock_bot.ban_chat_member.assert_called_once()
    mock_bot.unban_chat_member.assert_not_called()
