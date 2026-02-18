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
    with patch('src.bot.handlers.payment.reply_keyboards.confirm_transfer', new_callable=AsyncMock):
        await set_subscription_term(mock_message, mock_state)
        mock_state.set_data.assert_called_once()
        args = mock_state.set_data.call_args[0][0]
        assert args["subscription_term"] == 1
        assert "required_sol_amount" in args
        assert "To subscribe for 1 week(s)" in mock_message.answer.call_args.kwargs['text']

@pytest.mark.asyncio
async def test_set_subscription_term_no_text(mock_message, mock_state):
    mock_message.text = None
    await set_subscription_term(mock_message, mock_state)
    mock_message.answer.assert_not_called()

@pytest.mark.asyncio
@patch('src.bot.handlers.payment.SUBSCRIBE_AMOUNT_BY_PLANS', {1: 100})
async def test_set_subscription_term_invalid_term(mock_message, mock_state):
    mock_message.text = "2 week"
    with patch('src.bot.handlers.payment.reply_keyboards.back_to_main_menu', new_callable=AsyncMock):
        await set_subscription_term(mock_message, mock_state)
        assert "Invalid subscription duration" in mock_message.answer.call_args.kwargs['text']

@pytest.mark.asyncio
async def test_set_subscription_term_value_error(mock_message, mock_state):
    mock_message.text = "abc week"
    with patch('src.bot.handlers.payment.reply_keyboards.back_to_main_menu', new_callable=AsyncMock):
        await set_subscription_term(mock_message, mock_state)
        assert "Invalid format" in mock_message.answer.call_args.kwargs['text']

@pytest.mark.asyncio
@patch('src.bot.handlers.payment.SUBSCRIBE_AMOUNT_BY_PLANS', {1: 100})
@patch('src.bot.handlers.payment.PriceService.get_sol_price_in_usd', new_callable=AsyncMock)
async def test_set_subscription_term_no_sol_price(mock_price, mock_message, mock_state):
    mock_message.text = "1 week"
    mock_price.return_value = None
    with patch('src.bot.handlers.payment.reply_keyboards.back_to_main_menu', new_callable=AsyncMock):
        await set_subscription_term(mock_message, mock_state)
        assert "Could not fetch the current SOL price" in mock_message.answer.call_args.kwargs['text']

# Tests for confirm_transfer
@pytest.mark.asyncio
async def test_confirm_transfer(mock_message, mock_state):
    await confirm_transfer(mock_message, mock_state)
    mock_state.set_state.assert_called_once_with(GetTxidFromUser.state)

# Tests for check_transaction
@pytest.mark.asyncio
@patch('src.bot.handlers.payment.PaymentValidator.validate_transaction', new_callable=AsyncMock)
@patch('src.bot.handlers.payment.TransactionRepository')
@patch('src.bot.handlers.payment.UserRepository')
async def test_check_transaction_valid(mock_user_repo, mock_trans_repo, mock_validate, mock_message, mock_state):
    mock_validate.return_value = (True, "Success")
    mock_state.get_data.return_value = {"subscription_term": 1, "required_sol_amount": "0.5"}
    mock_user_repo.get = AsyncMock(return_value=User(id=1, telegram_id=123, first_name='Test', last_name='User', username='testuser', days_sub_end='2020-01-01 00:00:00', balance=0, invite_link='', is_banned=0, last_active=None))
    mock_trans_repo.create = AsyncMock()
    mock_trans_repo.set_status = AsyncMock()
    mock_user_repo.update_subscription_date = AsyncMock()
    with patch('src.bot.handlers.payment.reply_keyboards.back_to_main_menu', new_callable=AsyncMock):
        await check_transaction(mock_message, mock_state)
        assert "Payment successful!" in mock_message.answer.call_args.kwargs['text']

@pytest.mark.asyncio
async def test_check_transaction_no_text(mock_message, mock_state):
    mock_message.text = None
    await check_transaction(mock_message, mock_state)
    mock_message.answer.assert_not_called()

@pytest.mark.asyncio
async def test_check_transaction_no_from_user(mock_message, mock_state):
    mock_message.from_user = None
    await check_transaction(mock_message, mock_state)
    mock_message.answer.assert_not_called()

@pytest.mark.asyncio
async def test_check_transaction_no_weeks(mock_message, mock_state):
    mock_state.get_data.return_value = {}
    with patch('src.bot.handlers.payment.reply_keyboards.back_to_main_menu', new_callable=AsyncMock):
        await check_transaction(mock_message, mock_state)
        assert "Your session has expired" in mock_message.answer.call_args.args[0]

@pytest.mark.asyncio
@patch('src.bot.handlers.payment.PaymentValidator.validate_transaction', new_callable=AsyncMock)
@patch('src.bot.handlers.payment.TransactionRepository')
@patch('src.bot.handlers.payment.UserRepository')
async def test_check_transaction_invalid_date(mock_user_repo, mock_trans_repo, mock_validate, mock_message, mock_state):
    mock_validate.return_value = (True, "Success")
    mock_state.get_data.return_value = {"subscription_term": 1, "required_sol_amount": "0.5"}
    mock_user_repo.get = AsyncMock(return_value=User(id=1, telegram_id=123, first_name='Test', last_name='User', username='testuser', days_sub_end='invalid-date', balance=0, invite_link='', is_banned=0, last_active=None))
    mock_trans_repo.create = AsyncMock()
    mock_trans_repo.set_status = AsyncMock()
    mock_user_repo.update_subscription_date = AsyncMock()
    with patch('src.bot.handlers.payment.reply_keyboards.back_to_main_menu', new_callable=AsyncMock):
        await check_transaction(mock_message, mock_state)
        assert "Payment successful!" in mock_message.answer.call_args.kwargs['text']

@pytest.mark.asyncio
@patch('src.bot.handlers.payment.PaymentValidator.validate_transaction', new_callable=AsyncMock)
@patch('src.bot.handlers.payment.TransactionRepository')
@patch('src.bot.handlers.payment.UserRepository')
async def test_check_transaction_db_error(mock_user_repo, mock_trans_repo, mock_validate, mock_message, mock_state):
    mock_validate.return_value = (True, "Success")
    mock_state.get_data.return_value = {"subscription_term": 1, "required_sol_amount": "0.5"}
    mock_user_repo.get = AsyncMock(return_value=User(id=1, telegram_id=123, first_name='Test', last_name='User', username='testuser', days_sub_end='2020-01-01 00:00:00', balance=0, invite_link='', is_banned=0, last_active=None))
    mock_trans_repo.create = AsyncMock()
    mock_trans_repo.set_status = AsyncMock()
    mock_user_repo.update_subscription_date.side_effect = Exception("DB error")
    with patch('src.bot.handlers.payment.reply_keyboards.back_to_main_menu', new_callable=AsyncMock):
        await check_transaction(mock_message, mock_state)
        assert "There was a database error" in mock_message.answer.call_args.args[0]

# Tests for handle_payment_failed
@pytest.mark.asyncio
async def test_handle_payment_failed_retry(mock_message, mock_state):
    mock_message.text = "retry"
    await handle_payment_failed(mock_message, mock_state)
    mock_state.set_state.assert_called_once_with(GetTxidFromUser.state)

@pytest.mark.asyncio
async def test_handle_payment_failed_cancel(mock_message, mock_state):
    mock_message.text = "cancel"
    with patch('src.bot.handlers.payment.reply_keyboards.back_to_main_menu', new_callable=AsyncMock):
        await handle_payment_failed(mock_message, mock_state)
        mock_state.clear.assert_called_once()
        assert "Payment process cancelled" in mock_message.answer.call_args.kwargs['text']

# Tests for prompt_promo_code
@pytest.mark.asyncio
async def test_prompt_promo_code(mock_message, mock_state):
    await prompt_promo_code(mock_message, mock_state)
    mock_state.set_state.assert_called_once_with("awaiting_promo_code")

# Tests for redeem_promo_code
@pytest.mark.asyncio
@patch('src.bot.handlers.payment.PromoCodeRepository')
@patch('src.bot.handlers.payment.UserRepository')
async def test_redeem_promo_code_success(mock_user_repo, mock_promo_repo, mock_message, mock_state):
    mock_promo = PromoCode(id=1, code='PROMO', is_active=1, max_uses=10, used_count=0, created_by=123, created_at='', expires_at=None, last_redeemed_by=None)
    mock_promo_repo.get_by_code = AsyncMock(return_value=mock_promo)
    mock_promo_repo.redeem = AsyncMock(return_value=True)
    mock_user_repo.get = AsyncMock(return_value=None)
    mock_user_repo.update_subscription_date = AsyncMock()
    with patch('src.bot.handlers.payment.reply_keyboards.back_to_main_menu', new_callable=AsyncMock):
        await redeem_promo_code(mock_message, mock_state)
        assert "Promo code redeemed!" in mock_message.answer.call_args.kwargs['text']

@pytest.mark.asyncio
@patch('src.bot.handlers.payment.PromoCodeRepository')
@patch('src.bot.handlers.payment.UserRepository')
async def test_redeem_promo_code_existing_subscription(mock_user_repo, mock_promo_repo, mock_message, mock_state):
    from datetime import datetime, timedelta
    future_date = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")
    mock_promo = PromoCode(id=1, code='PROMO', is_active=1, max_uses=10, used_count=0, created_by=123, created_at='', expires_at=None, last_redeemed_by=None)
    mock_promo_repo.get_by_code = AsyncMock(return_value=mock_promo)
    mock_promo_repo.redeem = AsyncMock(return_value=True)
    mock_user_repo.get = AsyncMock(return_value=User(id=1, telegram_id=123, first_name='Test', last_name='User', username='testuser', days_sub_end=future_date, balance=0, invite_link='', is_banned=0, last_active=None))
    mock_user_repo.update_subscription_date = AsyncMock()
    with patch('src.bot.handlers.payment.reply_keyboards.back_to_main_menu', new_callable=AsyncMock):
        await redeem_promo_code(mock_message, mock_state)
        assert "Promo code redeemed!" in mock_message.answer.call_args.kwargs['text']

@pytest.mark.asyncio
async def test_redeem_promo_code_no_text(mock_message, mock_state):
    mock_message.text = None
    await redeem_promo_code(mock_message, mock_state)
    assert "Invalid input" in mock_message.answer.call_args.args[0]

@pytest.mark.asyncio
async def test_redeem_promo_code_no_from_user(mock_message, mock_state):
    mock_message.from_user = None
    await redeem_promo_code(mock_message, mock_state)
    assert "Invalid input" in mock_message.answer.call_args.args[0]

@pytest.mark.asyncio
@patch('src.bot.handlers.payment.PromoCodeRepository')
async def test_redeem_promo_code_not_found(mock_promo_repo, mock_message, mock_state):
    mock_promo_repo.get_by_code = AsyncMock(return_value=None)
    await redeem_promo_code(mock_message, mock_state)
    assert "Promo code not found" in mock_message.answer.call_args.args[0]

@pytest.mark.asyncio
@patch('src.bot.handlers.payment.PromoCodeRepository')
async def test_redeem_promo_code_inactive(mock_promo_repo, mock_message, mock_state):
    mock_promo = PromoCode(id=1, code='PROMO', is_active=0, max_uses=10, used_count=0, created_by=123, created_at='', expires_at=None, last_redeemed_by=None)
    mock_promo_repo.get_by_code = AsyncMock(return_value=mock_promo)
    await redeem_promo_code(mock_message, mock_state)
    assert "This promo code is no longer active" in mock_message.answer.call_args.args[0]

@pytest.mark.asyncio
@patch('src.bot.handlers.payment.PromoCodeRepository')
async def test_redeem_promo_code_expired(mock_promo_repo, mock_message, mock_state):
    from datetime import datetime, timedelta
    expired_time = (datetime.utcnow() - timedelta(days=1)).isoformat()
    mock_promo = PromoCode(id=1, code='PROMO', is_active=1, max_uses=10, used_count=0, created_by=123, created_at='', expires_at=expired_time, last_redeemed_by=None)
    mock_promo_repo.get_by_code = AsyncMock(return_value=mock_promo)
    await redeem_promo_code(mock_message, mock_state)
    assert "This promo code has expired" in mock_message.answer.call_args.args[0]

@pytest.mark.asyncio
@patch('src.bot.handlers.payment.PromoCodeRepository')
async def test_redeem_promo_code_max_uses(mock_promo_repo, mock_message, mock_state):
    mock_promo = PromoCode(id=1, code='PROMO', is_active=1, max_uses=10, used_count=10, created_by=123, created_at='', expires_at=None, last_redeemed_by=None)
    mock_promo_repo.get_by_code = AsyncMock(return_value=mock_promo)
    await redeem_promo_code(mock_message, mock_state)
    assert "This promo code has reached its maximum number of uses" in mock_message.answer.call_args.args[0]

@pytest.mark.asyncio
@patch('src.bot.handlers.payment.PromoCodeRepository')
async def test_redeem_promo_code_redeem_failed(mock_promo_repo, mock_message, mock_state):
    mock_promo = PromoCode(id=1, code='PROMO', is_active=1, max_uses=10, used_count=0, created_by=123, created_at='', expires_at=None, last_redeemed_by=None)
    mock_promo_repo.get_by_code = AsyncMock(return_value=mock_promo)
    mock_promo_repo.redeem = AsyncMock(return_value=False)
    await redeem_promo_code(mock_message, mock_state)
    assert "Failed to redeem promo code" in mock_message.answer.call_args.args[0]

@pytest.mark.asyncio
@patch('src.bot.handlers.payment.PromoCodeRepository')
@patch('src.bot.handlers.payment.UserRepository')
async def test_redeem_promo_code_invalid_date(mock_user_repo, mock_promo_repo, mock_message, mock_state):
    mock_promo = PromoCode(id=1, code='PROMO', is_active=1, max_uses=10, used_count=0, created_by=123, created_at='', expires_at=None, last_redeemed_by=None)
    mock_promo_repo.get_by_code = AsyncMock(return_value=mock_promo)
    mock_promo_repo.redeem = AsyncMock(return_value=True)
    mock_user_repo.get = AsyncMock(return_value=User(id=1, telegram_id=123, first_name='Test', last_name='User', username='testuser', days_sub_end='invalid-date', balance=0, invite_link='', is_banned=0, last_active=None))
    mock_user_repo.update_subscription_date = AsyncMock()
    with patch('src.bot.handlers.payment.reply_keyboards.back_to_main_menu', new_callable=AsyncMock):
        await redeem_promo_code(mock_message, mock_state)
        assert "Promo code redeemed!" in mock_message.answer.call_args.kwargs['text']
