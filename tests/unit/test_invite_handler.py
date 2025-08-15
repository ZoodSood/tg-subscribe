import pytest
from unittest.mock import AsyncMock, patch
from src.bot.handlers.invite import invite_link_handler
from src.bot.database.models import User

@pytest.fixture
def mock_message():
    """Fixture for a mock Message object."""
    message = AsyncMock()
    message.from_user.id = 123
    return message

@pytest.mark.asyncio
async def test_invite_link_handler_new_link(mock_message):
    """Test the invite link handler when a new link needs to be generated."""
    mock_user = User(id=1, telegram_id=123, first_name='Test', last_name='User', username='testuser', days_sub_end='', balance=0, invite_link=None, is_banned=0, last_active=None)

    with patch('src.bot.handlers.invite.UserRepository') as mock_user_repo, \
         patch('src.bot.handlers.invite.generate_single_use_invite_link') as mock_generate_link:

        mock_user_repo.get = AsyncMock(return_value=mock_user)
        mock_user_repo.update_invite_link = AsyncMock()
        mock_generate_link.return_value = "http://new.link"

        await invite_link_handler(mock_message)

        mock_user_repo.get.assert_called_once_with(telegram_id=123)
        mock_generate_link.assert_called_once()
        mock_user_repo.update_invite_link.assert_called_once_with("http://new.link", telegram_id=123)
        mock_message.answer.assert_called_once_with(text="Your unique channel invite link: http://new.link")

@pytest.mark.asyncio
async def test_invite_link_handler_existing_valid_link(mock_message):
    """Test the invite link handler when the user has a valid existing link."""
    mock_user = User(id=1, telegram_id=123, first_name='Test', last_name='User', username='testuser', days_sub_end='', balance=0, invite_link="http://existing.link", is_banned=0, last_active=None)

    with patch('src.bot.handlers.invite.UserRepository') as mock_user_repo, \
         patch('src.bot.handlers.invite.generate_single_use_invite_link') as mock_generate_link, \
         patch('src.bot.handlers.invite.is_invite_link_expired', return_value=False) as mock_is_expired:

        mock_user_repo.get = AsyncMock(return_value=mock_user)

        await invite_link_handler(mock_message)

        mock_is_expired.assert_called_once_with("http://existing.link")
        mock_generate_link.assert_not_called()
        mock_message.answer.assert_called_once_with(text="Your unique channel invite link: http://existing.link")

@pytest.mark.asyncio
async def test_invite_link_handler_existing_expired_link(mock_message):
    """Test the invite link handler when the user has an expired existing link."""
    mock_user = User(id=1, telegram_id=123, first_name='Test', last_name='User', username='testuser', days_sub_end='', balance=0, invite_link="http://expired.link", is_banned=0, last_active=None)

    with patch('src.bot.handlers.invite.UserRepository') as mock_user_repo, \
         patch('src.bot.handlers.invite.generate_single_use_invite_link', return_value="http://new.link") as mock_generate_link, \
         patch('src.bot.handlers.invite.is_invite_link_expired', return_value=True) as mock_is_expired:

        mock_user_repo.get = AsyncMock(return_value=mock_user)
        mock_user_repo.update_invite_link = AsyncMock()

        await invite_link_handler(mock_message)

        mock_is_expired.assert_called_once_with("http://expired.link")
        mock_generate_link.assert_called_once()
        mock_user_repo.update_invite_link.assert_called_once_with("http://new.link", telegram_id=123)
        mock_message.answer.assert_called_once_with(text="Your unique channel invite link: http://new.link")

@pytest.mark.asyncio
async def test_invite_link_handler_generation_fails(mock_message):
    """Test the invite link handler when link generation fails."""
    mock_user = User(id=1, telegram_id=123, first_name='Test', last_name='User', username='testuser', days_sub_end='', balance=0, invite_link=None, is_banned=0, last_active=None)

    with patch('src.bot.handlers.invite.UserRepository') as mock_user_repo, \
         patch('src.bot.handlers.invite.generate_single_use_invite_link', side_effect=Exception("API error")) as mock_generate_link:

        mock_user_repo.get = AsyncMock(return_value=mock_user)

        await invite_link_handler(mock_message)

        mock_generate_link.assert_called_once()
        mock_message.answer.assert_called_once_with("Sorry, failed to generate an invite link. Please try again later.")

@pytest.mark.asyncio
async def test_invite_link_handler_no_user(mock_message):
    """Test the handler when message.from_user is None."""
    mock_message.from_user = None
    with patch('src.bot.handlers.invite.UserRepository') as mock_user_repo:
        await invite_link_handler(mock_message)
        mock_user_repo.get.assert_not_called()

@pytest.mark.asyncio
async def test_invite_link_handler_user_not_found(mock_message):
    """Test the handler when the user is not found in the database."""
    with patch('src.bot.handlers.invite.UserRepository') as mock_user_repo:
        mock_user_repo.get = AsyncMock(return_value=None)
        await invite_link_handler(mock_message)
        mock_user_repo.get.assert_called_once_with(telegram_id=123)
        mock_message.answer.assert_not_called()
