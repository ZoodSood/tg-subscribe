import pytest
from unittest.mock import AsyncMock, patch
from src.bot.handlers.admin import admin_dashboard, admin_dashboard_callback, create_promo_code, list_promo_codes, start_mailing_to_not_subscribed_users
from aiogram.types import CallbackQuery
from src.bot.database.models import User

@pytest.fixture
def mock_message():
    """Fixture for a mock Message object."""
    message = AsyncMock()
    message.from_user = AsyncMock()
    return message

@pytest.fixture
def mock_callback_query():
    """Fixture for a mock CallbackQuery object."""
    query = AsyncMock(spec=CallbackQuery)
    query.from_user = AsyncMock()
    query.message = AsyncMock()
    return query

@pytest.mark.asyncio
@patch('src.bot.handlers.admin.BOT_OWNER_ID', 123)
async def test_admin_dashboard_owner(mock_message):
    """Test admin_dashboard when the user is the owner."""
    mock_message.from_user.id = 123

    with patch('src.bot.handlers.admin.admin_dashboard_keyboard', new_callable=AsyncMock) as mock_keyboard:
        mock_keyboard.return_value = "keyboard"
        await admin_dashboard(mock_message)
        mock_message.answer.assert_called_once_with("<b>Admin Dashboard</b>\nChoose an action:", reply_markup="keyboard")

@pytest.mark.asyncio
@patch('src.bot.handlers.admin.BOT_OWNER_ID', 123)
async def test_admin_dashboard_not_owner(mock_message):
    """Test admin_dashboard when the user is not the owner."""
    mock_message.from_user.id = 456

    await admin_dashboard(mock_message)
    mock_message.answer.assert_called_once_with("You are not authorized to access the admin dashboard.")


@pytest.mark.asyncio
@patch('src.bot.handlers.admin.BOT_OWNER_ID', 123)
async def test_admin_dashboard_callback_owner(mock_callback_query):
    """Test admin_dashboard_callback when the user is the owner."""
    mock_callback_query.from_user.id = 123

    # Test view users
    mock_callback_query.data = "admin_view_users"
    await admin_dashboard_callback(mock_callback_query)
    mock_callback_query.message.answer.assert_called_once_with("User list feature coming soon.")

    # Test manage subs
    mock_callback_query.message.answer.reset_mock()
    mock_callback_query.data = "admin_manage_subs"
    await admin_dashboard_callback(mock_callback_query)
    mock_callback_query.message.answer.assert_called_once_with("Manage subscriptions feature coming soon.")

    # Test analytics
    mock_callback_query.message.answer.reset_mock()
    mock_callback_query.data = "admin_analytics"
    await admin_dashboard_callback(mock_callback_query)
    mock_callback_query.message.answer.assert_called_once_with("Analytics feature coming soon.")

    # Test unknown action
    mock_callback_query.message.answer.reset_mock()
    mock_callback_query.data = "admin_unknown"
    await admin_dashboard_callback(mock_callback_query)
    mock_callback_query.answer.assert_called_once_with("Unknown action.", show_alert=True)


@pytest.mark.asyncio
@patch('src.bot.handlers.admin.BOT_OWNER_ID', 123)
async def test_admin_dashboard_callback_not_owner(mock_callback_query):
    """Test admin_dashboard_callback when the user is not the owner."""
    mock_callback_query.from_user.id = 456
    mock_callback_query.data = "admin_view_users"

    await admin_dashboard_callback(mock_callback_query)
    mock_callback_query.answer.assert_called_once_with("Not authorized.", show_alert=True)

# --- create_promo_code tests ---

from aiogram.filters import CommandObject

@pytest.fixture
def mock_command():
    """Fixture for a mock CommandObject."""
    command = AsyncMock(spec=CommandObject)
    return command

@pytest.mark.asyncio
@patch('src.bot.handlers.admin.BOT_OWNER_ID', 123)
@patch('src.bot.handlers.admin.PromoCodeRepository.create', new_callable=AsyncMock)
async def test_create_promo_code_success(mock_create, mock_message, mock_command):
    mock_message.from_user.id = 123
    mock_command.args = "PROMO 10"
    mock_create.return_value = True

    await create_promo_code(mock_message, mock_command)

    mock_create.assert_called_once()
    mock_message.answer.assert_called_once_with("Promo code 'PROMO' created. Max uses: 10. Expires: never.")

@pytest.mark.asyncio
@patch('src.bot.handlers.admin.BOT_OWNER_ID', 123)
async def test_create_promo_code_not_owner(mock_message, mock_command):
    mock_message.from_user.id = 456
    await create_promo_code(mock_message, mock_command)
    mock_message.answer.assert_called_once_with("You are not authorized to create promo codes.")

@pytest.mark.asyncio
@patch('src.bot.handlers.admin.BOT_OWNER_ID', 123)
async def test_create_promo_code_no_args(mock_message, mock_command):
    mock_message.from_user.id = 123
    mock_command.args = None
    await create_promo_code(mock_message, mock_command)
    mock_message.answer.assert_called_once_with("Usage: /create_promo CODE [max_uses] [expires_at]")

# --- list_promo_codes tests ---

@pytest.mark.asyncio
@patch('src.bot.handlers.admin.BOT_OWNER_ID', 123)
async def test_list_promo_codes_not_owner(mock_message):
    mock_message.from_user.id = 456
    await list_promo_codes(mock_message)
    mock_message.answer.assert_called_once_with("You are not authorized to view promo codes.")

@pytest.mark.asyncio
@patch('src.bot.handlers.admin.BOT_OWNER_ID', 123)
@patch('aiosqlite.connect')
async def test_list_promo_codes_no_codes(mock_connect, mock_message):
    mock_message.from_user.id = 123
    mock_cursor = AsyncMock()
    mock_cursor.fetchall.return_value = []
    mock_connect.return_value.__aenter__.return_value.execute.return_value = mock_cursor

    await list_promo_codes(mock_message)
    mock_message.answer.assert_called_once_with("No promo codes found.")

@pytest.mark.asyncio
@patch('src.bot.handlers.admin.BOT_OWNER_ID', 123)
@patch('aiosqlite.connect')
async def test_list_promo_codes_with_codes(mock_connect, mock_message):
    mock_message.from_user.id = 123
    mock_cursor = AsyncMock()
    mock_cursor.fetchall.return_value = [("PROMO1", 1, 5, 10, None), ("PROMO2", 0, 1, 1, "2025-01-01")]
    mock_connect.return_value.__aenter__.return_value.execute.return_value = mock_cursor

    await list_promo_codes(mock_message)
    mock_message.answer.assert_called_once()
    assert "<b>Promo Codes:</b>" in mock_message.answer.call_args[0][0]
    assert "PROMO1" in mock_message.answer.call_args[0][0]
    assert "PROMO2" in mock_message.answer.call_args[0][0]


# --- start_mailing tests ---

@pytest.mark.asyncio
@patch('src.bot.handlers.admin.UserRepository')
@patch('src.bot.handlers.admin.bot')
async def test_start_mailing(mock_bot, mock_user_repo, mock_message):
    """Test the start_mailing handler."""
    mock_message.from_user.id = 123

    users = [
        User(id=1, telegram_id=123, first_name='Admin', last_name='User', username='admin', days_sub_end='2025-01-01 00:00:00', balance=0, invite_link='', is_banned=0, last_active=None),
        User(id=2, telegram_id=456, first_name='Subscribed', last_name='User', username='sub', days_sub_end='2025-12-31 00:00:00', balance=0, invite_link='', is_banned=0, last_active=None),
        User(id=3, telegram_id=789, first_name='NotSubscribed', last_name='User', username='notsub', days_sub_end='2020-01-01 00:00:00', balance=0, invite_link='', is_banned=0, last_active=None),
    ]
    mock_user_repo.get_all = AsyncMock(return_value=users)
    mock_bot.send_message = AsyncMock()

    await start_mailing_to_not_subscribed_users(mock_message)

    mock_bot.send_message.assert_called_once_with(chat_id=789, text="Hello")
    mock_message.answer.assert_called_once()
