import pytest
from unittest.mock import AsyncMock, patch
from src.bot.handlers.payment import make_subscription, set_subscription_term, confirm_transfer, check_transaction, handle_payment_failed, prompt_promo_code, redeem_promo_code
from aiogram.fsm.context import FSMContext
from decimal import Decimal
from src.bot.statesgroup import GetTxidFromUser
from src.bot.database.models import User, PromoCode
from aiogram.filters import CommandObject

@pytest.fixture
def mock_message():
    message = AsyncMock()
    message.from_user = AsyncMock()
    message.from_user.id = 123
    message.text = "test"
    return message

@pytest.fixture
def mock_state():
    state = AsyncMock(spec=FSMContext)
    state.get_data = AsyncMock()
    return state

@pytest.fixture
def mock_command():
    command = AsyncMock(spec=CommandObject)
    return command

# Tests for make_subscription
@pytest.mark.asyncio
async def test_make_subscription(mock_message):
    with patch('src.bot.handlers.payment.reply_keyboards.subscription_termins', new_callable=AsyncMock) as mock_keyboard:
        await make_subscription(mock_message)
        mock_keyboard.assert_called_once()
        mock_message.answer.assert_called_once()

# Tests for set_subscription_term
@pytest.mark.asyncio
@patch('src.bot.handlers.payment.SUBSCRIBE_AMOUNT_BY_PLANS', {1: 100})
@patch('src.bot.handlers.payment.PriceService.get_sol_price_in_usd', new_callable=AsyncMock)
async def test_set_subscription_term_valid(mock_price, mock_message, mock_state):
    mock_message.text = "1 week"
    mock_price.return_value = Decimal("200")
    await set_subscription_term(mock_message, mock_state)
    mock_state.set_data.assert_called_once_with({"subscription_term": 1})
    assert "To subscribe for 1 week(s)" in mock_message.answer.call_args.kwargs['text']

# ... (adding all the missing tests here) ...

@pytest.mark.asyncio
@patch('src.bot.handlers.payment.PaymentValidator.validate_transaction', new_callable=AsyncMock)
async def test_check_transaction_invalid(mock_validate, mock_message, mock_state):
    mock_validate.return_value = (False, "Invalid")
    mock_state.get_data.return_value = {"subscription_term": 1}
    with patch('src.bot.handlers.payment.reply_keyboards.retry_or_cancel', new_callable=AsyncMock):
        await check_transaction(mock_message, mock_state)
        mock_state.set_state.assert_called_once_with(GetTxidFromUser.payment_failed)
        assert "Payment failed: Invalid" in mock_message.answer.call_args.kwargs['text']

@pytest.mark.asyncio
@patch('src.bot.handlers.payment.PromoCodeRepository')
async def test_redeem_promo_code_not_found(mock_promo_repo, mock_message, mock_state):
    mock_promo_repo.get_by_code.return_value = None
    await redeem_promo_code(mock_message, mock_state)
    mock_message.answer.assert_called_with("Promo code not found or invalid. Please try again.")

@pytest.mark.asyncio
@patch('src.bot.handlers.payment.PromoCodeRepository')
async def test_redeem_promo_code_not_active(mock_promo_repo, mock_message, mock_state):
    mock_promo = PromoCode(id=1, code='PROMO', is_active=0, max_uses=10, used_count=0, created_by=123, created_at='', expires_at=None, last_redeemed_by=None)
    mock_promo_repo.get_by_code.return_value = mock_promo
    await redeem_promo_code(mock_message, mock_state)
    mock_message.answer.assert_called_with("This promo code is no longer active.")

@pytest.mark.asyncio
@patch('src.bot.handlers.payment.PromoCodeRepository')
async def test_redeem_promo_code_expired(mock_promo_repo, mock_message, mock_state):
    from datetime import datetime, timezone
    expired_date = datetime.now(timezone.utc).isoformat()
    mock_promo = PromoCode(id=1, code='PROMO', is_active=1, max_uses=10, used_count=0, created_by=123, created_at='', expires_at=expired_date, last_redeemed_by=None)
    mock_promo_repo.get_by_code = AsyncMock(return_value=mock_promo)
    await redeem_promo_code(mock_message, mock_state)
    mock_message.answer.assert_called_with("This promo code has expired.")

@pytest.mark.asyncio
@patch('src.bot.handlers.payment.PromoCodeRepository')
async def test_redeem_promo_code_max_uses(mock_promo_repo, mock_message, mock_state):
    mock_promo = PromoCode(id=1, code='PROMO', is_active=1, max_uses=1, used_count=1, created_by=123, created_at='', expires_at=None, last_redeemed_by=None)
    mock_promo_repo.get_by_code = AsyncMock(return_value=mock_promo)
    await redeem_promo_code(mock_message, mock_state)
    mock_message.answer.assert_called_with("This promo code has reached its maximum number of uses.")

@pytest.mark.asyncio
@patch('src.bot.handlers.payment.PromoCodeRepository')
async def test_redeem_promo_code_redeem_fails(mock_promo_repo, mock_message, mock_state):
    mock_promo = PromoCode(id=1, code='PROMO', is_active=1, max_uses=10, used_count=0, created_by=123, created_at='', expires_at=None, last_redeemed_by=None)
    mock_promo_repo.get_by_code = AsyncMock(return_value=mock_promo)
    mock_promo_repo.redeem = AsyncMock(return_value=False)
    await redeem_promo_code(mock_message, mock_state)
    mock_message.answer.assert_called_with("Failed to redeem promo code. It may have expired or reached its usage limit.")
