import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock
import importlib

from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, User, Chat

# We need to import the handlers module to get the router
from src.bot.handlers import payment
from src.bot.services.payment_validator import PaymentValidator
from src.bot.services.price_service import PriceService
from src.bot.statesgroup import GetTxidFromUser

@pytest.fixture
async def dispatcher():
    # Re-import the payment module to get a fresh router instance for each test
    importlib.reload(payment)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.include_router(payment.payment_router)
    yield dp, storage

@pytest.fixture
def mock_services():
    with patch("src.bot.handlers.payment.PaymentValidator", spec=PaymentValidator) as mock_validator, \
         patch("src.bot.handlers.payment.PriceService", spec=PriceService) as mock_price_service, \
         patch("src.bot.handlers.payment.TransactionRepository") as mock_transaction_repo, \
         patch("src.bot.handlers.payment.UserRepository") as mock_user_repo:

        mock_price_service.get_sol_price_in_usd = AsyncMock(return_value=Decimal("150.0"))
        mock_validator.validate_transaction = AsyncMock(return_value=(True, "Success"))
        mock_transaction_repo.create = AsyncMock()
        mock_user_repo.get = AsyncMock(return_value=MagicMock(days_sub_end=None))
        mock_user_repo.update_subscription_date = AsyncMock()

        yield {
            "validator": mock_validator,
            "price_service": mock_price_service,
            "transactions": mock_transaction_repo,
            "users": mock_user_repo,
        }

@pytest.mark.asyncio
@patch("aiogram.types.Message.answer", new_callable=AsyncMock)
async def test_set_subscription_term_handler(mock_answer, dispatcher, mock_services):
    dp, storage = dispatcher
    bot = AsyncMock()

    chat = Chat(id=123, type="private")
    user = User(id=123, is_bot=False, first_name="Test")
    message = Message(message_id=1, date=1, chat=chat, from_user=user, text="1 week")

    state = dp.fsm.get_context(bot, user.id, chat.id)

    await payment.set_subscription_term(message, state)

    mock_answer.assert_called_once()
    call_args = mock_answer.call_args[1]
    assert "To subscribe for 1 week(s)" in call_args["text"]
    assert "SOL" in call_args["text"]

@pytest.mark.asyncio
@patch("aiogram.types.Message.answer", new_callable=AsyncMock)
async def test_check_transaction_success(mock_answer, dispatcher, mock_services):
    dp, storage = dispatcher
    bot = AsyncMock()

    chat = Chat(id=123, type="private")
    user = User(id=123, is_bot=False, first_name="Test")
    message = Message(message_id=1, date=1, chat=chat, from_user=user, text="valid_txid")

    state = dp.fsm.get_context(bot, user.id, chat.id)
    await state.set_state(GetTxidFromUser.state)
    await state.set_data({"subscription_term": 1})

    await payment.check_transaction(message, state)

    mock_services["validator"].validate_transaction.assert_called_once()
    mock_answer.assert_called()
    last_call_args = mock_answer.call_args_list[-1][1]
    assert "Payment successful!" in last_call_args["text"]

@pytest.mark.asyncio
@patch("aiogram.types.Message.answer", new_callable=AsyncMock)
async def test_check_transaction_failure(mock_answer, dispatcher, mock_services):
    dp, storage = dispatcher
    bot = AsyncMock()

    mock_services["validator"].validate_transaction.return_value = (False, "Invalid transaction")

    chat = Chat(id=123, type="private")
    user = User(id=123, is_bot=False, first_name="Test")
    message = Message(message_id=1, date=1, chat=chat, from_user=user, text="invalid_txid")

    state = dp.fsm.get_context(bot, user.id, chat.id)
    await state.set_state(GetTxidFromUser.state)
    await state.set_data({"subscription_term": 1})

    await payment.check_transaction(message, state)

    mock_services["validator"].validate_transaction.assert_called_once()
    mock_answer.assert_called()
    last_call_args = mock_answer.call_args_list[-1][1]
    assert "Payment failed: Invalid transaction" in last_call_args["text"]
