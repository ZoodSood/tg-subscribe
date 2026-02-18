import pytest
from unittest.mock import AsyncMock, patch
from src.bot.utils.subscription_checker import task
from src.bot.database.models import Transaction, User

@pytest.fixture
def mock_bot():
    """Fixture for a mock Bot object."""
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    return bot

@pytest.mark.asyncio
@patch('src.bot.utils.subscription_checker.TransactionRepository')
@patch('src.bot.utils.subscription_checker.UserRepository')
@patch('src.bot.utils.subscription_checker.solana_service')
@patch('src.bot.utils.subscription_checker.reply')
async def test_subscription_checker_task_valid_transaction(mock_reply, mock_solana, mock_user_repo, mock_trans_repo, mock_bot):
    """Test the subscription checker task with a valid transaction."""
    mock_trans = Transaction(id=1, txid="valid_txid", owner_telegram_id=123, status=False, weeks=1, amount_sol="0.5", created_at_timestamp=0)
    mock_trans_repo.get_new = AsyncMock(return_value=[mock_trans])
    mock_trans_repo.set_status = AsyncMock()
    mock_user_repo.get = AsyncMock(return_value=User(id=1, telegram_id=123, first_name='Test', last_name='User', username='testuser', days_sub_end='', balance=0, invite_link='', is_banned=0, last_active=None))
    mock_user_repo.update_subscription_date = AsyncMock()
    mock_solana.check_transaction_for_correct_data = AsyncMock(return_value=True)
    mock_reply.back_to_main_menu = AsyncMock(return_value="keyboard")

    # Mock PriceService
    with patch('src.bot.utils.subscription_checker.PriceService.get_sol_price_in_usd', new_callable=AsyncMock) as mock_price:
        mock_price.return_value = 100
        await task(mock_bot)

    mock_trans_repo.set_status.assert_called_once_with(True, database_id=1)
    mock_user_repo.update_subscription_date.assert_called_once()
    mock_bot.send_message.assert_called_once()
    assert "Your subscription has been activated!" in mock_bot.send_message.call_args[1]['text']

@pytest.mark.asyncio
@patch('src.bot.utils.subscription_checker.TransactionRepository')
@patch('src.bot.utils.subscription_checker.UserRepository')
@patch('src.bot.utils.subscription_checker.solana_service')
@patch('src.bot.utils.subscription_checker.reply')
async def test_subscription_checker_task_invalid_transaction(mock_reply, mock_solana, mock_user_repo, mock_trans_repo, mock_bot):
    """Test the subscription checker task with an invalid transaction."""
    mock_trans = Transaction(id=1, txid="invalid_txid", owner_telegram_id=123, status=False, weeks=1, amount_sol="0.5", created_at_timestamp=0)
    mock_trans_repo.get_new = AsyncMock(return_value=[mock_trans])
    mock_solana.check_transaction_for_correct_data = AsyncMock(return_value=False)
    mock_user_repo.get = AsyncMock(return_value=User(id=1, telegram_id=123, first_name='Test', last_name='User', username='testuser', days_sub_end='', balance=0, invite_link='', is_banned=0, last_active=None))

    await task(mock_bot)

    mock_trans_repo.set_status.assert_not_called()
    mock_user_repo.update_subscription_date.assert_not_called()
    mock_bot.send_message.assert_called_once()
    assert "Transaction verification failed" in mock_bot.send_message.call_args[1]['text']

@pytest.mark.asyncio
@patch('src.bot.utils.subscription_checker.TransactionRepository')
async def test_subscription_checker_task_no_transactions(mock_trans_repo, mock_bot):
    """Test the subscription checker task with no new transactions."""
    mock_trans_repo.get_new = AsyncMock(return_value=[])

    await task(mock_bot)

    mock_bot.send_message.assert_not_called()

@pytest.mark.asyncio
@patch('src.bot.utils.subscription_checker.TransactionRepository')
@patch('src.bot.utils.subscription_checker.UserRepository')
@patch('src.bot.utils.subscription_checker.solana_service')
@patch('src.bot.utils.subscription_checker.reply')
async def test_subscription_checker_task_valid_transaction_send_error(mock_reply, mock_solana, mock_user_repo, mock_trans_repo, mock_bot):
    """Test the subscription checker task with a valid transaction but an error sending the message."""
    mock_trans = Transaction(id=1, txid="valid_txid", owner_telegram_id=123, status=False, weeks=1, amount_sol="0.5", created_at_timestamp=0)
    mock_trans_repo.get_new = AsyncMock(return_value=[mock_trans])
    mock_trans_repo.set_status = AsyncMock()
    mock_user_repo.get = AsyncMock(return_value=User(id=1, telegram_id=123, first_name='Test', last_name='User', username='testuser', days_sub_end='', balance=0, invite_link='', is_banned=0, last_active=None))
    mock_user_repo.update_subscription_date = AsyncMock()
    mock_solana.check_transaction_for_correct_data = AsyncMock(return_value=True)
    mock_reply.back_to_main_menu = AsyncMock(return_value="keyboard")
    mock_bot.send_message.side_effect = Exception("Send error")

    # Mock PriceService
    with patch('src.bot.utils.subscription_checker.PriceService.get_sol_price_in_usd', new_callable=AsyncMock) as mock_price:
        mock_price.return_value = 100
        await task(mock_bot)

    mock_trans_repo.set_status.assert_called_once_with(True, database_id=1)
    mock_user_repo.update_subscription_date.assert_called_once()
    mock_bot.send_message.assert_called_once()

@pytest.mark.asyncio
@patch('src.bot.utils.subscription_checker.TransactionRepository')
@patch('src.bot.utils.subscription_checker.UserRepository')
@patch('src.bot.utils.subscription_checker.solana_service')
async def test_subscription_checker_task_invalid_transaction_send_error(mock_solana, mock_user_repo, mock_trans_repo, mock_bot):
    """Test the subscription checker task with an invalid transaction and an error sending the message."""
    mock_trans = Transaction(id=1, txid="invalid_txid", owner_telegram_id=123, status=False, weeks=1, amount_sol="0.5", created_at_timestamp=0)
    mock_trans_repo.get_new = AsyncMock(return_value=[mock_trans])
    mock_solana.check_transaction_for_correct_data = AsyncMock(return_value=False)
    mock_user_repo.get = AsyncMock(return_value=User(id=1, telegram_id=123, first_name='Test', last_name='User', username='testuser', days_sub_end='', balance=0, invite_link='', is_banned=0, last_active=None))
    mock_bot.send_message.side_effect = Exception("Send error")

    await task(mock_bot)

    mock_bot.send_message.assert_called_once()
