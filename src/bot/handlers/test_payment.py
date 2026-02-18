import pytest
from unittest.mock import patch, AsyncMock, MagicMock, ANY
from handlers.payment import check_transaction

@pytest.mark.asyncio
@patch("utils.solana_service.is_valid_transaction_signature")
@patch("utils.solana_service.check_transaction_for_correct_data")
@patch("database.transactions.get")
@patch("database.transactions.get_new")
@patch("database.transactions.create")
@patch("database.users.get")
@patch("database.users.update_subscription_date")
@patch("utils.rate_limiter.is_allowed")
async def test_check_transaction_success(
    mock_rate_limit, mock_user_update, mock_user_get,
    mock_tx_create, mock_tx_get_new, mock_tx_get,
    mock_sol_check, mock_sol_valid
):
    # Setup mocks
    mock_rate_limit.return_value = True
    mock_tx_get.return_value = None
    mock_tx_get_new.return_value = []
    mock_sol_valid.return_value = True
    mock_sol_check.return_value = True

    user_mock = MagicMock()
    user_mock.days_sub_end = "2023-01-01 00:00:00"
    mock_user_get.return_value = user_mock

    # Setup Message and State mocks
    message = AsyncMock()
    message.text = "5V9Y1v2J8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7z8v7zA"
    message.from_user.id = 12345

    state = AsyncMock()
    state.get_data.return_value = {"subscription_termin": 1}

    # Call function
    await check_transaction(message, state)

    # Assertions
    # Check if answer was called with success message
    args, kwargs = message.answer.call_args
    assert "Great, wait for the end of the transaction" in kwargs["text"]

    state.clear.assert_called_once()
    mock_tx_create.assert_called_once()
    mock_user_update.assert_called_once()

@pytest.mark.asyncio
@patch("utils.solana_service.is_valid_transaction_signature")
@patch("utils.rate_limiter.is_allowed")
@patch("database.transactions.get")
@patch("database.transactions.get_new")
async def test_check_transaction_invalid_signature(
    mock_tx_get_new, mock_tx_get, mock_rate_limit, mock_sol_valid
):
    mock_rate_limit.return_value = True
    mock_tx_get.return_value = None
    mock_tx_get_new.return_value = []
    mock_sol_valid.return_value = False

    message = AsyncMock()
    message.text = "invalid_sig"
    message.from_user.id = 12345

    state = AsyncMock()
    state.get_data.return_value = {"subscription_termin": 1}

    await check_transaction(message, state)

    args, kwargs = message.answer.call_args
    assert "Invalid transaction signature format" in kwargs["text"]
    state.set_state.assert_called()
