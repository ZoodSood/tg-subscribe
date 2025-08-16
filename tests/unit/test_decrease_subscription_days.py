import pytest
from unittest.mock import AsyncMock, patch
from src.bot.utils.decrease_subscription_days import task
from src.bot.database.models import User
from datetime import datetime, timedelta

@pytest.fixture
def mock_bot():
    """Fixture for a mock Bot object."""
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    return bot

@pytest.mark.asyncio
@patch('src.bot.utils.decrease_subscription_days.UserRepository')
@patch('src.bot.utils.decrease_subscription_days.SUBSCRIBE_END_NOTIFICATION_DAYS', [3, 1])
async def test_decrease_subscription_days_task(mock_user_repo, mock_bot):
    """Test the decrease_subscription_days task."""
    # A user whose subscription ends in 3 days
    three_days_from_now = (datetime.now() + timedelta(days=2, hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    # A user whose subscription ends in 1 day
    one_day_from_now = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    # A user whose subscription is not ending soon
    ten_days_from_now = (datetime.now() + timedelta(days=9, hours=1)).strftime("%Y-%m-%d %H:%M:%S")

    users = [
        User(id=1, telegram_id=123, first_name='User1', last_name='Test', username='user1', days_sub_end=three_days_from_now, balance=0, invite_link='', is_banned=0, last_active=None),
        User(id=2, telegram_id=456, first_name='User2', last_name='Test', username='user2', days_sub_end=one_day_from_now, balance=0, invite_link='', is_banned=0, last_active=None),
        User(id=3, telegram_id=789, first_name='User3', last_name='Test', username='user3', days_sub_end=ten_days_from_now, balance=0, invite_link='', is_banned=0, last_active=None),
    ]
    mock_user_repo.get_all = AsyncMock(return_value=users)

    await task(mock_bot)

    # Should send notifications to the first two users
    assert mock_bot.send_message.call_count == 2
    mock_bot.send_message.assert_any_call(chat_id=123, text="Your subscription will end soon!\n<code>3</code> days left until the end.")
    mock_bot.send_message.assert_any_call(chat_id=456, text="Your subscription will end soon!\n<code>1</code> day left until the end.")


@pytest.mark.asyncio
@patch('src.bot.utils.decrease_subscription_days.UserRepository')
@patch('src.bot.utils.decrease_subscription_days.SUBSCRIBE_END_NOTIFICATION_DAYS', [1])
async def test_decrease_subscription_days_task_send_exception(mock_user_repo, mock_bot):
    """Test the task when send_message raises an exception."""
    one_day_from_now = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    users = [User(id=1, telegram_id=123, first_name='User1', last_name='Test', username='user1', days_sub_end=one_day_from_now, balance=0, invite_link='', is_banned=0, last_active=None)]
    mock_user_repo.get_all = AsyncMock(return_value=users)
    mock_bot.send_message.side_effect = Exception("API error")

    # The exception should be caught, so the test should pass without errors.
    await task(mock_bot)

    mock_bot.send_message.assert_called_once()


@pytest.mark.asyncio
@patch('src.bot.utils.decrease_subscription_days.UserRepository')
@patch('src.bot.utils.decrease_subscription_days.SUBSCRIBE_END_NOTIFICATION_DAYS', [3])
async def test_decrease_subscription_days_task_send_exception_else_case(mock_user_repo, mock_bot):
    """Test the task when send_message raises an exception in the else case."""
    three_days_from_now = (datetime.now() + timedelta(days=2, hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    users = [User(id=1, telegram_id=123, first_name='User1', last_name='Test', username='user1', days_sub_end=three_days_from_now, balance=0, invite_link='', is_banned=0, last_active=None)]
    mock_user_repo.get_all = AsyncMock(return_value=users)
    mock_bot.send_message.side_effect = Exception("API error")

    await task(mock_bot)

    mock_bot.send_message.assert_called_once()
