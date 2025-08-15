import pytest
from unittest.mock import AsyncMock, patch
from src.bot.handlers.start import start_for_subsribed_user, start_for_not_subsribed_user
from src.bot.database.models import User
from aiogram.fsm.context import FSMContext

@pytest.fixture
def mock_message():
    """Fixture for a mock Message object."""
    message = AsyncMock()
    message.from_user = AsyncMock()
    message.from_user.id = 123
    return message

@pytest.fixture
def mock_state():
    """Fixture for a mock FSMContext object."""
    state = AsyncMock(spec=FSMContext)
    return state

@pytest.mark.asyncio
async def test_start_for_subscribed_user_found(mock_message, mock_state):
    """Test start_for_subsribed_user when user is found."""
    mock_user = User(id=1, telegram_id=123, first_name='Test', last_name='User', username='testuser', days_sub_end='2025-01-01 00:00:00', balance=0, invite_link='', is_banned=0, last_active=None)
    with patch('src.bot.handlers.start.UserRepository.get', new_callable=AsyncMock) as mock_get, \
         patch('src.bot.handlers.start.reply_keyboards.close_functionality', new_callable=AsyncMock) as mock_keyboard:
        mock_get.return_value = mock_user
        mock_keyboard.return_value = "keyboard"

        await start_for_subsribed_user(mock_message, mock_state)

        mock_state.clear.assert_called_once()
        mock_message.answer.assert_called_once()
        assert "Your subscription is active until" in mock_message.answer.call_args[1]['text']

@pytest.mark.asyncio
async def test_start_for_subscribed_user_not_found(mock_message, mock_state):
    """Test start_for_subsribed_user when user is not found."""
    with patch('src.bot.handlers.start.UserRepository.get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        await start_for_subsribed_user(mock_message, mock_state)
        mock_message.answer.assert_not_called()

@pytest.mark.asyncio
async def test_start_for_subscribed_user_no_user(mock_message, mock_state):
    """Test start_for_subsribed_user when message.from_user is None."""
    mock_message.from_user = None
    with patch('src.bot.handlers.start.UserRepository.get', new_callable=AsyncMock) as mock_get:
        await start_for_subsribed_user(mock_message, mock_state)
        mock_get.assert_not_called()

@pytest.mark.asyncio
async def test_start_for_not_subscribed_user(mock_message, mock_state):
    """Test start_for_not_subsribed_user."""
    with patch('src.bot.handlers.start.reply_keyboards.make_subscribtion', new_callable=AsyncMock) as mock_keyboard:
        mock_keyboard.return_value = "keyboard"

        await start_for_not_subsribed_user(mock_message, mock_state)

        mock_state.clear.assert_called_once()
        mock_message.answer.assert_called_once_with(text="Hello. Subscribe to the bot to get access to the closed functionality.", reply_markup="keyboard")
